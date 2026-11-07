# vigia-devices

Worker mock que simula dispositivos Vigia na cloud: loop de vídeo → RTMP sob demanda, thumbnail periódica, e quedas aleatórias (MQTT Ultralight + upload de clipe).

Sem YOLO, BLE, LCD ou OTA. Os IDs vêm de [`device_pool.json`](device_pool.json) e devem espelhar `MockDevicesSeed` na API (.NET).

## Pré-requisitos

- Stack local (`docker-compose/local`) com API em **Debug** (seed dos 8 devices no grupo do admin + FIWARE)
- Redis acessível (`localhost:6379`)
- MediaMTX + Mosquitto (Traefik `:81`)
- Python ≥ 3.12, FFmpeg no PATH
- ≥1 ficheiro `.mp4` em `assets/videos/`

## Setup

```bash
cd vigia-devices
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# coloque vídeos em assets/videos/
```

## Correr

```bash
python main.py
```

Cada instância claima um ID livre via Redis (`vigia:mock-device:{id}`). Para forçar um slot:

```bash
DEVICE_ID=b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c python main.py
```

Para demos curtas de queda:

```bash
FALL_MIN_S=30 FALL_MAX_S=60 python main.py
```

Login admin (Keycloak): `admin` / `admin` (realm import). A listagem deve mostrar os devices seedados; thumbnails aparecem após o primeiro upload; o stream WHEP dispara `stream_on` como num device real.

## Sync do pool

Alterar o pool exige atualizar **os dois**:

1. `vigia-api/Libraries/Vigia.Models/Seed/MockDevicesSeed.cs`
2. `vigia-devices/device_pool.json`

## Testes

```bash
python -m pytest
```
