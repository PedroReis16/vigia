# Older fall

Boilerplate em Python para um único repositório com três pilares:

- inferência com conceitos de machine learning,
- pré-processamento para visão computacional,
- publicação/replicação de eventos para APIs externas.

## Estrutura

```text
src/
	api/           # FastAPI (rotas e factory da aplicação)
	core/          # Configuração e logging
	ml/            # Modelos de inferência (YOLO, fall detector)
	processor/     # Pipeline que orquestra visão + ML + replicação
	replication/   # Publicação de eventos para APIs externas
	runtime/      # Runtime local (preview webcam/vídeo)
	schemas/       # Contratos (Pydantic)
	vision/        # Captura, preview, extração de features (YOLO → sequências LSTM)
	main.py        # Ponto de entrada e CLI (--webcam / --video)
	bootstrap.py   # run() padrão e run_preview() para modo câmera/vídeo
```

### Visão (`src/vision/`) – organização interna

- **`preview_config.py`** – Configuração do preview (câmera/vídeo, YOLO, captura).
- **`frame_source.py`** – Fonte de frames: câmera ou arquivo de vídeo (modo debug); `create_frame_source()`.
- **`sequence_pipeline.py`** – Pipeline frames → YOLO → features → sequência `(n_frames, n_features)` para LSTM.
- **`capture_handler.py`** – Buffers de captura (manual com tecla `c`, contínuo) e overlays.
- **`preview_display.py`** – Janela OpenCV e desenho de overlays.
- **`webcam.py`** – Orquestrador do preview: coordena fonte, captura, pipeline e display (`WebcamPreviewService`).
- **`yolo_features.py`** – Extração de features a partir dos resultados do YOLO; save de sequências (npy/csv).

## Guia de organização (onde colocar cada coisa)

- `src/vision/`: entrada visual (captura, câmera/vídeo, extração de features, preview).
- `src/ml/`: modelo e inferência (YOLO, fall detector, pesos, score).
- `src/processor/`: fluxo de negócio (entrada → visão + ML → evento).
- `src/replication/`: integrações externas (REST, fila, retry).
- `src/api/`: endpoints HTTP (inference, health, eventos).
- `src/schemas/`: contratos de entrada/saída e eventos.
- `src/core/`: configurações, logging, infraestrutura.
- `src/runtime/`: ciclo de vida local (preview por webcam ou vídeo).

## Preview: webcam ou vídeo (captura para LSTM)

A aplicação pode abrir a visualização de duas formas **explícitas** pela linha de comando, ou usar o modo padrão (configurado no `.env`). Em todos os casos a **mesma lógica** é usada: captura manual (tecla `c`), modo contínuo, YOLO, geração de sequências para LSTM.

### Formas de inicialização do preview

| Comando | Comportamento |
|--------|----------------|
| `python -m src.main --webcam` | Abre a visualização **somente** com a webcam. |
| `python -m src.main --video <caminho>` | Abre a visualização **somente** com o arquivo de vídeo (mesma lógica de captura da webcam; útil para debug). |
| `python -m src.main` | Modo padrão: usa `.env` (`WEBCAM_PREVIEW_ENABLED`, `WEBCAM_DEBUG_VIDEO`). |

Exemplos:

```bash
# Webcam
python -m src.main --webcam

# Vídeo (modo debug: mesmo pipeline, arquivo em loop)
python -m src.main --video data/videos/meu_video.mp4
```

Na janela do preview:

- **Tecla `c`**: inicia captura dos próximos N frames e salva a sequência para LSTM (manual).
- **Tecla `q` ou `Esc`**: fecha a janela e encerra o preview.

### Configuração via `.env` (modo sem CLI)

Quando você **não** usa `--webcam` nem `--video`, o comportamento depende do `.env`:

```env
WEBCAM_PREVIEW_ENABLED=true
WEBCAM_INDEX=0,1
WEBCAM_WINDOW_NAME=older-fall webcam
WEBCAM_FLIP_HORIZONTAL=false
WEBCAM_DEBUG_VIDEO=              # vazio = webcam; preenchido = caminho do vídeo (modo debug)
YOLO_MODEL_PATH=yolov8s.pt
```

- `WEBCAM_PREVIEW_ENABLED=true`: ao rodar `python -m src.main`, a janela de preview abre (webcam ou vídeo conforme `WEBCAM_DEBUG_VIDEO`).
- `WEBCAM_DEBUG_VIDEO`: se definido com um caminho de vídeo, o preview usa o arquivo em vez da câmera (igual ao `--video` da CLI).

Se a imagem estiver espelhada:

```env
WEBCAM_FLIP_HORIZONTAL=true
```

## Setup rápido (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Modo de execução (runtime)

No `.env` você pode definir o modo de execução geral:

```env
APP_RUNTIME_MODE=local
```

Modos disponíveis:

- `api`: sobe FastAPI.
- `local`: roda local sem servidor HTTP (preview via `--webcam` / `--video` ou `.env`).
- `embedded`: mesmo fluxo local, para placa embarcada.

Comando único (a escolha webcam vs vídeo é feita pelos argumentos ou pelo `.env`):

```bash
python -m src.main              # padrão (.env)
python -m src.main --webcam     # forçar webcam
python -m src.main --video path # forçar vídeo
```

## Executando a API

```bash
python -m src.main
```

(Com `APP_RUNTIME_MODE=api` e servidor configurado.) Opcionalmente, Uvicorn direto:

```bash
uvicorn src.api.app:app --reload
```

Endpoints iniciais:

- `GET /health`
- `POST /v1/inference`
- `GET /v1/events`

## Exemplo de inferência

```bash
curl -X POST http://127.0.0.1:8000/v1/inference \
	-H "Content-Type: application/json" \
	-d '{
		"camera_id": "cam-01",
		"features": [0.2, 0.9, 0.8, 0.7]
	}'
```

## Replicação para API externa

Configure no `.env`:

```env
REPLICATION_ENABLED=true
REPLICATION_URL=https://sua-api.com/events
REPLICATION_URLS=https://api-1.com/events,https://api-2.com/events
REPLICATION_AUTH_TOKEN=seu_token_opcional
REPLICATION_TIMEOUT_SECONDS=2.0
```

Quando uma queda é detectada pelo pipeline, o evento é:

1. armazenado localmente (consultável em `GET /v1/events`),
2. enviado para todos os endpoints externos configurados.

Observabilidade da publicação:

- `GET /v1/replication-status`: targets configurados e últimas tentativas de entrega.

## Próximos passos sugeridos

- Trocar `BaselineFallDetector` por um modelo real (PyTorch, scikit-learn, ONNX).
- Ligar o pipeline de queda às sequências geradas pelo preview (LSTM/fall detection em tempo real).
- Adicionar autenticação e fila (RabbitMQ/Kafka) na camada de replicação.
