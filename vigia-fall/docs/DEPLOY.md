# Deploy do vigia-fall (Linux ARM64)

Guia curto para gerar o pacote PyInstaller onedir e instalar na placa.

## Pré-requisitos (máquina de build)

- **`make`** e **Python 3.12** com dependências do projeto.
- O ficheiro `yolo26s-pose.pt` é gitignored: o Makefile baixa-o automaticamente se faltar.
- O modelo GRU `model/gru_2classes.onnx` entra no bundle PyInstaller (classificador `gru`).
- **Caminho do build** (escolhido automaticamente por `make build-linux-arm64`):
  - **Linux aarch64/arm64** — compilação nativa (CI com `ubuntu-24.04-arm`, VM ARM, placa).
  - **Outros hosts** (macOS, Linux amd64, etc.) — Docker + buildx (`deploy/Dockerfile.linux-arm64-binary`).
- Em hosts não-ARM Linux, é preciso **Docker** com suporte a `linux/arm64`.

> Mac Apple Silicon é `arm64`, mas o SO é Darwin: o Makefile **não** trata como nativo (o binário teria de ser Linux). Nesse caso usa Docker.

## Gerar o artefato

Na raiz de `vigia-fall/`:

```bash
# Em linux/arm64 (opcional, se ainda não tiver deps):
make install-build-deps

make build-linux-arm64
```

**Saída:**

- `dist/vigia-fall-detection-linux-arm64/` — onedir (executável + `_internal/`).
- `dist/vigia-fall-detection-linux-arm64.tar.gz` — ficheiro para copiar para a placa.

No caminho Docker, o build usa Python 3.12 e OpenCV headless dentro da imagem.

## Instalação na placa

Instale **primeiro** o bootstrap, depois o fall-detection.

Copie o tarball, o instalador, o desinstalador e a unit:

```bash
scp dist/vigia-fall-detection-linux-arm64.tar.gz \
    deploy/install.sh \
    deploy/uninstall.sh \
    deploy/fall-detection.service \
    usuario@placa:/tmp/
```

Na placa:

```bash
sudo chmod +x /tmp/install.sh
sudo /tmp/install.sh /tmp/vigia-fall-detection-linux-arm64.tar.gz
```

Isto instala `ffmpeg` e libs de runtime (`libgomp1`, `libglib2.0-0`, `libgl1`, `libsm6`, `libxext6`) se faltarem, extrai para `/opt/vigia/fall-detection/`, instala o unit e o script `vigia-fall-detection-uninstall`. O **start** só sucede se existirem `/opt/vigia/identity.json` e `/opt/vigia/network.json` (escritos pelo **vigia-bootstrap** após o pareamento BLE). Instale o bootstrap antes; na primeira utilização o fall fica inactivo até o app provisionar a rede.

Ordem na placa: bootstrap → pareamento (app) → `systemctl start fall-detection` (o bootstrap dispara o start).

Desinstalar:

```bash
sudo vigia-fall-detection-uninstall
# ou, apagando também o SQLite em /opt/vigia/DB:
sudo vigia-fall-detection-uninstall --purge-data
```

Só remove os pacotes apt que **este** `install.sh` tiver adicionado. `identity.json`, `network.json` e `.env` ficam (são do bootstrap).

### `.env` (opcional)

Copie um `.env` para `/opt/vigia/.env` (o unit usa `EnvironmentFile=-/opt/vigia/.env`). Na placa use pelo menos:

- `SHOW_VIDEO=false`
- `DEBUG=false`
- `DATA_DIR=/opt/vigia` (mesmo valor que o bootstrap)

Com `DATA_DIR=/opt/vigia`, pending OTA em `/var/lib/vigia/ota`. Em debug local (`DATA_DIR=./data`), OTA → `{DATA_DIR}/ota`.

`YOLO_POSE_MODEL` pode continuar `yolo26s-pose` (resolve para o `.pt` empacotado) ou um caminho absoluto.

## Verificar

```bash
sudo systemctl status fall-detection.service
journalctl -u fall-detection.service -n 80 --no-pager
```

Mantenha a pasta `fall-detection` completa (executável + `_internal/`).
