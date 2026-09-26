# =============================================================================
# Makefile — vigia-onboard
# Único ponto de entrada. O .env da raiz é partilhado; cada projeto tem a sua
# inicialização (Python: venv + src/bootstrap.py; Go: go mod).
#
#   make capture                  # setup + loop de captura
#   make capture SETUP_ONLY=1     # só venv/deps/modelo
#   make integration              # setup + serviço Go
#   make integration SETUP_ONLY=1 # só go mod tidy
#   make bootstrap                # setup + serviço Go
#   make bootstrap SETUP_ONLY=1   # só go mod tidy
# =============================================================================

# python3 no macOS é muitas vezes o 3.9 do Xcode; o capture precisa de >= 3.12.
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
HOST_GO     ?= $(shell command -v go)
PROJECTS    := capture integration bootstrap core

.PHONY: help $(PROJECTS)

help:
	@echo "Uso: make <projeto>"
	@echo ""
	@echo "Inicializa o ambiente e executa o projeto."
	@echo "  make capture                  setup + loop de captura"
	@echo "  make capture SETUP_ONLY=1     só venv/deps/modelo"
	@echo "  make integration              setup + serviço Go"
	@echo "  make integration SETUP_ONLY=1 só go mod tidy"
	@echo "Configuração: .env nesta pasta (veja .env.example)."
	@echo ""
	@echo "Projetos: $(PROJECTS)"

# O Ultralytics AutoUpdate chama `pip` (não `python -m pip`) ao exportar
# ONNX/CoreML. Sem o bin/ do venv no PATH, o export falha com "pip: command
# not found" mesmo com o interpretador do .venv.
capture:
	@test -d $@ || { echo "Projeto '$@' não encontrado."; exit 1; }
	@test -f $@/src/bootstrap.py || { echo "'$@' ainda não tem src/bootstrap.py."; exit 1; }
	@cd $@ && \
		if [ -d "$(CURDIR)/$@/.venv/bin" ]; then export PATH="$(CURDIR)/$@/.venv/bin:$$PATH"; \
		elif [ -d "$(CURDIR)/$@/.venv/Scripts" ]; then export PATH="$(CURDIR)/$@/.venv/Scripts:$$PATH"; fi; \
		PYTHONPATH=. $(HOST_PYTHON) -m src.bootstrap $(if $(SETUP_ONLY),--setup-only,)

integration:
	@test -d $@ || { echo "Projeto '$@' não encontrado."; exit 1; }
	@test -f $@/go.mod || { echo "'$@' ainda não tem go.mod."; exit 1; }
	@command -v "$(HOST_GO)" >/dev/null 2>&1 || { echo "Go não encontrado. Instale Go ou defina HOST_GO."; exit 1; }
	@set -a; [ -f "$(CURDIR)/.env" ] && . "$(CURDIR)/.env"; set +a; \
		cd $@ && $(HOST_GO) mod tidy \
		$(if $(SETUP_ONLY),&& echo "Módulo Go inicializado em $(CURDIR)/$@",&& $(HOST_GO) run ./main.go)

bootstrap:
	@test -d $@ || { echo "Projeto '$@' não encontrado."; exit 1; }
	@test -f $@/main.go || { echo "'$@' ainda não tem main.go."; exit 1; }
	@command -v "$(HOST_GO)" >/dev/null 2>&1 || { echo "Go não encontrado. Instale Go ou defina HOST_GO."; exit 1; }
	@set -a; [ -f "$(CURDIR)/.env" ] && . "$(CURDIR)/.env"; set +a; \
		cd $@ && $(HOST_GO) mod tidy \
		$(if $(SETUP_ONLY),&& echo "Módulo Go inicializado em $(CURDIR)/$@",&& $(HOST_GO) run ./main.go)