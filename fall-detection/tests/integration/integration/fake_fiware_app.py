"""Aplicação aiohttp mínima que simula IoT Agent + Orion atrás de FIWARE_PATH."""

from __future__ import annotations

from typing import Any

from aiohttp import web


def default_device_payload(device_id: str) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "entity_type": "VigiaCam",
        "protocol": "PDI-IoTA-UltraLight",
        "transport": "MQTT",
        "commands": [{"name": "stream"}],
        "attributes": [
            {"name": "stream", "type": "Boolean", "object_id": "st"},
        ],
    }


def build_fake_fiware_app() -> tuple[web.Application, dict[str, Any]]:
    state: dict[str, Any] = {
        "calls": [],
        "entities": {},
    }

    def record(method: str, path: str) -> None:
        state["calls"].append((method, path))

    async def get_device(request: web.Request) -> web.StreamResponse:
        record("GET", request.path)
        status = state.get("get_device_status", 200)
        if status == 404:
            return web.Response(status=404)
        if state.get("get_device_html"):
            return web.Response(
                status=200,
                text="<!doctype html><title>Frontend</title>",
                content_type="text/html",
            )
        device_id = request.match_info["device_id"]
        body = state.get("get_device_body") or default_device_payload(device_id)
        wrapped = state.get("get_device_wrapped", True)
        payload = {"device": body} if wrapped else body
        return web.json_response(payload)

    async def post_devices(request: web.Request) -> web.StreamResponse:
        record("POST", request.path)
        status = state.get("post_devices_status", 201)
        return web.Response(status=status)

    async def put_device(request: web.Request) -> web.StreamResponse:
        record("PUT", request.path)
        status = state.get("put_device_status", 204)
        return web.Response(status=status)

    async def post_registrations(request: web.Request) -> web.StreamResponse:
        record("POST", request.path)
        status = state.get("post_registrations_status", 204)
        return web.Response(status=status)

    async def get_entity(request: web.Request) -> web.StreamResponse:
        record("GET", request.path)
        entity_id = request.match_info["entity_id"]
        status = state.get("get_entity_status", 200)
        if status == 404:
            return web.Response(status=404)
        body = state.get("get_entity_body") or state["entities"].get(entity_id)
        if body is None:
            body = {"id": entity_id, "type": "VigiaCam"}
        return web.json_response(body)

    async def post_entities(request: web.Request) -> web.StreamResponse:
        record("POST", request.path)
        status = state.get("post_entities_status", 201)
        text = state.get("post_entities_body", "")
        if status == 422:
            return web.Response(
                status=422,
                text=text or '{"error":"Unprocessable","description":"Already Exists"}',
                content_type="application/json",
            )
        return web.Response(status=status)

    async def post_entity_attrs(request: web.Request) -> web.StreamResponse:
        record("POST", request.path)
        status = state.get("post_entity_attrs_status", 204)
        return web.Response(status=status)

    app = web.Application()
    app.router.add_get("/iot-agent/iot/devices/{device_id}", get_device)
    app.router.add_post("/iot-agent/iot/devices", post_devices)
    app.router.add_put("/iot-agent/iot/devices/{device_id}", put_device)
    app.router.add_post("/orion/v2/registrations", post_registrations)
    app.router.add_get("/orion/v2/entities/{entity_id}", get_entity)
    app.router.add_post("/orion/v2/entities", post_entities)
    app.router.add_post("/orion/v2/entities/{entity_id}/attrs", post_entity_attrs)

    return app, state
