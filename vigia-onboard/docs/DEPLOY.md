# Deploy do serviço Vigia (vigia-onboard, Linux ARM64)

Guia para gerar o pacote PyInstaller onedir e instalar na Raspberry Pi OS (aarch64).

O instalador sobe **um único serviço**, `vigia.service` (nome **Vigia**). O binário `vigia` arranca captura, integração e interface no mesmo unit. Fica em `/opt/vigia/onboard/`.

## Pré-requisitos (máquina de build)

- **`make`** e **Python 3.12**.
- O export NCNN em `capture/models/yolo/{stem}_ncnn_model/` é gerado por `make ensure-model` (Ultralytics, `YOLO_MODEL`, default `yolo26s-pose`, `YOLO_IMGSZ` default 320) se faltar. Exports YOLO não se commitam.
- Só o **NCNN** do YOLO entra no bundle (ONNX no Windows e CoreML no macOS ficam para desenvolvimento). No executável congelado a inferência usa esse NCNN.
- Se existir `core/models/gru_2classes.onnx`, o classificador `gru` também entra no bundle.
- **Caminho do build** (`make build-linux-arm64`):
  - **Linux aarch64/arm64** — compilação nativa (CI `ubuntu-24.04-arm`, placa).
  - **Outros hosts** (macOS, Linux amd64) — Docker + buildx (`deploy/Dockerfile.linux-arm64-binary`).
- Em hosts que não são Linux ARM, é preciso **Docker** com `linux/arm64`.

> Mac Apple Silicon é `arm64`, mas o SO é Darwin: o Makefile usa Docker. O binário tem de ser ELF Linux aarch64.

## Gerar o artefato

Na raiz de `vigia-onboard/`:

```bash
# Em linux/arm64, com liblgpio já instalada (CI usa .github/scripts/install-liblgpio.sh):
make install-build-deps

make build-linux-arm64
```

**Saída:**

- `dist/vigia-onboard-linux-arm64/` — onedir (`vigia` + `_internal/`, com o NCNN em `_internal/models/yolo/`).
- `dist/vigia-onboard-linux-arm64.tar.gz` — bundle.
- `dist/vigia-onboard-deploy.zip` — zip único para a placa.

`make package-ota` (depois do build) gera `dist/vigia-onboard-ota-<versão>.tar.gz` com `manifest.json`, `install.sh` e o tarball interno `vigia-onboard-linux-arm64.tar.gz`.

## Instalação na placa

Raspberry Pi OS 64-bit. Este pacote é o serviço de borda completo (pareamento, captura e integração). Na instalação manual, `vigia-bootstrap` e `fall-detection` são desactivados se já estiverem na placa.

```bash
scp dist/vigia-onboard-deploy.zip usuario@placa:/tmp/
ssh usuario@placa
cd /tmp
unzip -o vigia-onboard-deploy.zip -d vigia-onboard-deploy
sudo ./vigia-onboard-deploy/install-on-board.sh
```

Isto instala `ffmpeg`, libs de runtime OpenCV/torch, `liblgpio1` e `i2c-tools`, activa o I2C do LCD, extrai para `/opt/vigia/onboard/` e liga `vigia.service`.

```bash
systemctl status vigia.service
journalctl -u vigia.service -n 80 --no-pager
```

O serviço arranca sem `identity.json`: o interface espera o pareamento BLE. A captura permanece no gate até identity e network existirem.

Desinstalar:

```bash
sudo vigia-uninstall
# também apaga identity, network, classifier, .env e o estado OTA:
sudo vigia-uninstall --purge-data
```

### `.env` (opcional)

Ficheiro em `/opt/vigia/.env`. O unit aplica-o e depois fixa `DATA_DIR=/opt/vigia`, `SHOW_VIDEO=false`, `DEBUG=false`, `WIFI_MOCK=false`, `BLE_ENABLED=true` e `LCD_ENABLED=true`. `FRAME_RATE`, `CLASSIFIER` e `YOLO_MODEL` continuam a poder vir do `.env`.

Com `DATA_DIR=/opt/vigia`, o OTA fica em `/var/lib/vigia/ota`.

### OTA

O `install.sh` chamado pelo próprio serviço (`VIGIA_OTA_APPLY=1`) substitui o bundle sem parar o unit e agenda `systemctl restart vigia` passados 45 segundos, para o health-check gravar a revisão antes do processo novo subir.
