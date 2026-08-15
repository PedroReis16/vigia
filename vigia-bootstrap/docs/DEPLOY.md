# Deploy do vigia-bootstrap (Linux ARM64)

Guia curto para gerar o pacote PyInstaller onedir e instalar na placa como serviço systemd.

O bootstrap é o **control plane** da placa: identidade, pareamento BLE, Wi‑Fi (`nmcli`), LCD 16x2 e GPIO. Grava `/opt/vigia/identity.json` e `/opt/vigia/network.json`. Só depois arranca `fall-detection.service`.

Se `identity.json` e `network.json` já existirem, o pareamento BLE é ignorado e o fall é iniciado de imediato.

## Interface física (predefinições BCM)

| Função | GPIO | Notas |
| --- | --- | --- |
| OK | 17 | curto = confirmar; longo (≥3 s) = ecrã Desvincular |
| Cima | 22 | ecrã anterior |
| Baixo | 23 | ecrã seguinte |
| LCD 16x2 I2C | SDA 2 / SCL 3 | backpack PCF8574, endereço `0x27`, bus 1 |

O feedback de estado (pareamento, Wi‑Fi, fall) é só no LCD.

Ecrãs: **VIGIA** (Pareando user / Fall ativo / …) → **WiFi** (SSID) → **Nova rede?** → **Servico** (OK = restart) → **Desvincular?**.

- **Nova rede** apaga só `network.json` (`vigia_reset_wifi.sh`) e reabre o BLE.
- **Desvincular** corre `vigia_reset_config.sh` (identidade + rede).

Na **Raspberry Pi 5** o gpiozero precisa de **liblgpio** em runtime. O `install.sh` instala `liblgpio1` e `i2c-tools` via apt e activa o I2C (`raspi-config nonint do_i2c 0`). Não é preciso `apt-get` manual na placa.

Se o I2C acabou de ser ligado pela primeira vez, pode faltar `/dev/i2c-1` até um reboot.

Se o módulo LCD estiver em `0x3F`: `LCD_I2C_ADDR=0x3F` no `.env`. Sem LCD: `LCD_ENABLED=false` (botões continuam).

## Pré-requisitos (máquina de build)

- **`make`** e **Python 3.12** com dependências do projeto.
- **Caminho do build** (escolhido automaticamente por `make build-linux-arm64`):
  - **Linux aarch64/arm64** (a placa) — PyInstaller nativo.
  - **Mac (incluindo Apple Silicon) e Linux amd64** — Docker + buildx. Um build nativo no Mac gera Darwin e a Pi responde `Exec format error`.

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

```bash
scp dist/vigia-bootstrap-linux-arm64.tar.gz \
    deploy/install.sh \
    deploy/uninstall.sh \
    deploy/vigia-bootstrap.service \
    deploy/vigia_reset_config.sh \
    deploy/vigia_reset_wifi.sh \
    usuario@placa:/tmp/
```

Na placa:

```bash
sudo chmod +x /tmp/install.sh
sudo /tmp/install.sh /tmp/vigia-bootstrap-linux-arm64.tar.gz
```

Isto instala `liblgpio1` e `i2c-tools` se faltarem, activa I2C, extrai para `/opt/vigia/bootstrap/`, instala o unit e os scripts (incluindo `vigia-bootstrap-uninstall`).

Desinstalar:

```bash
sudo vigia-bootstrap-uninstall
# ou, apagando também identity/network/.env:
sudo vigia-bootstrap-uninstall --purge-data
```

Só remove os pacotes apt que **este** `install.sh` tiver adicionado (não desinstala `liblgpio1` se já existia). O I2C fica ligado.

O unit usa `EnvironmentFile=-/opt/vigia/.env` (opcional, partilhado com o fall-detection):

- `DATA_DIR=/opt/vigia`
- `DEBUG=false` na placa (`true` = Wi‑Fi mock)
- `WIFI_MOCK_RESULT=success`
- `LCD_ENABLED=true`
- `LCD_I2C_ADDR=0x27`
- `BUTTON_OK=17` `BUTTON_UP=22` `BUTTON_DOWN=23`

## Verificar

```bash
sudo systemctl status vigia-bootstrap.service
journalctl -u vigia-bootstrap.service -n 80 --no-pager
```

Mantenha a pasta `bootstrap` completa (executável + `_internal/`).
