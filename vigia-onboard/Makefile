# =============================================================================
# Makefile — vigia-onboard
# Único ponto de entrada. O .env da raiz é partilhado; cada projeto tem a sua
# inicialização (Python: venv + src/bootstrap.py; Go: go mod).
#
# Portátil: GNU Make nativo no Windows (cmd.exe) e make no macOS/Linux (sh).
# Receitas só usam o subconjunto comum (cd, &&, echo). Checagens e .env
# ficam em funções Make — sem `command`, `test` ou `{ … }` POSIX.
#
#   make capture                  # setup + loop de captura
#   make capture SETUP_ONLY=1     # só venv/deps/modelo
#   make integration              # setup + serviço Go
#   make integration SETUP_ONLY=1 # só go mod tidy
#   make bootstrap                # setup + serviço Go
#   make bootstrap SETUP_ONLY=1   # só go mod tidy
#   make run                      # todos os projetos em paralelo
# =============================================================================

# python3 no macOS é muitas vezes o 3.9 do Xcode; o capture precisa de >= 3.12.
# No Windows o Make 32-bit corre cmd.exe: `command -v` falha. Usar `python`/`go`.
ifeq ($(OS),Windows_NT)
HOST_PYTHON ?= py
else
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
endif

PROJECTS := capture

# `.env` em KEY=VALUE (veja .env.example). Só estas chaves vão para o ambiente
# das receitas — `export` sozinho exporta também require_* e o $(error) dispara
# com mensagem vazia (`Makefile:38: *** .  Stop.`) assim que o .env existe.
ONBOARD_ENV_KEYS := CAPTURE_SOURCE SHOW_VIDEO SHOW_YOLO_PLOT CAPTURE_LOOP YOLO_MODEL YOLO_IMGSZ SHOW_PLOT BLUR_VIDEO
ifneq ($(wildcard $(CURDIR)/.env),)
include $(CURDIR)/.env
export $(ONBOARD_ENV_KEYS)
endif

# Checagens sem `test` POSIX (Make avalia $(wildcard) nos dois SO).
require_dir  = $(if $(wildcard $(1)/.),,$(error Projeto '$(1)' não encontrado.))
require_file = $(if $(wildcard $(1)),,$(error $(2)))
unexport require_dir require_file

.PHONY: help run $(PROJECTS)

help:
	@echo Uso: make projeto
	@echo Inicializa o ambiente e executa o projeto.
	@echo   make capture                  setup + loop de captura
	@echo   make capture SETUP_ONLY=1     só venv/deps/modelo
	@echo   make run                      todos os projetos em paralelo
	@echo Configuração: .env nesta pasta (veja .env.example).
	@echo Windows: HOST_PYTHON=py (ou python). macOS: python3.12+.
	@echo Projetos: $(PROJECTS)

run:
	$(MAKE) -j$(words $(PROJECTS)) $(PROJECTS)

# O Ultralytics AutoUpdate chama `pip` ao exportar ONNX/CoreML. O bootstrap
# coloca bin/ (Unix) ou Scripts/ (Windows) do venv no PATH.
capture:
	$(call require_dir,$@)
	$(call require_file,$@/src/bootstrap.py,'$@' ainda não tem src/bootstrap.py.)
	@cd $@ && $(HOST_PYTHON) -m src.bootstrap $(if $(SETUP_ONLY),--setup-only,)
