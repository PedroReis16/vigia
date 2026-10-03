# =============================================================================
# Makefile — seed-codes
# Único ponto de entrada para os utilitários de desenvolvimento (frame, seed
# do edge local, conversão AVI→MP4).
#
# Portátil: GNU Make nativo no Windows (cmd.exe) e make no macOS/Linux (sh).
# Receitas só usam o subconjunto comum (cd, &&, echo). Checagens e .env
# ficam em funções Make — sem `command`, `test` ou `{ … }` POSIX.
#
#   make deps                         # pip install -r requirements.txt
#   make seed                         # gera edge-data/ (identity/network/…)
#   make publish-frame                # POST frame assinado na API local
#   make convert INPUT=video.avi      # AVI → MP4 (mesmo nome .mp4)
#   make convert INPUT=v.avi OUTPUT=out.mp4
#   make test                         # testes de seed_local_edge
# =============================================================================

ifeq ($(OS),Windows_NT)
HOST_PYTHON ?= py
else
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
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

.PHONY: help deps seed publish-frame convert test

help:
	@echo Uso: make alvo
	@echo   make deps                         pip install -r requirements.txt
	@echo   make seed                         gera identity/network/classifier em edge-data/
	@echo   make seed DATA_DIR=path           diretorio de saida custom
	@echo   make seed API_BASE_URL=url        api_base_url em network.json
	@echo   make seed CLASSIFIER=gru          classifier.json math ou gru
	@echo   make seed ALSO_SERVICE_DATA=1     tambem grava em bootstrap/fall data/
	@echo   make publish-frame                POST JPEG assinado em /devices/.../frame
	@echo   make convert INPUT=video.avi      AVI para MP4 saida mesmo nome .mp4
	@echo   make convert INPUT=v.avi OUTPUT=o.mp4
	@echo   make convert INPUT=v.avi COPY=1   remux sem reencodar
	@echo   make test                         testes de seed_local_edge
	@echo Configuracao opcional: .env nesta pasta VIGIA_API_BASE_URL etc.
	@echo Windows: HOST_PYTHON=py ou python. macOS/Linux: python3.

deps:
	@$(HOST_PYTHON) -m pip install -r requirements.txt

seed:
	$(call require_file,seed_local_edge.py,seed_local_edge.py nao encontrado.)
	@$(HOST_PYTHON) seed_local_edge.py $(if $(DATA_DIR),--data-dir "$(DATA_DIR)",) $(if $(API_BASE_URL),--api-base-url "$(API_BASE_URL)",) $(if $(FIWARE_API_KEY),--fiware-api-key "$(FIWARE_API_KEY)",) $(if $(STREAM_INGEST_URL),--stream-ingest-url "$(STREAM_INGEST_URL)",) $(if $(CLASSIFIER),--classifier "$(CLASSIFIER)",) $(if $(ALSO_SERVICE_DATA),--also-service-data,)

publish-frame:
	$(call require_file,publish_frame.py,publish_frame.py nao encontrado.)
	@$(HOST_PYTHON) publish_frame.py

convert:
	$(call require_var,$(INPUT),Defina INPUT=caminho/video.avi)
	$(call require_file,video_converter.py,video_converter.py nao encontrado.)
	@$(HOST_PYTHON) video_converter.py "$(INPUT)" $(if $(OUTPUT),-o "$(OUTPUT)",) $(if $(COPY),--copy,)

test:
	$(call require_file,test_seed_local_edge.py,test_seed_local_edge.py nao encontrado.)
	@$(HOST_PYTHON) test_seed_local_edge.py
