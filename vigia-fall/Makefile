# =============================================================================
# Makefile — vigia-fall-detection
# Targets:
#   make ensure-model       Baixa yolo26s-pose.pt se ausente
#   make build-linux-arm64  Linux ARM64: nativo se host for linux/arm64,
#                           senão Docker (buildx / emulação)
#   make package-ota        Empacota OTA (manifest + scripts + tarball)
#   make clean              Remove artefatos gerados
# =============================================================================

APP_NAME    := vigia-fall-detection
VERSION     := $(or $(VERSION),$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev"))
VERSION_TAG := $(shell echo "$(VERSION)" | tr '@/ ' '---')

IMAGE_ARM64 := $(APP_NAME):linux-arm64-$(VERSION_TAG)
OUT_DIR     := dist/$(APP_NAME)-linux-arm64
OUT_TAR     := dist/$(APP_NAME)-linux-arm64.tar.gz
OUT_DEPLOY  := dist/$(APP_NAME)-deploy.zip
DIST_BUNDLE := dist/$(APP_NAME)
OTA_STAGING := dist/ota-staging
OTA_TAR     := dist/vigia-fall-ota-$(VERSION).tar.gz

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

.PHONY: help ensure-model install-local-deps install-build-deps build build-linux-arm64 \
	build-linux-arm64-native build-linux-arm64-docker package-linux-arm64 package-deploy \
	package-ota clean

help:
	@echo "Targets:"
	@echo "  ensure-model       Garante yolo26s-pose.pt na raiz do projeto"
	@echo "  install-local-deps Venv local: runtime + OpenCV GUI (SHOW_VIDEO)"
	@echo "  install-build-deps Build nativo Linux: torch CPU + OpenCV headless"
	@echo "  build              PyInstaller no SO atual -> $(DIST_BUNDLE)"
	@echo "  build-linux-arm64  Linux ARM64 -> $(OUT_DIR)/, $(OUT_TAR) e $(OUT_DEPLOY)"
	@echo "                     (nativo em linux/arm64; Docker nos demais hosts)"
	@echo "  package-deploy     Zip único para scp -> $(OUT_DEPLOY)"
	@echo "  package-ota        Pacote OTA -> $(OTA_TAR) (requer $(OUT_TAR))"
	@echo "  clean              Remove artefatos gerados"
	@echo ""
	@echo "Host: $(HOST_OS)/$(HOST_ARCH) — native linux/arm64: $(NATIVE_LINUX_ARM64)"

ensure-model:
	@$(PYTHON) scripts/ensure_yolo_model.py

# Dev local: OpenCV com HighGUI. Remove headless se ficou de um build anterior.
install-local-deps:
	$(PIP) install --upgrade pip
	-$(PIP) uninstall -y opencv-python-headless
	$(PIP) install -r requirements-debug.txt
	$(PIP) install --force-reinstall "opencv-python>=4.6.0,<5"

# Espelha a sequência do Dockerfile.linux-arm64-binary (torch CPU + headless OpenCV).
# Só para build nativo na placa/CI — não usar no Mac para correr main.py.
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
	@echo "   ssh usuario@<ip> 'cd /tmp && unzip -o vigia-fall-detection-deploy.zip -d vigia-fall-detection-deploy && sudo ./vigia-fall-detection-deploy/install-on-board.sh'"

# Zip único para instalação manual (mesmo padrão do bootstrap).
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
		deploy/fall-detection.service \
		dist/.deploy-staging/
	@chmod +x dist/.deploy-staging/install-on-board.sh \
		dist/.deploy-staging/install.sh \
		dist/.deploy-staging/uninstall.sh
	@cd dist/.deploy-staging && zip -q -r ../$(APP_NAME)-deploy.zip .
	@rm -rf dist/.deploy-staging
	@echo "✅ Pacote deploy: $(OUT_DEPLOY)"

# Empacota OTA: manifest + scripts + unit + tarball interno.
# Requer $(OUT_TAR) (rode make build-linux-arm64 antes).
package-ota:
	@if [ ! -f "$(OUT_TAR)" ]; then \
		echo "ERRO: $(OUT_TAR) não encontrado. Rode make build-linux-arm64 primeiro."; \
		exit 1; \
	fi
	@echo "──────────────────────────────────────────────"
	@echo " Pacote OTA: vigia-fall-ota-$(VERSION)"
	@echo "──────────────────────────────────────────────"
	@rm -rf $(OTA_STAGING)
	@mkdir -p $(OTA_STAGING)
	@cp "$(OUT_TAR)" "$(OTA_STAGING)/$(APP_NAME)-linux-arm64.tar.gz"
	@cp deploy/install.sh deploy/uninstall.sh deploy/fall-detection.service "$(OTA_STAGING)/"
	@chmod +x "$(OTA_STAGING)/install.sh" "$(OTA_STAGING)/uninstall.sh"
	@VERSION='$(VERSION)' APP_NAME='$(APP_NAME)' STAGING='$(OTA_STAGING)' \
		$(PYTHON) -c 'import hashlib, json, os, pathlib; \
inner = pathlib.Path(os.environ["STAGING"]) / (os.environ["APP_NAME"] + "-linux-arm64.tar.gz"); \
data = inner.read_bytes(); \
manifest = {"version": os.environ["VERSION"], "sha256": hashlib.sha256(data).hexdigest(), \
"size": len(data), "app": os.environ["APP_NAME"]}; \
pathlib.Path(os.environ["STAGING"], "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8"); \
print("manifest:", json.dumps(manifest))'
	@tar -czf "$(OTA_TAR)" -C "$(OTA_STAGING)" \
		manifest.json \
		install.sh \
		uninstall.sh \
		fall-detection.service \
		$(APP_NAME)-linux-arm64.tar.gz
	@rm -rf $(OTA_STAGING)
	@echo ""
	@echo "✅ Pacote OTA: $(OTA_TAR)"

# ── Limpeza ───────────────────────────────────────────────────────────────────
clean:
	@rm -rf build dist/
	@docker rmi $(IMAGE_ARM64) 2>/dev/null || true
	@echo "🧹 Artefatos removidos."
