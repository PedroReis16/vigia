# =============================================================================
# Makefile — vigia-onboard
# Único ponto de entrada. O .env da raiz é partilhado; cada projeto tem o seu
# venv e a sua inicialização (src/bootstrap.py).
#
#   make capture
#   make <projeto>          # quando o diretório existir
# =============================================================================

# python3 no macOS é muitas vezes o 3.9 do Xcode; o capture precisa de >= 3.12.
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
PROJECTS    := capture

.PHONY: help $(PROJECTS)

help:
	@echo "Uso: make <projeto>"
	@echo ""
	@echo "Inicializa o ambiente específico desse projeto (venv, deps, modelo)."
	@echo "Configuração: .env nesta pasta (veja .env.example)."
	@echo ""
	@echo "Projetos: $(PROJECTS)"

$(PROJECTS):
	@test -d $@ || { echo "Projeto '$@' não encontrado."; exit 1; }
	@test -f $@/src/bootstrap.py || { echo "'$@' ainda não tem src/bootstrap.py."; exit 1; }
	@cd $@ && PYTHONPATH=. $(HOST_PYTHON) -m src.bootstrap
