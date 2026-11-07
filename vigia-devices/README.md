# vigia-devices

Worker mock que simula dispositivos Vigia na cloud: loop de vídeo → RTMP sob demanda, thumbnail periódica, e quedas aleatórias (MQTT Ultralight + upload de clipe).

Sem YOLO, BLE, LCD ou OTA. Os IDs vêm de [`device_pool.json`](device_pool.json) e devem espelhar `MockDevicesSeed` na API (.NET).

O worker **nunca** claima o device de edge/teste (`Vigia-a1b2c3d4` / `TestDeviceSeed`). Esse ID fica em `reserved_edge_ids` e é rejeitado no load do pool e no claim.

## Pré-requisitos

- Stack local (`docker-compose/local`) com API em **Debug** (seed do edge de teste + 7 mock no grupo do admin + FIWARE)
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

Cada instância claima um ID livre via Redis (`vigia:mock-device:{id}`). Para forçar um slot do pool mock (nunca o edge):

```bash
DEVICE_ID=a1b2c3d4-e5f6-4789-a012-3456789abcde python main.py
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

## Docker / release

Imagem: `pedroreis16/vigia-devices:latest` (`docker-compose/dockerfiles/vigia-devices.dockerfile`). Os MP4 de `assets/videos/` vão para dentro da imagem; o build falha se a pasta estiver vazia.

Pipeline manual: `.github/workflows/worker-release.yml` (testes → segurança → Docker Hub → Portainer via `PORTAINER_DEVICES_WEBHOOK_URL` → tag rolling `worker`).

## Testes

```bash
python -m pytest
```
