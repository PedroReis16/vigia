# =============================================================================
# Makefile — vigia-onboard
# Único ponto de entrada. O .env da raiz é partilhado; o runtime Python
# (venv + deps) vive em shared/runtime.py e cada módulo arranca sozinho.
#
# Portátil: GNU Make nativo no Windows (cmd.exe) e make no macOS/Linux (sh).
# Receitas só usam o subconjunto comum (cd, &&, echo). Checagens e .env
# ficam em funções Make — sem `command`, `test` ou `{ … }` POSIX.
#
#   make capture                  # setup + loop de captura
#   make capture SETUP_ONLY=1     # só venv/deps/modelo
#   make core                     # setup + processo core
#   make core SETUP_ONLY=1        # só venv/deps
#   make run                      # módulos em paralelo
# =============================================================================

# python3 no macOS é muitas vezes o 3.9 do Xcode; o onboard precisa de >= 3.12.
# No Windows o Make 32-bit corre cmd.exe: `command -v` falha. Usar `python`.
ifeq ($(OS),Windows_NT)
HOST_PYTHON ?= py
else
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
endif

PROJECTS := capture core

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
	@echo Inicializa o ambiente e executa o modulo.
	@echo   make capture                  setup + loop de captura
	@echo   make capture SETUP_ONLY=1     so venv/deps/modelo
	@echo   make core                     setup + processo core
	@echo   make core SETUP_ONLY=1        so venv/deps
	@echo   make run                      todos os modulos em paralelo
	@echo Configuracao: .env nesta pasta (veja .env.example).
	@echo Windows: HOST_PYTHON=py (ou python). macOS: python3.12+.
	@echo Projetos: $(PROJECTS)

run:
	$(MAKE) -j$(words $(PROJECTS)) $(PROJECTS)

# O Ultralytics AutoUpdate chama `pip` ao exportar ONNX/CoreML. O runtime
# coloca bin/ (Unix) ou Scripts/ (Windows) do venv no PATH.
$(PROJECTS):
	$(call require_dir,$@)
	$(call require_file,$@/__main__.py,'$@' ainda não tem __main__.py.)
	@$(HOST_PYTHON) -m $@ $(if $(SETUP_ONLY),--setup-only,)
