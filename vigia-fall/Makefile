# =============================================================================
# Makefile — vigia-fall-detection
# Targets:
#   make ensure-model       Baixa yolo26s-pose.pt se ausente
#   make build-linux-arm64  Compila o binário onedir para Linux ARM64
#   make clean              Remove artefatos gerados
# =============================================================================

APP_NAME    := vigia-fall-detection
VERSION     := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
VERSION_TAG := $(shell echo "$(VERSION)" | tr '@/ ' '---')

IMAGE_ARM64 := $(APP_NAME):linux-arm64-$(VERSION_TAG)
OUT_DIR     := dist/$(APP_NAME)-linux-arm64
OUT_TAR     := dist/$(APP_NAME)-linux-arm64.tar.gz

DOCKERFILE  := deploy/Dockerfile.linux-arm64-binary
PYTHON      ?= python3

.PHONY: help ensure-model build build-linux-arm64 clean

help:
	@echo "Targets:"
	@echo "  ensure-model       Garante yolo26s-pose.pt na raiz do projeto"
	@echo "  build              PyInstaller no SO atual -> dist/$(APP_NAME)"
	@echo "  build-linux-arm64  Linux ARM64 (Docker buildx) -> $(OUT_DIR)/ e $(OUT_TAR)"
	@echo "  clean              Remove artefatos gerados"

ensure-model:
	@$(PYTHON) scripts/ensure_yolo_model.py

build: ensure-model
	pyinstaller --clean --noconfirm vigia-fall-detection.spec

# ── Build Linux ARM64 ─────────────────────────────────────────────────────────
build-linux-arm64: ensure-model
	@echo "──────────────────────────────────────────────"
	@echo " Build: $(APP_NAME) — Linux ARM64"
	@echo " Versão: $(VERSION)"
	@echo "──────────────────────────────────────────────"

	@mkdir -p dist

	@# Compila com buildx quando disponível; fallback para docker build.
	@if docker buildx version >/dev/null 2>&1; then \
		echo "Usando docker buildx"; \
		docker buildx inspect arm64-builder > /dev/null 2>&1 \
			|| docker buildx create --name arm64-builder --use; \
		docker buildx use arm64-builder; \
		docker buildx build \
			--platform linux/arm64 \
			--file $(DOCKERFILE) \
			--tag $(IMAGE_ARM64) \
			--load \
			.; \
	else \
		echo "docker buildx indisponível; usando docker build"; \
		docker build \
			--file $(DOCKERFILE) \
			--tag $(IMAGE_ARM64) \
			.; \
	fi

	@# Extrai o artefato da imagem sem rodar o container
	@rm -rf $(OUT_DIR)
	@cid=$$(docker create $(IMAGE_ARM64)) || exit 1; \
		docker cp $$cid:/vigia-fall-detection $(OUT_DIR) || { docker rm -f $$cid 2>/dev/null; exit 1; }; \
		docker rm -v $$cid

	@chmod +x $(OUT_DIR)/$(APP_NAME)

	@# Empacota em .tar.gz pronto para scp
	@tar -czf $(OUT_TAR) -C dist $(APP_NAME)-linux-arm64

	@echo ""
	@echo "✅ Build concluído!"
	@echo "   Pasta : $(OUT_DIR)"
	@echo "   SCP   : $(OUT_TAR)"
	@echo ""
	@echo "   Para enviar à placa:"
	@echo "   scp $(OUT_TAR) deploy/install.sh deploy/fall-detection.service usuario@<ip-da-placa>:/tmp/"

# ── Limpeza ───────────────────────────────────────────────────────────────────
clean:
	@rm -rf build dist/
	@docker rmi $(IMAGE_ARM64) 2>/dev/null || true
	@echo "🧹 Artefatos removidos."
