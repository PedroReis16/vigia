# =============================================================================
# Makefile — vigia-fall-detection
# Targets:
#   make ensure-model       Baixa yolo26s-pose.pt se ausente
#   make build-linux-arm64  Linux ARM64: nativo se host for linux/arm64,
#                           senão Docker (buildx / emulação)
#   make clean              Remove artefatos gerados
# =============================================================================

APP_NAME    := vigia-fall-detection
VERSION     := $(or $(VERSION),$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev"))
VERSION_TAG := $(shell echo "$(VERSION)" | tr '@/ ' '---')

IMAGE_ARM64 := $(APP_NAME):linux-arm64-$(VERSION_TAG)
OUT_DIR     := dist/$(APP_NAME)-linux-arm64
OUT_TAR     := dist/$(APP_NAME)-linux-arm64.tar.gz
DIST_BUNDLE := dist/$(APP_NAME)

DOCKERFILE  := deploy/Dockerfile.linux-arm64-binary
PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip

HOST_OS   := $(shell uname -s | tr '[:upper:]' '[:lower:]')
HOST_ARCH := $(shell uname -m)

# Binário de deploy é Linux aarch64. Mac ARM (Darwin) NÃO conta como nativo —
# PyInstaller aí gera macOS, não o bundle da placa.
NATIVE_LINUX_ARM64 := $(shell \
	if [ "$(HOST_OS)" = "linux" ] && { [ "$(HOST_ARCH)" = "aarch64" ] || [ "$(HOST_ARCH)" = "arm64" ]; }; then \
		echo 1; \
	else \
		echo 0; \
	fi)

.PHONY: help ensure-model install-build-deps build build-linux-arm64 \
	build-linux-arm64-native build-linux-arm64-docker package-linux-arm64 clean

help:
	@echo "Targets:"
	@echo "  ensure-model       Garante yolo26s-pose.pt na raiz do projeto"
	@echo "  install-build-deps Instala deps de runtime + PyInstaller (build nativo)"
	@echo "  build              PyInstaller no SO atual -> $(DIST_BUNDLE)"
	@echo "  build-linux-arm64  Linux ARM64 -> $(OUT_DIR)/ e $(OUT_TAR)"
	@echo "                     (nativo em linux/arm64; Docker nos demais hosts)"
	@echo "  clean              Remove artefatos gerados"
	@echo ""
	@echo "Host: $(HOST_OS)/$(HOST_ARCH) — native linux/arm64: $(NATIVE_LINUX_ARM64)"

ensure-model:
	@$(PYTHON) scripts/ensure_yolo_model.py

# Espelha a sequência do Dockerfile.linux-arm64-binary (torch CPU + headless OpenCV).
install-build-deps:
	$(PIP) install --upgrade pip
	$(PIP) install --index-url https://download.pytorch.org/whl/cpu \
		--extra-index-url https://pypi.org/simple \
		"torch>=2.6,<2.12" "torchvision>=0.21,<0.27"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-build.txt
	-$(PIP) uninstall -y opencv-python
	$(PIP) install --force-reinstall "opencv-python-headless==4.12.0.88"

build: ensure-model
	pyinstaller --clean --noconfirm vigia-fall-detection.spec

# ── Dispatch: nativo (linux/arm64) ou Docker ──────────────────────────────────
build-linux-arm64:
ifeq ($(NATIVE_LINUX_ARM64),1)
	@$(MAKE) build-linux-arm64-native
else
	@echo "Host $(HOST_OS)/$(HOST_ARCH) não é linux/arm64 — usando Docker."
	@$(MAKE) build-linux-arm64-docker
endif

# ── Build nativo (CI arm / placa / VM aarch64) ────────────────────────────────
build-linux-arm64-native: ensure-model
	@echo "──────────────────────────────────────────────"
	@echo " Build nativo: $(APP_NAME) — Linux ARM64"
	@echo " Host: $(HOST_OS)/$(HOST_ARCH)"
	@echo " Versão: $(VERSION)"
	@echo "──────────────────────────────────────────────"
	@mkdir -p dist
	pyinstaller --clean --noconfirm vigia-fall-detection.spec
	@$(MAKE) package-linux-arm64

# ── Build via Docker (dev em amd64 / macOS) ───────────────────────────────────
build-linux-arm64-docker: ensure-model
	@echo "──────────────────────────────────────────────"
	@echo " Build Docker: $(APP_NAME) — Linux ARM64"
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

	@$(MAKE) package-linux-arm64 FROM_DOCKER=1

# Empacota onedir -> OUT_DIR + tar.gz.
# No caminho Docker o onedir já está em OUT_DIR; no nativo vem de DIST_BUNDLE.
package-linux-arm64:
	@mkdir -p dist
	@if [ "$(FROM_DOCKER)" != "1" ]; then \
		if [ ! -d "$(DIST_BUNDLE)" ]; then \
			echo "ERRO: $(DIST_BUNDLE) não encontrado após PyInstaller."; \
			exit 1; \
		fi; \
		rm -rf $(OUT_DIR); \
		mv $(DIST_BUNDLE) $(OUT_DIR); \
	fi
	@test -x $(OUT_DIR)/$(APP_NAME) || chmod +x $(OUT_DIR)/$(APP_NAME)
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
