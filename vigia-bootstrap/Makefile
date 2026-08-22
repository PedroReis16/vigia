# =============================================================================
# Makefile — vigia-bootstrap
# Targets:
#   make build-linux-arm64  Linux ARM64: nativo só em linux/arm64;
#                           Mac e amd64 usam Docker (buildx).
#   make package-deploy     Zip único para SCP na placa
#   make test               Executa pytest
#   make clean              Remove artefatos gerados
# =============================================================================

APP_NAME    := vigia-bootstrap
VERSION     := $(or $(VERSION),$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev"))
VERSION_TAG := $(shell echo "$(VERSION)" | tr '@/ ' '---')

IMAGE_ARM64 := $(APP_NAME):linux-arm64-$(VERSION_TAG)
OUT_DIR     := dist/$(APP_NAME)-linux-arm64
OUT_TAR     := dist/$(APP_NAME)-linux-arm64.tar.gz
OUT_DEPLOY  := dist/$(APP_NAME)-deploy.zip
DIST_BUNDLE := dist/$(APP_NAME)

DOCKERFILE  := deploy/Dockerfile.linux-arm64-binary
PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip

HOST_OS   := $(shell uname -s | tr '[:upper:]' '[:lower:]')
HOST_ARCH := $(shell uname -m)

# Binário de deploy é Linux aarch64. Mac ARM (Darwin) NÃO conta como nativo —
# PyInstaller aí gera macOS (Exec format error na placa).
NATIVE_LINUX_ARM64 := $(shell \
	if [ "$(HOST_OS)" = "linux" ] && { [ "$(HOST_ARCH)" = "aarch64" ] || [ "$(HOST_ARCH)" = "arm64" ]; }; then \
		echo 1; \
	else \
		echo 0; \
	fi)

.PHONY: help install-local-deps install-build-deps build build-linux-arm64 \
	build-linux-arm64-native build-linux-arm64-docker package-linux-arm64 \
	package-deploy test clean

help:
	@echo "Targets:"
	@echo "  install-local-deps Venv local (macOS/desktop): sem lgpio"
	@echo "  install-build-deps Instala deps de runtime + PyInstaller (build nativo Linux)"
	@echo "  build              PyInstaller no SO atual -> $(DIST_BUNDLE)"
	@echo "  build-linux-arm64  Linux ARM64 -> $(OUT_DIR)/ e $(OUT_TAR)"
	@echo "                     (nativo só em linux/arm64; Docker no Mac e amd64)"
	@echo "  package-deploy     Zip único para a placa -> $(OUT_DEPLOY)"
	@echo "  test               Executa pytest"
	@echo "  clean              Remove artefatos gerados"
	@echo ""
	@echo "Host: $(HOST_OS)/$(HOST_ARCH) — native linux/arm64: $(NATIVE_LINUX_ARM64)"

install-local-deps:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-build-deps:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-build.txt

test:
	$(PYTHON) -m pytest

build:
	$(PYTHON) -m PyInstaller --clean --noconfirm vigia-bootstrap.spec

build-linux-arm64:
ifeq ($(NATIVE_LINUX_ARM64),1)
	@$(MAKE) build-linux-arm64-native
else
	@echo "Host $(HOST_OS)/$(HOST_ARCH) não é linux/arm64 — usando Docker."
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
	@if command -v file >/dev/null 2>&1; then \
		info=$$(file "$(OUT_DIR)/$(APP_NAME)"); \
		echo "$$info"; \
		echo "$$info" | grep -q 'ELF' || { \
			echo "ERRO: o executável não é ELF Linux. No Mac use Docker (make build-linux-arm64)."; \
			exit 1; \
		}; \
		echo "$$info" | grep -Eqi 'aarch64|ARM aarch64' || { \
			echo "ERRO: o executável não é ARM64. Não instale este tarball na Raspberry Pi."; \
			exit 1; \
		}; \
	fi
	@tar -czf $(OUT_TAR) -C dist $(APP_NAME)-linux-arm64
	@$(MAKE) package-deploy
	@echo ""
	@echo "✅ Build concluído!"
	@echo "   Pasta : $(OUT_DIR)"
	@echo "   Bundle: $(OUT_TAR)"
	@echo "   Deploy: $(OUT_DEPLOY)"
	@echo ""
	@echo "   Para enviar à placa (um único ficheiro):"
	@echo "   scp $(OUT_DEPLOY) usuario@<ip-da-placa>:/tmp/"
	@echo "   ssh usuario@<ip> 'cd /tmp && unzip -o vigia-bootstrap-deploy.zip -d vigia-bootstrap-deploy && sudo ./vigia-bootstrap-deploy/install-on-board.sh'"

package-deploy:
	@test -f "$(OUT_TAR)" || { echo "ERRO: $(OUT_TAR) em falta. Corra make build-linux-arm64 antes."; exit 1; }
	@command -v zip >/dev/null 2>&1 || { echo "ERRO: 'zip' não está instalado."; exit 1; }
	@rm -f $(OUT_DEPLOY)
	@rm -rf dist/.deploy-staging
	@mkdir -p dist/.deploy-staging
	@cp $(OUT_TAR) \
		deploy/install-on-board.sh \
		deploy/install.sh \
		deploy/uninstall.sh \
		deploy/vigia-bootstrap.service \
		deploy/vigia_reset_config.sh \
		deploy/vigia_reset_wifi.sh \
		dist/.deploy-staging/
	@chmod +x dist/.deploy-staging/install-on-board.sh \
		dist/.deploy-staging/install.sh \
		dist/.deploy-staging/uninstall.sh \
		dist/.deploy-staging/vigia_reset_config.sh \
		dist/.deploy-staging/vigia_reset_wifi.sh
	@cd dist/.deploy-staging && zip -q -r ../$(APP_NAME)-deploy.zip .
	@rm -rf dist/.deploy-staging
	@echo "✅ Pacote deploy: $(OUT_DEPLOY)"

clean:
	@rm -rf build dist/
	@docker rmi $(IMAGE_ARM64) 2>/dev/null || true
	@echo "🧹 Artefatos removidos."
