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
	ml/            # Modelos de inferência
	processor/     # Pipeline que orquestra visão + ML + replicação
	replication/   # Publicação de eventos para APIs externas
	schemas/       # Contratos (Pydantic)
	vision/        # Extração/pré-processamento de features
	main.py        # Ponto de entrada da aplicação
```

## Guia de organização (onde colocar cada coisa)

- `src/vision/`: tudo sobre entrada visual (captura de frame, limpeza da imagem, extração de features).
- `src/ml/`: modelo e lógica de inferência (carregar pesos, pré/pós-processamento do modelo, score).
- `src/processor/`: fluxo de negócio principal (recebe entrada, chama visão + ML, decide se gera evento).
- `src/replication/`: integrações externas (publicar em REST APIs, autenticação, retry, fallback, fila).
- `src/api/`: endpoints HTTP para consumir o sistema internamente (`inference`, health, observabilidade).
- `src/schemas/`: contratos de entrada/saída e eventos compartilhados entre camadas.
- `src/core/`: configurações, logging e utilitários comuns de infraestrutura.

Regra prática: se a mudança envolver modelo, mexa em `ml`; se envolver integração com terceiros, mexa em `replication`; se envolver ordem do fluxo, mexa em `processor`.

## Webcam ao iniciar a aplicação (sem ML)

Para o cenário que você descreveu, o código fica em `src/vision/`.

- Implementação do preview: `src/vision/webcam.py`.
- Inicialização no ciclo de vida da API: `src/api/app.py`.
- Configurações do dispositivo/janela: `.env` (campos abaixo).

No seu `.env`:

```env
WEBCAM_PREVIEW_ENABLED=true
WEBCAM_INDEX=0
WEBCAM_WINDOW_NAME=older-fall webcam
```

Ao subir o projeto (`python -m src.main`), a janela da webcam abre automaticamente.
Para fechar, pressione `q` (ou `Esc`) na janela da câmera, ou encerre a aplicação.

## Setup rápido (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Formas de inicialização (simples)

Defina no `.env` o modo de execução:

```env
APP_RUNTIME_MODE=api
```

Modos disponíveis:

- `api`: sobe FastAPI.
- `local`: roda local sem servidor HTTP.
- `embedded`: mesmo fluxo local, para placa embarcada.

Comando único para todos os modos:

```bash
python -m src.main
```

## Executando a API

```bash
python -m src.main
```

Opcionalmente, você ainda pode usar Uvicorn direto:

```bash
uvicorn src.main:app --reload
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

- `GET /v1/replication-status`: mostra os targets configurados e últimas tentativas de entrega.

## Próximos passos sugeridos

- Trocar `BaselineFallDetector` por um modelo real (PyTorch, scikit-learn, ONNX).
- Ligar `vision` em frames reais de câmera (OpenCV/RTSP).
- Adicionar autenticação e fila (RabbitMQ/Kafka) na camada de replicação.