from __future__ import annotations

import asyncio
import json
import os
import ssl
from dataclasses import dataclass

import paho.mqtt.client as mqtt

from app.fiware.models.vigia_settings import VigiaSettings
from app.integration.command_bus import CommandDispatcher
from app.logging import get_logger

logger = get_logger("integration")

# Deploy (docker-compose/deploy/docker-compose.yaml): Mosquitto expõe WS na 9001;
# Traefik encaminha websecure → :9001 com PathPrefix `/fiware/mosquitto` (strip) +
# caminho MQTT `/mqtt` no broker. Clientes externos usam WSS na 443 com path
# `/fiware/mosquitto/mqtt`. O IoT Agent dentro da rede usa TCP :1883 (interno).


def _normalize_mqtt_transport(raw: str | None) -> str:
    """Retorna 'tcp' ou 'websockets' para o construtor do Paho."""
    v = (raw or "websockets").strip().lower()
    if v in ("ws", "websockets", "websocket"):
        return "websockets"
    if v in ("tcp", "mqtt"):
        return "tcp"
    logger.warning("FIWARE_MQTT_TRANSPORT inválido '{}', usando websockets", v)
    return "websockets"


def _resolve_tls_flag(transport: str, port: int, raw: str | None) -> bool:
    """TLS para WSS na borda (443); desligável para WS local (ex.: :9001 sem TLS)."""
    if raw is not None and raw.strip() != "":
        return raw.strip().lower() in ("1", "true", "yes", "on")
    return transport == "websockets" and port in (443, 8443)


@dataclass(frozen=True)
class _MqttListenConfig:
    host: str
    port: int
    topic: str
    username: str
    password: str
    transport: str
    ws_path: str
    use_tls: bool


def _default_mqtt_port(transport: str) -> int:
    """TCP costuma ser 1883 no broker; deploy público usa WSS na 443 (Traefik)."""
    return 1883 if transport == "tcp" else 443


def _load_mqtt_config(device_settings: VigiaSettings) -> _MqttListenConfig:
    transport = _normalize_mqtt_transport(os.getenv("FIWARE_MQTT_TRANSPORT"))
    port_raw = os.getenv("FIWARE_MQTT_PORT")
    port = (
        int(port_raw)
        if port_raw is not None and str(port_raw).strip() != ""
        else _default_mqtt_port(transport)
    )
    use_tls = _resolve_tls_flag(
        transport,
        port,
        os.getenv("FIWARE_MQTT_TLS"),
    )
    default_ws_path = (
        "/fiware/mosquitto/mqtt"
        if port in (443, 8443)
        else "/mqtt"
    )
    ws_path = (os.getenv("FIWARE_MQTT_WS_PATH") or default_ws_path).strip() or default_ws_path
    return _MqttListenConfig(
        host=(os.getenv("FIWARE_MQTT_HOST") or "localhost").strip(),
        port=port,
        topic=os.getenv("FIWARE_MQTT_TOPIC") or f"/{device_settings.entity_name}/cmd",
        username=(os.getenv("FIWARE_MQTT_USERNAME") or "").strip(),
        password=(os.getenv("FIWARE_MQTT_PASSWORD") or "").strip(),
        transport=transport,
        ws_path=ws_path,
        use_tls=use_tls,
    )


def _parse_command_json(raw: str) -> tuple[str, dict] | None:
    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        body = {"raw": raw}

    command_name = str(body.get("command") or body.get("name") or "").strip()
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else body
    if not command_name:
        logger.warning("mensagem MQTT sem comando: {}", raw)
        return None
    return command_name, payload


def _build_client(cfg: _MqttListenConfig) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        transport=cfg.transport,
    )
    if cfg.transport == "websockets":
        client.ws_set_options(path=cfg.ws_path)
    if cfg.use_tls:
        client.tls_set_context(ssl.create_default_context())
    if cfg.username:
        client.username_pw_set(cfg.username, cfg.password)
    return client


async def listen_mqtt_commands(
    device_settings: VigiaSettings, dispatcher: CommandDispatcher
) -> None:
    mqtt_enabled = (os.getenv("FIWARE_MQTT_ENABLED") or "true").strip().lower()
    if mqtt_enabled in ("0", "false", "no", "off"):
        logger.info("escuta MQTT desabilitada por FIWARE_MQTT_ENABLED")
        while True:
            await asyncio.sleep(60)

    cfg = _load_mqtt_config(device_settings)
    loop = asyncio.get_running_loop()
    incoming_queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()

    while True:
        client = _build_client(cfg)

        def on_connect(
            _client: mqtt.Client,
            _userdata: object,
            _flags: mqtt.ConnectFlags,
            reason_code: mqtt.ReasonCode,
            _properties: mqtt.Properties | None = None,
        ) -> None:
            if reason_code.is_failure:
                logger.warning("falha ao conectar MQTT: {}", reason_code)
                return
            _client.subscribe(cfg.topic, qos=1)
            logger.info(
                "MQTT conectado ({} tls={} {}:{} path={}), ouvindo tópico: {}",
                cfg.transport,
                cfg.use_tls,
                cfg.host,
                cfg.port,
                cfg.ws_path if cfg.transport == "websockets" else "-",
                cfg.topic,
            )

        def on_message(
            _client: mqtt.Client,
            _userdata: object,
            msg: mqtt.MQTTMessage,
        ) -> None:
            raw = msg.payload.decode("utf-8", errors="ignore")
            parsed = _parse_command_json(raw)
            if parsed is None:
                return
            command_name, payload = parsed
            loop.call_soon_threadsafe(
                incoming_queue.put_nowait,
                (command_name, payload),
            )

        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(cfg.host, cfg.port, keepalive=60)
            client.loop_start()
            while True:
                command_name, payload = await incoming_queue.get()
                try:
                    await dispatcher.dispatch(command_name, payload)
                except Exception as exc:
                    logger.warning(
                        "erro ao processar comando '{}': {}", command_name, exc
                    )
        except OSError as exc:
            logger.warning(
                "broker MQTT indisponível em {}:{} ({}): {}. nova tentativa em 10s.",
                cfg.host,
                cfg.port,
                cfg.transport,
                exc,
            )
            await asyncio.sleep(10)
        finally:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass
