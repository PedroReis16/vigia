# VIGIA — Sistema doméstico para o monitoramento de quedas

O **VIGIA** detecta quedas de pessoas em ambiente doméstico a partir de uma câmera ligada a um **Raspberry Pi 5**. Toda a inferência roda na própria placa (edge): nenhuma imagem precisa sair de casa para que uma queda seja identificada. Quando o evento é detectado, a placa avisa a nuvem via MQTT/FIWARE e os responsáveis recebem o alerta no aplicativo mobile ou na interface web, onde também podem ver o vídeo ao vivo e o clipe da queda.

- **Produção (web):** <https://vigiadeteccoes.com.br>
- **Produção (API e serviços):** `https://services.vigiadeteccoes.com.br`

---

## Sumário

- [Visão geral](#visão-geral)
- [Arquitetura do sistema](#arquitetura-do-sistema)
- [Tecnologias utilizadas](#tecnologias-utilizadas)
- [Pré-requisitos](#pré-requisitos)
- [Mapeamento de pastas e projetos](#mapeamento-de-pastas-e-projetos)
- [Como executar (ambiente local)](#como-executar-ambiente-local)
- [Como instalar e fazer deploy](#como-instalar)
- [Documentação complementar](#documentação-complementar)

---

## Visão geral

### Pipeline de detecção na placa

![Pipeline de detecção de quedas no Raspberry Pi 5](docs/images/pipeline-deteccao.png)

1. **Câmera:** captura contínua de vídeo.
2. **Estimativa de pose:** o modelo YOLO pose (`yolo26s-pose`, exportado para NCNN na placa) extrai 17 pontos-chave por pessoa, com rastreamento entre frames (BoT-SORT).
3. **Normalização e filtragem:** cada ponto `p(x, y, c)` passa por validação de confiança e por um filtro de Kalman, que reduz o ruído entre frames.
4. **Janela deslizante:** os pontos de cada pessoa são acumulados numa janela temporal reamostrada em cadência fixa.
5. **Classificação do evento:** um classificador decide `FALL` / `NOT FALL`. Há dois motores intercambiáveis: `math` (regras geométricas, padrão) e `gru` (rede recorrente GRU exportada em ONNX).

Quando o estado muda para `fall`, a placa publica o atributo no FIWARE e envia à API a janela de frames ao redor do evento, que vira um clipe MP4.

### Funcionalidades

- Detecção de quedas 100% local, no Raspberry Pi 5.
- Alerta em tempo real: push (Firebase), SignalR e caixa de notificações no app e na web.
- Vídeo ao vivo sob demanda (RTMP → MediaMTX → WebRTC/WHEP), ligado só quando alguém assiste.
- Clipes da queda com miniatura e reprodução no app e na web.
- Desfoque (blur) opcional das pessoas nas imagens enviadas.
- Pareamento da placa pelo app via Bluetooth (BLE), com configuração de Wi-Fi e certificado de cliente.
- Compartilhamento de dispositivos entre usuários por convite.
- Atualização remota (OTA) do software da placa.

---

## Arquitetura do sistema

![Arquitetura do sistema VIGIA](docs/images/arquitetura-sistema.png)

O sistema é dividido em duas camadas:

**Edge (casa do usuário)**

- Câmera + Raspberry Pi 5 executando o serviço `vigia` (projeto [`vigia-onboard`](vigia-onboard/)).
- O serviço tem três processos: **captura** (YOLO + classificação), **integração** (MQTT/FIWARE) e **interface** (BLE, Wi-Fi, LCD 16x2 e botões).
- Ao detectar uma queda, publica o evento por **MQTTS** no broker Mosquitto da nuvem.

**Cloud**

- **FIWARE** (IoT Agent Ultralight + Orion Context Broker + STH-Comet) recebe a telemetria e encaminha os comandos (`stream_on`, `clips_on`, `blur_on`, `device_update` etc.) para a placa.
- **API de gestão** ([`vigia-api`](vigia-api/), .NET) recebe o webhook do Orion, grava o alerta, envia push e notifica os clientes via SignalR. Também gerencia usuários, dispositivos, grupos, clipes e versões OTA.
- **Keycloak** cuida de login, cadastro e redefinição de senha; os usuários são sincronizados com a API via **RabbitMQ**.
- **MediaMTX** recebe o vídeo RTMP da placa e o entrega aos clientes por WebRTC (WHEP).
- **PostgreSQL**, **Redis** e **MinIO** (armazenamento S3) dão suporte à API; o **Traefik** faz o proxy reverso e o TLS.

**Clientes**

- **Aplicativo** Flutter ([`vigia_ui`](vigia_ui/)) para Android e iOS.
- **Web** Angular ([`vigia-web`](vigia-web/)) publicada no Cloudflare Pages.

```
 Evento ─▶ Câmera ─▶ Raspberry Pi 5 ──MQTTS──▶ Mosquitto ─▶ IoT Agent ─▶ Orion ──webhook──▶ API ──HTTPS / SignalR / push──▶ App / Web
                         │                                                                   ▲
                         └──────────── RTMPS (vídeo ao vivo) ─▶ MediaMTX ──WHEP────────────────┘
```

Detalhes de cada fluxo (pareamento, detecção, streaming, OTA, compartilhamento, clipes) estão em [`docs/project-structure.md`](docs/project-structure.md#8-fluxos-de-dados).

---

## Tecnologias utilizadas

| Camada | Tecnologias |
|--------|-------------|
| **Edge** | Raspberry Pi 5 (8 GB) com Raspberry Pi OS Lite 64-bit · Python 3.12 · Ultralytics YOLO pose (NCNN / ONNX / CoreML) · OpenCV · ONNX Runtime (GRU) · paho-mqtt · `bless` (BLE) · NetworkManager · gpiozero / lgpio · RPLCD (LCD 16x2) · FFmpeg · PyInstaller · systemd |
| **API** | .NET 10 · ASP.NET Core · Entity Framework Core + Npgsql · SignalR · Redis · RabbitMQ · Firebase Admin · Swagger/OpenAPI |
| **Infraestrutura** | Docker / Docker Compose · Traefik v3 · PostgreSQL 15 · Redis · MinIO · Keycloak 26 · RabbitMQ · MediaMTX · Portainer |
| **FIWARE** | Orion Context Broker · IoT Agent Ultralight · Mosquitto (MQTT/MQTTS/WSS) · STH-Comet · MongoDB |
| **Mobile** | Flutter (Dart ≥ 3.12) · Riverpod · go_router · dio · flutter_blue_plus · flutter_webrtc · signalr_netcore · Firebase Cloud Messaging (Android) · i18n pt/en/es |
| **Web** | Angular 22 · Optimus UI 2 · Tailwind CSS 4 · ngx-translate · Keycloak (Authorization Code + PKCE) · Vitest · pnpm · Cloudflare Pages |
| **Pesquisa / ML** | `vigia-lab` (captura e avaliação dos classificadores com o mesmo pipeline da placa) |
| **CI/CD** | GitHub Actions · Docker Hub · Portainer webhooks · Cloudflare Pages · gitleaks · bandit |

---

## Pré-requisitos

### Desenvolvimento (todos os projetos)

| Ferramenta | Versão | Usada em |
|------------|--------|----------|
| Git | — | todo o repositório |
| Docker + Docker Compose | Docker Desktop recente | stack local, builds ARM64 em hosts não-ARM |
| .NET SDK | 10.0 | `vigia-api` |
| Python | 3.12 ou 3.13 | `vigia-onboard`, `vigia-bootstrap`, `vigia-devices`, `vigia-lab`, `seed-codes` |
| FFmpeg | no `PATH` | streaming e clipes (`vigia-onboard`, `vigia-devices`, `seed-codes`) |
| GNU Make | — | `vigia-onboard`, `vigia-bootstrap`, `seed-codes`, `vigia-lab` (no Windows, use o Make com Git Bash) |
| Node.js + pnpm | Node 22 · pnpm 11 | `vigia-web` |
| Flutter SDK | stable (Dart ≥ 3.12) · Java 17 para o Android | `vigia_ui` |

Credenciais que **não** são versionadas e precisam ser obtidas à parte:

- Firebase: `vigia_ui/android/app/google-services.json`, `vigia-web/public/firebase-config.js` e a service account da API (`docker-compose/local/firebase-service-account.json`, a partir do `.example`). Sem elas o sistema funciona, mas sem push.
- Arquivos `.env` de cada projeto, criados a partir dos respectivos `.env.example`.

### Placa (edge)

- Raspberry Pi 5 com Raspberry Pi OS Lite 64-bit e acesso SSH.
- Câmera USB (UVC).
- Opcional: display LCD 16x2 (I2C) e botões GPIO para o menu local.
- Conexão com a internet (Wi-Fi configurado pelo pareamento BLE).

O passo a passo de preparação do sistema operacional (hostname/mDNS, SSH por chave, Tailscale e redes Wi-Fi) está em [`docs/raspberry-pi.md`](docs/raspberry-pi.md).

---

## Mapeamento de pastas e projetos

```
vigia/
├── vigia-onboard/        # Serviço da placa: captura + YOLO + classificação, MQTT/FIWARE, streaming, clipes, BLE/Wi-Fi/LCD, OTA
├── vigia-bootstrap/      # Control plane legado da placa (BLE, Wi-Fi, LCD, OTA) — release "bootstrap"
├── vigia-api/            # API de gestão (.NET) + bibliotecas compartilhadas e testes
├── vigia-web/            # Interface web (Angular)
├── vigia_ui/             # Aplicativo mobile (Flutter, Android/iOS)
├── vigia-devices/        # Worker que simula dispositivos na nuvem (demonstrações)
├── vigia-lab/            # Bancada de captura e avaliação dos classificadores (roda no notebook)
├── seed-codes/           # Utilitários de desenvolvimento (seed do edge local, envio de frames e clipes)
├── docker-compose/
│   ├── local/            # Stack completa de desenvolvimento
│   ├── deploy/           # Stack de produção da VM (infra.sh + docker-compose.yaml)
│   └── dockerfiles/      # Dockerfiles da API, web, worker, Keycloak e MediaMTX
├── docs/                 # Documentação técnica (estrutura, Raspberry Pi, FIWARE, diagramas)
├── edge-data/            # device.json mock do edge local (gerado pelo seed; ignorado pelo Git)
└── .github/workflows/    # CI (quality gate) e pipelines de release
```

| Projeto | Descrição | Ponto de entrada | Documentação |
|---------|-----------|------------------|--------------|
| [`vigia-onboard`](vigia-onboard/) | Serviço único da placa (`vigia.service`): processos de captura, integração e interface | `main.py` / `Makefile` | [`docs/DEPLOY.md`](vigia-onboard/docs/DEPLOY.md) |
| [`vigia-bootstrap`](vigia-bootstrap/) | Control plane anterior ao `onboard` (pareamento BLE, Wi-Fi, LCD, OTA) | `main.py` / `Makefile` | [`docs/DEPLOY.md`](vigia-bootstrap/docs/DEPLOY.md) |
| [`vigia-api`](vigia-api/) | API REST + SignalR. Bibliotecas `Vigia.Models`, `Vigia.Database`, `Vigia.Fiware`, `Vigia.Cache`, `Vigia.Cloud`, `Vigia.AMQP` | `Vigia.API/Program.cs` (base path `/vigia`) | [`docs/fiware.md`](docs/fiware.md) |
| [`vigia-web`](vigia-web/) | SPA Angular (camadas `core` / `pages` / `shared`) | `src/main.ts` | [`README`](vigia-web/README.md) |
| [`vigia_ui`](vigia_ui/) | App Flutter (camadas `core` / `domain` / `data` / `presentation`) | `lib/main.dart` | [`README`](vigia_ui/README.md) |
| [`vigia-devices`](vigia-devices/) | Simula até 7 dispositivos: vídeo em loop, stream, miniaturas e quedas aleatórias | `main.py` | [`README`](vigia-devices/README.md) |
| [`vigia-lab`](vigia-lab/) | Captura cenas rotuladas e compara os classificadores (Math, GRU 34/37/38) | `python -m vigia_lab` / `Makefile` | [`README`](vigia-lab/README.md) |
| [`seed-codes`](seed-codes/) | `make seed`, `make publish-frame`, `make publish-clip`, `make convert` | `Makefile` | — |
| [`docker-compose`](docker-compose/) | Orquestração local e de produção | `local/` e `deploy/` | [`project-structure.md`](docs/project-structure.md#docker-compose) |

A descrição módulo a módulo de cada projeto está em [`docs/project-structure.md`](docs/project-structure.md).

---

## Como executar (ambiente local)

### 1. Subir a infraestrutura e a API

```bash
cd docker-compose/local
cp .env.example .env    # preencha as senhas do Postgres e do Keycloak
docker compose up -d --build
```

A API sobe em modo **Debug**, aplica as migrations e cria os dispositivos de teste (`Vigia-a1b2c3d4` para o edge local e 7 dispositivos simulados) no grupo do usuário `admin`, já provisionados no FIWARE.

| Serviço | Endereço local |
|---------|----------------|
| API (via Traefik) | <http://localhost:81/vigia> |
| API (direto) / Swagger | <http://localhost:8090/vigia> |
| Keycloak | <http://localhost:81/auth> (direto em <http://localhost:8081/auth>) |
| MediaMTX (WHEP) | <http://localhost:81/live> |
| Traefik dashboard | <http://localhost:8080> |
| MinIO console | <http://localhost:9001> |
| RabbitMQ management | <http://localhost:15672> |
| MailHog (e-mails do Keycloak) | <http://localhost:8025> |
| RedisInsight | <http://localhost:5540> |

> Para depurar a API fora do Docker: `dotnet run --project vigia-api/Vigia.API` (porta `8090`), com o restante da stack no ar. O `.vscode/launch.json` já traz configurações para API, app, bootstrap e onboard.

### 2. Interface web

```bash
cd vigia-web
pnpm install
pnpm start              # http://localhost:4200
```

O ambiente local aponta para a API e o Keycloak em `localhost:81` (`src/environments/environment.ts`).

### 3. Aplicativo mobile

```bash
cd vigia_ui
flutter pub get
make builder            # geração de código (Riverpod), em outro terminal
flutter run
```

O build de debug lê `homolog.env` (`API_URL`, `STREAM_BASE_URL`, `KEYCLOAK_URL`…). Num aparelho físico, use o IP do computador na LAN e inclua esse host em `Keycloak:AdditionalValidIssuers` da API.

### 4. Serviço de detecção (sem Raspberry Pi)

O `vigia-onboard` roda em Windows, macOS ou Linux usando a webcam (ou um arquivo de vídeo) no lugar da câmera da placa.

```bash
# gera edge-data/device.json alinhado ao dispositivo de teste da API
cd seed-codes
make deps
make seed

cd ../vigia-onboard
cp .env.example .env    # CAPTURE_SOURCE=0 (webcam) ou caminho de um vídeo; DATA_DIR=../edge-data
make run                # captura + integração + interface em paralelo
```

Cada processo também pode ser iniciado sozinho: `make capture`, `make integration` e `make interface`. Na primeira execução o Makefile cria o `.venv`, instala as dependências e exporta o modelo YOLO para o formato do sistema operacional.

### 5. Dispositivos simulados (opcional)

```bash
cd vigia-devices
python -m venv .venv && .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python main.py          # cada instância assume um ID livre do pool
```

### Testes

| Projeto | Comando |
|---------|---------|
| `vigia-api` | `dotnet test vigia-api/Vigia.slnx` |
| `vigia-onboard`, `vigia-bootstrap`, `vigia-devices` | `pytest` na pasta do projeto |
| `vigia-lab`, `seed-codes` | `make test` |
| `vigia-web` | `pnpm exec ng lint` · `pnpm test` |
| `vigia_ui` | `flutter analyze` · `flutter test` |

Os mesmos testes rodam no CI (`continuos-integration.yml`) em todo PR para `develop` ou `master`, apenas para os projetos alterados.

---

## Como instalar

### Visão geral das versões

Cada componente tem um workflow de release **manual** (`workflow_dispatch`) no GitHub Actions. Ao final, o workflow move uma **tag rolling** (sobrescrita a cada release) que identifica a última versão publicada.

| Componente | Workflow | Tag | Artefato | Destino |
|------------|----------|-----|----------|---------|
| API | `service-release.yml` | `service` | Imagem `pedroreis16/vigia-api:latest` | VM (Docker), redeploy via Portainer |
| Web | `web-release.yml` | `web` | Build estático Angular | Cloudflare Pages (`vigiadeteccoes.com.br`) |
| Worker de simulação | `worker-release.yml` | `worker` | Imagem `pedroreis16/vigia-devices:latest` | VM (Docker), redeploy via Portainer |
| Serviço da placa | `onboard-release.yml` | `onboard` | `vigia-onboard-deploy.zip` + pacote OTA | Raspberry Pi 5 |
| Bootstrap (legado) | `bootstrap-pipeline.yml` | `bootstrap` | `vigia-bootstrap-deploy.zip` | Raspberry Pi 5 |
| App mobile | `mobile-release.yml` | `mobile` | APK assinado | Google Drive |

### Cloud — infraestrutura da VM

A produção roda numa VM Linux com Docker, em `/home/ubuntu/dockers`. A instalação é feita em duas etapas:

**1. Infraestrutura base (`infra.sh`)** — sobe, com `docker run`, a rede `vigia-network`, Redis, PostgreSQL, MinIO, Traefik (TLS Let's Encrypt via DNS da Cloudflare), MediaMTX, Portainer e a stack FIWARE (MongoDB, Orion, IoT Agent, STH-Comet e Mosquitto).

```bash
cp docker-compose/deploy/infra.env.example .env   # na VM, ao lado do infra.sh
bash infra.sh
```

O `.env` precisa, no mínimo, de `CLOUDFLARE_DNS_API_TOKEN`, `MOSQUITTO_IOTAGENT_PASSWORD`, `MOSQUITTO_DEVICE_PASSWORD` e `PORTAINER_ADMIN_PASSWORD` (mínimo de 12 caracteres).

| Domínio | Uso |
|---------|-----|
| `services.vigiadeteccoes.com.br` | API (`/vigia`), Keycloak (`/auth`), FIWARE e stream |
| `ingest.vigiadeteccoes.com.br:8443` | Ingestão RTMPS do vídeo das placas |
| `mqtt.vigiadeteccoes.com.br:8883` | MQTTS das placas (DNS-only na Cloudflare) |
| `mosquitto.vigiadeteccoes.com.br` | MQTT sobre WSS |
| `portainer.vigiadeteccoes.com.br` | Painel do Portainer |

**2. Stack de aplicação (`docker-compose.yaml`)** — RabbitMQ, Keycloak (com inicialização do schema no Postgres e reaplicação do realm), API e worker de simulação.

```bash
cp docker-compose/deploy/.env.example default.env   # variáveis da API (ASP.NET Core, Section__Key)
# o mesmo .env do infra.sh (modelo: infra.env.example) também traz RABBITMQ_PASSWORD,
# POSTGRES_ADMIN_PASSWORD, KEYCLOAK_DB_PASSWORD, KEYCLOAK_ADMIN_PASSWORD…
docker compose -p vigia up -d
```

A CA usada para emitir os certificados de cliente das placas fica em `./certificates` (montada na API e no Traefik). O mTLS das rotas da placa é controlado por `DeviceAuth__RequireClientCertificate`.

### Cloud — API (`service`)

1. Execute o workflow **service-release** no GitHub Actions.
2. O pipeline roda os testes .NET e a verificação de segurança, gera a imagem com `docker-compose/dockerfiles/vigia-api.dockerfile`, publica `pedroreis16/vigia-api:latest` no Docker Hub e chama o webhook do Portainer, que recria o container na VM.
3. As migrations do banco são aplicadas automaticamente na inicialização da API, e o schema FIWARE (`Fiware:Devices`) é sincronizado com os dispositivos já provisionados.

### Cloud — Web (`web`)

1. Execute o workflow **web-release**.
2. O pipeline roda lint, testes e `ng build --configuration=production`, injeta a configuração do Firebase a partir dos secrets e publica no projeto `vigia-web` do Cloudflare Pages.
3. O `public/_worker.js` repassa `vigiadeteccoes.com.br/auth` para o Keycloak da VM, e o `_redirects` garante o fallback da SPA (`/invite/*`, `/*` → `index.html`).

### Cloud — Worker de simulação (`worker`)

Execute o workflow **worker-release**. A imagem `pedroreis16/vigia-devices:latest` é gerada com os vídeos de `vigia-devices/assets/videos/` embutidos e o container é recriado via webhook do Portainer (`PORTAINER_DEVICES_WEBHOOK_URL`).

### Edge — Serviço da placa (`onboard`)

O pacote `onboard` instala **um único serviço**, `vigia.service`, em `/opt/vigia/onboard/`. Ele substitui as instalações antigas de `vigia-bootstrap` e `fall-detection`, que são desativadas automaticamente se existirem.

**Gerar o pacote**

- Pelo CI: execute **onboard-release** (build nativo em runner ARM64). A opção `upload_to_api` também envia o pacote OTA para a API.
- Localmente, na pasta `vigia-onboard/`:

  ```bash
  make ensure-model         # exporta o YOLO pose para NCNN
  make build-linux-arm64    # nativo em linux/arm64; nos demais hosts usa Docker buildx
  make package-ota          # opcional: tarball OTA
  ```

**Instalar na placa**

```bash
scp vigia-onboard-deploy.zip vigia@vigia.local:/tmp/
ssh vigia@vigia.local
cd /tmp
unzip -o vigia-onboard-deploy.zip -d vigia-onboard-deploy
sudo ./vigia-onboard-deploy/install-on-board.sh
```

O instalador adiciona `ffmpeg`, as bibliotecas de runtime do OpenCV, `liblgpio1` e `i2c-tools`, habilita o I2C do LCD e ativa o `vigia.service`.

```bash
systemctl status vigia.service
journalctl -u vigia.service -n 80 --no-pager
```

**Primeiro uso:** o serviço sobe aguardando o pareamento. Pelo app, o usuário encontra a placa via BLE, envia o Wi-Fi e recebe a identidade do dispositivo, o certificado de cliente e a URL de ingestão de vídeo; tudo é gravado em `/opt/vigia/device.json` e a captura é liberada.

**Atualizações:** novas versões chegam por OTA (comando `device_update` via FIWARE). O serviço substitui o bundle sem parar e reinicia após 45 segundos.

**Desinstalar:**

```bash
sudo vigia-uninstall                # mantém device.json e .env
sudo vigia-uninstall --purge-data   # remove também identidade, rede e estado OTA (será preciso parear de novo)
```

Configurações opcionais (`FRAME_RATE`, `CLASSIFIER`, `YOLO_MODEL`) podem ser definidas em `/opt/vigia/.env`. Detalhes em [`vigia-onboard/docs/DEPLOY.md`](vigia-onboard/docs/DEPLOY.md).

### Edge — Bootstrap (`bootstrap`, legado)

Usado apenas em placas que ainda não migraram para o `onboard`. O pacote `vigia-bootstrap-deploy.zip` (release **Vigia Bootstrap**) é instalado da mesma forma, com `sudo ./vigia-bootstrap-deploy/install-on-board.sh`, e ativa `vigia-bootstrap.service` em `/opt/vigia/bootstrap/`. Para remover: `sudo vigia-bootstrap-uninstall [--purge-data]`. Veja [`vigia-bootstrap/docs/DEPLOY.md`](vigia-bootstrap/docs/DEPLOY.md).

### Mobile (`mobile`)

1. Execute o workflow **mobile-release**.
2. O pipeline passa por preflight, verificação de segredos, análise estática e testes, gera o APK assinado com `production.env` e o publica numa pasta do Google Drive.
3. Instale o APK no aparelho Android. O push (FCM) está disponível apenas no Android; o iOS é compilado localmente pelo Xcode.

---

## Documentação complementar

| Documento | Conteúdo |
|-----------|----------|
| [`docs/project-structure.md`](docs/project-structure.md) | Estrutura detalhada, decisões arquiteturais, regras de negócio e fluxos de dados |
| [`docs/raspberry-pi.md`](docs/raspberry-pi.md) | Preparação da placa: hostname/mDNS, SSH, Tailscale e Wi-Fi |
| [`docs/fiware.md`](docs/fiware.md) | Schema de atributos e comandos FIWARE e como alterá-lo |
| [`vigia-onboard/docs/DEPLOY.md`](vigia-onboard/docs/DEPLOY.md) | Build e instalação do serviço da placa |
| [`vigia-lab/README.md`](vigia-lab/README.md) | Captura e avaliação dos classificadores |
