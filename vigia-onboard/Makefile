# =============================================================================
# Makefile — vigia-onboard
# Único ponto de entrada. O .env da raiz é partilhado; cada projeto tem o seu
# venv e a sua inicialização (src/bootstrap.py).
#
#   make capture              # setup + loop de captura
#   make capture SETUP_ONLY=1 # só venv/deps/modelo
#   make <projeto>            # quando o diretório existir
# =============================================================================

# python3 no macOS é muitas vezes o 3.9 do Xcode; o capture precisa de >= 3.12.
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
PROJECTS    := capture

.PHONY: help $(PROJECTS)

help:
	@echo "Uso: make <projeto>"
	@echo ""
	@echo "Inicializa o ambiente (venv, deps, modelo) e executa o projeto."
	@echo "Só preparar, sem correr a captura: make capture SETUP_ONLY=1"
	@echo "Configuração: .env nesta pasta (veja .env.example)."
	@echo ""
	@echo "Projetos: $(PROJECTS)"

# O Ultralytics AutoUpdate chama `pip` (não `python -m pip`) ao exportar
# ONNX/CoreML. Sem o bin/ do venv no PATH, o export falha com "pip: command
# not found" mesmo com o interpretador do .venv.
$(PROJECTS):
	@test -d $@ || { echo "Projeto '$@' não encontrado."; exit 1; }
	@test -f $@/src/bootstrap.py || { echo "'$@' ainda não tem src/bootstrap.py."; exit 1; }
	@cd $@ && \
		if [ -d "$(CURDIR)/$@/.venv/bin" ]; then export PATH="$(CURDIR)/$@/.venv/bin:$$PATH"; \
		elif [ -d "$(CURDIR)/$@/.venv/Scripts" ]; then export PATH="$(CURDIR)/$@/.venv/Scripts:$$PATH"; fi; \
		PYTHONPATH=. $(HOST_PYTHON) -m src.bootstrap $(if $(SETUP_ONLY),--setup-only,)
