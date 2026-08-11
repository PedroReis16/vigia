# Deploy do vigia-fall (Linux ARM64)

Guia curto para gerar o pacote PyInstaller onedir e instalar na placa.

## Pré-requisitos (máquina de build)

- **`make`** e **Python 3.12** com dependências do projeto.
- O ficheiro `yolo26s-pose.pt` é gitignored: o Makefile baixa-o automaticamente se faltar.
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

Copie o tarball, o instalador e a unit:

```bash
scp dist/vigia-fall-detection-linux-arm64.tar.gz \
    deploy/install.sh \
    deploy/fall-detection.service \
    usuario@placa:/tmp/
```

Na placa:

```bash
sudo chmod +x /tmp/install.sh
sudo /tmp/install.sh /tmp/vigia-fall-detection-linux-arm64.tar.gz
```

Isto extrai para `/opt/vigia/fall-detection/`, instala `fall-detection.service`, faz `daemon-reload` e `enable --now`.

### `.env` (opcional)

Copie um `.env` para `/opt/vigia/.env` (o unit usa `EnvironmentFile=-/opt/vigia/.env`). Na placa use pelo menos:

- `SHOW_VIDEO=false`
- `DEBUG=false`

`YOLO_POSE_MODEL` pode continuar `yolo26s-pose` (resolve para o `.pt` empacotado) ou um caminho absoluto.

## Verificar

```bash
sudo systemctl status fall-detection.service
journalctl -u fall-detection.service -n 80 --no-pager
```

Mantenha a pasta `fall-detection` completa (executável + `_internal/`).
