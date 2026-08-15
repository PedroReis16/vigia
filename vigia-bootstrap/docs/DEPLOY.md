# Deploy do vigia-bootstrap (Linux ARM64)

Guia curto para gerar o pacote PyInstaller onedir e instalar na placa como serviço systemd.

O bootstrap é o **control plane** da placa: identidade, pareamento BLE, Wi‑Fi (`nmcli`) e GPIO. Grava `/opt/vigia/identity.json` e `/opt/vigia/network.json`. Só depois arranca `fall-detection.service`.

O processo escuta o botão GPIO (pino 17) e o LED de estado (pino 27):

- **toque curto** — indica se `fall-detection.service` está ativo
- **toque longo** — corre `/usr/local/bin/vigia_reset_config.sh` (apaga identidade/rede, **não** reinicia o fall). O bootstrap reabre o beacon BLE.

Se `identity.json` e `network.json` já existirem, o pareamento BLE é ignorado e o fall é iniciado de imediato.

## Pré-requisitos (máquina de build)

- **`make`** e **Python 3.12** com dependências do projeto.
- **Caminho do build** (escolhido automaticamente por `make build-linux-arm64`):
  - **Host ARM** (`aarch64` / `arm64`, incluindo a placa e Mac Apple Silicon) — PyInstaller nativo, **sem Docker**.
  - **Host não-ARM** (Linux amd64, Intel, etc.) — Docker + buildx (`deploy/Dockerfile.linux-arm64-binary`).

> O artefato para instalar na Raspberry Pi tem de ser **Linux ARM64**. Gere-o na própria placa (ou noutro Linux ARM). Num Mac ARM o build nativo produz um binário Darwin, não o da placa.

Na placa: NetworkManager e Bluetooth ativos (`Wants=` no unit). O serviço corre como root (GPIO, `nmcli`, `systemctl`).

## Gerar o artefato

Na raiz de `vigia-bootstrap/`:

```bash
# Em linux/arm64 (opcional, se ainda não tiver deps):
make install-build-deps

make build-linux-arm64
```

**Saída:**

- `dist/vigia-bootstrap-linux-arm64/` — onedir (executável + `_internal/`).
- `dist/vigia-bootstrap-linux-arm64.tar.gz` — ficheiro para copiar para a placa.

## Instalação na placa

Instale **primeiro** o bootstrap, depois o fall-detection.

Copie o tarball, o instalador, a unit e o script de reset:

```bash
scp dist/vigia-bootstrap-linux-arm64.tar.gz \
    deploy/install.sh \
    deploy/vigia-bootstrap.service \
    deploy/vigia_reset_config.sh \
    usuario@placa:/tmp/
```

Na placa:

```bash
sudo chmod +x /tmp/install.sh
sudo /tmp/install.sh /tmp/vigia-bootstrap-linux-arm64.tar.gz
```

Isto extrai para `/opt/vigia/bootstrap/`, instala `vigia-bootstrap.service`, copia `vigia_reset_config.sh` para `/usr/local/bin/`, faz `daemon-reload` e `enable --now`.

O unit usa `EnvironmentFile=-/opt/vigia/.env` (ficheiro opcional, partilhado com o fall-detection):

- `DATA_DIR=/opt/vigia` (predefinição)
- `DEBUG=false` na placa (Wi‑Fi real via `nmcli`; `true` usa mock)
- `WIFI_MOCK_RESULT=success` (só com `DEBUG=true`)

## Verificar

```bash
sudo systemctl status vigia-bootstrap.service
journalctl -u vigia-bootstrap.service -n 80 --no-pager
```

Mantenha a pasta `bootstrap` completa (executável + `_internal/`).
