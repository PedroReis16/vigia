# =============================================================================
# Makefile — vigia-bootstrap
# Targets:
#   make build-linux-arm64  ARM: PyInstaller nativo (sem Docker).
#                           Hosts não-ARM: Docker (buildx / emulação)
#   make clean              Remove artefatos gerados
# =============================================================================

APP_NAME    := vigia-bootstrap
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

# Docker só entra em arquiteturas que não são ARM (ex.: amd64/x86_64).
# Em ARM (aarch64/arm64) o PyInstaller corre nativo — na placa (Linux) gera
# o bundle da instalação; em macOS ARM gera um binário Darwin (útil para
# testar o empacotamento, não para copiar para a Raspberry Pi).
HOST_IS_ARM := $(shell \
	if [ "$(HOST_ARCH)" = "aarch64" ] || [ "$(HOST_ARCH)" = "arm64" ]; then \
		echo 1; \
	else \
		echo 0; \
	fi)

.PHONY: help install-build-deps build build-linux-arm64 \
	build-linux-arm64-native build-linux-arm64-docker package-linux-arm64 clean

help:
	@echo "Targets:"
	@echo "  install-build-deps Instala deps de runtime + PyInstaller (build nativo)"
	@echo "  build              PyInstaller no SO atual -> $(DIST_BUNDLE)"
	@echo "  build-linux-arm64  ARM64 -> $(OUT_DIR)/ e $(OUT_TAR)"
	@echo "                     (nativo em ARM; Docker só em hosts não-ARM)"
	@echo "  clean              Remove artefatos gerados"
	@echo ""
	@echo "Host: $(HOST_OS)/$(HOST_ARCH) — ARM nativo: $(HOST_IS_ARM)"

install-build-deps:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-build.txt

build:
	$(PYTHON) -m PyInstaller --clean --noconfirm vigia-bootstrap.spec

build-linux-arm64:
ifeq ($(HOST_IS_ARM),1)
	@$(MAKE) build-linux-arm64-native
else
	@echo "Host $(HOST_OS)/$(HOST_ARCH) não é ARM — usando Docker."
	@$(MAKE) build-linux-arm64-docker
endif

build-linux-arm64-native:
	@echo "──────────────────────────────────────────────"
	@echo " Build nativo: $(APP_NAME) — $(HOST_OS)/$(HOST_ARCH) (sem Docker)"
	@echo " Host: $(HOST_OS)/$(HOST_ARCH)"
	@echo " Versão: $(VERSION)"
	@echo "──────────────────────────────────────────────"
	@mkdir -p dist
	$(PYTHON) -m PyInstaller --clean --noconfirm vigia-bootstrap.spec
	@$(MAKE) package-linux-arm64

build-linux-arm64-docker:
	@echo "──────────────────────────────────────────────"
	@echo " Build Docker: $(APP_NAME) — Linux ARM64"
	@echo " Versão: $(VERSION)"
	@echo "──────────────────────────────────────────────"

	@mkdir -p dist

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

	@rm -rf $(OUT_DIR)
	@cid=$$(docker create $(IMAGE_ARM64)) || exit 1; \
		docker cp $$cid:/vigia-bootstrap $(OUT_DIR) || { docker rm -f $$cid 2>/dev/null; exit 1; }; \
		docker rm -v $$cid

	@$(MAKE) package-linux-arm64 FROM_DOCKER=1

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
	@echo "   scp $(OUT_TAR) deploy/install.sh deploy/vigia-bootstrap.service deploy/vigia_reset_config.sh usuario@<ip-da-placa>:/tmp/"

clean:
	@rm -rf build dist/
	@docker rmi $(IMAGE_ARM64) 2>/dev/null || true
	@echo "🧹 Artefatos removidos."
