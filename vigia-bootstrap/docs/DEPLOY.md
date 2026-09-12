# Deploy do vigia-bootstrap (Linux ARM64)

Guia curto para gerar o pacote PyInstaller onedir e instalar na placa como serviço systemd.

O bootstrap é o **control plane** da placa: identidade, pareamento BLE, Wi‑Fi (`nmcli`), LCD 16x2 e GPIO. Grava `/opt/vigia/identity.json`, `/opt/vigia/network.json` e `/opt/vigia/classifier.json` (modelo de classificação; default `math`). Só depois arranca `fall-detection.service`.

Se `identity.json` e `network.json` já existirem, o pareamento BLE é ignorado e o fall é iniciado de imediato.

## Interface física (predefinições BCM)

| Função | GPIO | Notas |
| --- | --- | --- |
| OK | 17 | curto = confirmar no overlay/editor; hold 2 s no WiFi = alterar rede; hold 5 s no Serviço = desvincular |
| Cima | 22 | ecrã anterior (no editor: carácter anterior) |
| Baixo | 23 | ecrã seguinte (no editor: carácter seguinte) |
| LCD 16x2 I2C | SDA 2 / SCL 3 | backpack PCF8574, endereço `0x27`, bus 1 |

O feedback de estado (pareamento, Wi‑Fi, fall) é só no LCD. Durante o vínculo o ecrã de eficiência mostra o estágio BLE (app ligada, utilizador encontrado, a esperar internet, a conectar, rede inválida).

Ecrãs (cima/baixo em ciclo): **Eficiência** (`F  12%  48M` / `S  34% 412M  55C`) → **WiFi** (SSID; hold 2 s = Alterar rede?) → **Servico** (ativo/parado; hold 5 s = Desvincular?) → **Modelo** (Matematico/GRU; OK = escolher; aplica e reinicia o fall se provisionado) → **Buscar atualiz.** (OK = procurar OTA). Nos overlays, cima/baixo escolhem `>Cancelar` / `>Confirmar` (ou `>Matematico` / `>GRU` no pick de modelo) e OK aplica (não mudam de ecrã). Sem actividade o LCD entra em standby (`LCD_STANDBY_SECONDS`, predefinição 20); o primeiro clique só acende a backlight.

No Pi 5 o bootstrap abre `lgpio` em `/dev/gpiochip0` ou `gpiochip4` (conforme o kernel) e faz poll dos botões a 50 ms.

- **Alterar rede** tenta `nmcli` com o SSID/senha digitados. Só grava `network.json` se a ligação for válida; se falhar, mantém a rede atual.
- **Modelo** grava `classifier.json` (`math` / `gru`) e reinicia `fall-detection` quando o valor muda e o device está provisionado (ou o serviço ativo). Unlink / limpar Wi‑Fi **não** apagam `classifier.json`.
- **Desvincular** corre `vigia_reset_config.sh`: pára o fall e limpa dados locais do fall; **mantém** `identity.json`, `network.json`, `classifier.json`, `.env` e perfis Wi‑Fi. O bootstrap reabre o beacon BLE para um novo utilizador na mesma rede.

Na **Raspberry Pi 5** o gpiozero precisa de **liblgpio** em runtime (chip 0 nos kernels recentes, chip 4 nos mais antigos). O `install.sh` instala `liblgpio1` e `i2c-tools` via apt e activa o I2C (`raspi-config nonint do_i2c 0`). Não é preciso `apt-get` manual na placa.

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
- `dist/vigia-bootstrap-linux-arm64.tar.gz` — bundle interno.
- `dist/vigia-bootstrap-deploy.zip` — **pacote único** para enviar à placa.

## Instalação na placa

Instale **primeiro** o bootstrap, depois o fall-detection.

Baixe `vigia-bootstrap-deploy.zip` (release `bootstrap` ou `dist/` após o build) e envie um único ficheiro:

```bash
scp vigia-bootstrap-deploy.zip usuario@placa:/tmp/
```

Na placa:

```bash
cd /tmp
unzip -o vigia-bootstrap-deploy.zip -d vigia-bootstrap-deploy
sudo ./vigia-bootstrap-deploy/install-on-board.sh
```

Isto corre `install.sh`, instala `liblgpio1` e `i2c-tools` se faltarem, activa I2C, extrai para `/opt/vigia/bootstrap/`, instala o unit e os scripts (incluindo `vigia-bootstrap-uninstall`), e no fim remove o zip e a pasta temporária.

Desinstalar:

```bash
sudo vigia-bootstrap-uninstall
# ou, apagando também identity/network/.env:
sudo vigia-bootstrap-uninstall --purge-data
```

Só remove os pacotes apt que **este** `install.sh` tiver adicionado (não desinstala `liblgpio1` se já existia). O I2C fica ligado.

O unit usa `EnvironmentFile=-/opt/vigia/.env` (opcional, partilhado com o fall-detection):

- `DATA_DIR=/opt/vigia`
- `WIFI_MOCK=false` na placa (`true` só em testes: aceita qualquer SSID)
- `WIFI_MOCK_RESULT=success` (quando `WIFI_MOCK=true`)
- `LCD_ENABLED=true`
- `LCD_I2C_ADDR=0x27`
- `BUTTON_OK=17` `BUTTON_UP=22` `BUTTON_DOWN=23`
- `LCD_STANDBY_SECONDS=20`

Com `DATA_DIR=/opt/vigia`, OTA fica em `/var/lib/vigia/ota` (override: `VIGIA_OTA_DIR`). Em debug local (`DATA_DIR=./data`), OTA vai para `{DATA_DIR}/ota` sem precisar de paths de instalação.

O LCD mostra o estágio de vínculo (`Aguardando app`, `Usuario encontrado`, `Esperando internet`, `A conectar...`, `Rede invalida`, …). Credenciais Wi‑Fi só são gravadas em `network.json` depois do `nmcli` ligar com sucesso.

## Verificar

```bash
sudo systemctl status vigia-bootstrap.service
journalctl -u vigia-bootstrap.service -n 80 --no-pager
```

Mantenha a pasta `bootstrap` completa (executável + `_internal/`).
