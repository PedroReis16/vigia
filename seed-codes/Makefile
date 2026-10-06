# =============================================================================
# Makefile — seed-codes
# Único ponto de entrada para os utilitários de desenvolvimento (frame, seed
# do edge local, conversão AVI→MP4, clipe a partir de um vídeo).
#
# Portátil: GNU Make nativo no Windows (cmd.exe) e make no macOS/Linux (sh).
# Receitas só usam o subconjunto comum (cd, &&, echo). Checagens e .env
# ficam em funções Make — sem `command`, `test` ou `{ … }` POSIX.
#
#   make deps                         # pip install -r requirements.txt
#   make seed                         # gera edge-data/ (identity/network/…)
#   make publish-frame                # POST frame JPEG na API local
#   make publish-clip INPUT=video.mp4 # extrai PNG e envia o clipe
#   make convert INPUT=video.avi      # AVI → MP4 (mesmo nome .mp4)
#   make convert INPUT=v.avi OUTPUT=out.mp4
#   make test                         # testes de seed_local_edge e publish_clip
# =============================================================================

ifeq ($(OS),Windows_NT)
HOST_PYTHON ?= py
VENV_PYTHON := $(CURDIR)/.venv/Scripts/python.exe
else
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
VENV_PYTHON := $(CURDIR)/.venv/bin/python
endif

# O .venv local ganha do Python do sistema. HOST_PYTHON= na linha de comando
# ainda força o interpretador.
ifeq ($(origin HOST_PYTHON),command line)
PYTHON := $(HOST_PYTHON)
else
ifneq ($(wildcard $(VENV_PYTHON)),)
PYTHON := $(VENV_PYTHON)
else
PYTHON := $(HOST_PYTHON)
endif
endif

# `.env` em KEY=VALUE (opcional). Só estas chaves vão para o ambiente das
# receitas — `export` sozinho exportaria também require_* e o $(error) dispara
# com mensagem vazia assim que o .env existe.
SEED_ENV_KEYS := VIGIA_API_BASE_URL VIGIA_FIWARE_API_KEY VIGIA_STREAM_INGEST_URL
ifneq ($(wildcard $(CURDIR)/.env),)
include $(CURDIR)/.env
export $(SEED_ENV_KEYS)
endif

require_file = $(if $(wildcard $(1)),,$(error $(2)))
require_var  = $(if $(strip $(1)),,$(error $(2)))
unexport require_file require_var

.PHONY: help deps seed publish-frame publish-clip convert test

help:
	@echo Uso: make alvo
	@echo   make deps                         pip install -r requirements.txt
	@echo   make seed                         gera identity/network/classifier em edge-data/
	@echo   make seed DATA_DIR=path           diretorio de saida custom
	@echo   make seed API_BASE_URL=url        api_base_url em network.json
	@echo   make seed CLASSIFIER=gru          classifier.json math ou gru
	@echo   make seed ALSO_SERVICE_DATA=1     tambem grava em bootstrap/fall data/
	@echo   make publish-frame                POST JPEG em /devices/.../frame
	@echo   make publish-clip INPUT=video.mp4 extrai PNG e envia POST /devices/.../clips
	@echo   make publish-clip INPUT=v.mp4 FPS=12 MAX_SECONDS=30
	@echo   make publish-clip INPUT=v.mp4 DRY_RUN=1 FRAMES_DIR=./frames
	@echo   make convert INPUT=video.avi      AVI para MP4 saida mesmo nome .mp4
	@echo   make convert INPUT=v.avi OUTPUT=o.mp4
	@echo   make convert INPUT=v.avi COPY=1   remux sem reencodar
	@echo   make test                         testes de seed_local_edge e publish_clip
	@echo Configuracao opcional: .env nesta pasta VIGIA_API_BASE_URL etc.
	@echo Windows: HOST_PYTHON=py ou python. macOS/Linux: python3.
	@echo Se existir .venv nesta pasta, os alvos usam esse Python.

deps:
	@$(PYTHON) -m pip install -r requirements.txt

seed:
	$(call require_file,seed_local_edge.py,seed_local_edge.py nao encontrado.)
	@$(PYTHON) seed_local_edge.py $(if $(DATA_DIR),--data-dir "$(DATA_DIR)",) $(if $(API_BASE_URL),--api-base-url "$(API_BASE_URL)",) $(if $(FIWARE_API_KEY),--fiware-api-key "$(FIWARE_API_KEY)",) $(if $(STREAM_INGEST_URL),--stream-ingest-url "$(STREAM_INGEST_URL)",) $(if $(CLASSIFIER),--classifier "$(CLASSIFIER)",) $(if $(ALSO_SERVICE_DATA),--also-service-data,)

publish-frame:
	$(call require_file,publish_frame.py,publish_frame.py nao encontrado.)
	@$(PYTHON) publish_frame.py

publish-clip:
	$(call require_var,$(INPUT),Defina INPUT=caminho/video.mp4)
	$(call require_file,publish_clip.py,publish_clip.py nao encontrado.)
	@$(PYTHON) publish_clip.py "$(INPUT)" $(if $(FPS),--fps $(FPS),) $(if $(MAX_SECONDS),--max-seconds $(MAX_SECONDS),) $(if $(DEVICE_ID),--device-id "$(DEVICE_ID)",) $(if $(BASE_URL),--base-url "$(BASE_URL)",) $(if $(CLIP_ID),--clip-id "$(CLIP_ID)",) $(if $(FRAMES_DIR),--frames-dir "$(FRAMES_DIR)",) $(if $(DRY_RUN),--dry-run,) $(if $(WAIT),--wait,)

convert:
	$(call require_var,$(INPUT),Defina INPUT=caminho/video.avi)
	$(call require_file,video_converter.py,video_converter.py nao encontrado.)
	@$(PYTHON) video_converter.py "$(INPUT)" $(if $(OUTPUT),-o "$(OUTPUT)",) $(if $(COPY),--copy,)

test:
	$(call require_file,test_seed_local_edge.py,test_seed_local_edge.py nao encontrado.)
	@$(PYTHON) test_seed_local_edge.py
	@$(PYTHON) test_publish_clip.py
