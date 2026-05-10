# Deploy do fall-detection (Linux ARM64)

Guia curto para gerar o pacote PyInstaller e instalar na placa embarcada.

## Pré-requisitos (máquina de build)

- **Docker** (idealmente com suporte a imagens `linux/arm64`, ex.: Mac Apple Silicon ou Colima).
- **`make`**.
- Repositório na pasta `fall-detection/` com `model/classifier_svm.onnx` e fontes em `src/`.

## Gerar o “instalador” (artefato)

Na raiz de `fall-detection/`:

```bash
make build-linux-arm64
```

**Saída:**

- `dist/vigia-fall-detection-linux-arm64/` — diretório **onedir** (executável + `_internal/`; os dois precisam ir juntos).
- `dist/vigia-fall-detection-linux-arm64.tar.gz` — **um ficheiro** para copiar para a placa (recomendado).

O build corre dentro de Docker (`deploy/Dockerfile.linux-arm64-binary`), com **OpenCV headless** e reforço para não misturar `opencv-python` (GUI) com o que o Ultralytics puxa.

## Configuração (variáveis de ambiente)

A aplicação lê **`.env`** e variáveis de ambiente (ver `load_dotenv` em `Settings`).

1. Copie `.env.example` para um ficheiro de configuração na placa, por exemplo `/opt/vigia/.env`.
2. Ajuste pelo menos:
   - **`VIDEO_CAPTURE_SOURCE`** — índice V4L2 (`0`, `1`, …) ou URL (`rtsp://…`, `http://…`).
   - **`CAPTURES_PER_SECOND`**, **`DATA_PATH`**, integração FIWARE/MQTT conforme o ambiente.
   - **`SHOW_VIDEO`** — use **`False`** na placa (build headless; sem janela `imshow`).

Referência completa: ficheiro **`.env.example`** na raiz do projeto.

## Instalação na placa

### 1. Copiar ficheiros para a placa (máquina de desenvolvimento)

Após `make build-linux-arm64`, envie o tarball (e a unit systemd, na primeira vez ou quando mudar):

```bash
scp dist/vigia-fall-detection-linux-arm64.tar.gz usuario@placa:/tmp/
scp deploy/fall-detection.service usuario@placa:/tmp/   # primeira instalação ou atualização da unit
```

### 2. Configurar `.env` na placa (uma vez ou quando mudar credenciais)

Exemplo: `/opt/vigia/.env` (o `fall-detection.service` usa `EnvironmentFile=-/opt/vigia/.env`). Baseie-se em `.env.example`.

### 3. Primeira instalação do serviço systemd (só na primeira vez)

Na placa, como utilizador com `sudo`:

```bash
sudo install -d -m 755 /opt/vigia
sudo install -m 644 /tmp/fall-detection.service /etc/systemd/system/fall-detection.service
sudo systemctl daemon-reload
sudo systemctl enable fall-detection.service
```

### 4. Colocar ou atualizar a aplicação após exportar o build

Na placa — este fluxo **para o serviço**, remove a instalação antiga, extrai o novo tarball para `/opt/vigia`, renomeia para o caminho esperado pelo systemd e **volta a iniciar**:

```bash
sudo systemctl stop fall-detection.service
sudo rm -rf /opt/vigia/fall-detection
sudo tar -xzf /tmp/vigia-fall-detection-linux-arm64.tar.gz -C /opt/vigia
sudo mv /opt/vigia/vigia-fall-detection-linux-arm64 /opt/vigia/fall-detection
sudo chmod +x /opt/vigia/fall-detection/vigia-fall-detection
sudo systemctl start fall-detection.service
```

Notas:

- O tarball descompacta uma pasta chamada `vigia-fall-detection-linux-arm64`; o `mv` alinha com o layout em `deploy/fall-detection.service` (`ExecStart=/opt/vigia/fall-detection/vigia-fall-detection`).
- Se alterou só o código e já existe serviço + `.env`, basta repetir o bloco acima sempre que copiar um **novo** `.tar.gz` para `/tmp/`.

### 5. Verificar

```bash
sudo systemctl status fall-detection.service
journalctl -u fall-detection.service -n 80 --no-pager
```

### Outros requisitos

- **Câmera V4L2:** o utilizador do serviço precisa de permissão em `/dev/video*` (ex.: grupo `video`).
- Manter **toda** a pasta `fall-detection` (executável + `_internal/`); não apagar `_internal` nem mover só o binário.

## Desenvolvimento local vs build de deploy

| Ambiente | Ficheiro de dependências |
|----------|---------------------------|
| Debug local (GUI `cv2.imshow`) | `requirements.txt` → inclui `opencv-python` |
| Build Docker / binário para placa | `requirements-headless.txt` → `opencv-python-headless` |

Não é obrigatório clonar o repositório na placa: basta o **tar.gz** e o **`.env`**.

## Comandos úteis na placa

```bash
# Teste manual (sem systemd)
cd /opt/vigia/fall-detection
./vigia-fall-detection

# Logs em tempo real (também na secção “Verificar” acima)
journalctl -u fall-detection.service -f
```

## Se algo falhar após mudanças no código

- Sempre **regenerar** o pacote com `make build-linux-arm64` e **voltar a extrair** na placa (substituir a pasta inteira).
- Problemas típicos já tratados no pipeline: `libGL` (OpenCV GUI na placa headless), dependências Torch omitidas pelo `.spec` — o ficheiro **`vigia-fall-detection.spec`** está versionado no repositório.
