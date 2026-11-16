# =============================================================================
# Makefile — vigia-onboard
# Único ponto de entrada. O .env da raiz é partilhado; o runtime Python
# (venv + deps) vive em shared/runtime.py e cada módulo arranca sozinho.
#
# Portátil: GNU Make nativo no Windows (cmd.exe) e make no macOS/Linux (sh).
# Receitas só usam o subconjunto comum (cd, &&, echo). Checagens e .env
# ficam em funções Make — sem `command`, `test` ou `{ … }` POSIX.
#
#   make capture                  # setup + loop de captura (+ thread core)
#   make capture SETUP_ONLY=1     # só venv/deps/modelo
#   make integration              # setup + processo de integração
#   make integration SETUP_ONLY=1 # só venv/deps
#   make interface                # setup + control plane (BLE, Wi-Fi, LCD, gate)
#   make interface SETUP_ONLY=1   # só venv/deps
#   make run                      # capture + integration + interface em paralelo
#
# Instalador Linux ARM64 (Raspberry Pi OS), serviço único "Vigia":
#   make ensure-model             # export NCNN em capture/models/yolo/
#   make build-linux-arm64        # PyInstaller → dist/vigia-onboard-deploy.zip
#   make package-ota              # tarball OTA (manifest + install.sh + bundle)
# As receitas de build usam shell POSIX. No Windows o Make usa Git Bash
# (no cmd, `mkdir -p` cria uma pasta chamada "-p").
# =============================================================================

# python3 no macOS é muitas vezes o 3.9 do Xcode; o onboard precisa de >= 3.12.
# No Windows o Make 32-bit corre cmd.exe: `command -v` falha. Usar `python`.
ifeq ($(OS),Windows_NT)
HOST_PYTHON ?= py
else
HOST_PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
endif

PROJECTS := capture integration interface

# ── Instalador linux/arm64 (serviço Vigia) ───────────────────────────────────
APP_NAME    := vigia-onboard
BINARY_NAME := vigia
IMAGE_ARM64_PREFIX := $(APP_NAME)
OUT_DIR     := dist/$(APP_NAME)-linux-arm64
OUT_TAR     := dist/$(APP_NAME)-linux-arm64.tar.gz
OUT_DEPLOY  := dist/$(APP_NAME)-deploy.zip
DIST_BUNDLE := dist/$(BINARY_NAME)
OTA_STAGING := dist/ota-staging
DOCKERFILE  := deploy/Dockerfile.linux-arm64-binary
PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip

ifeq ($(OS),Windows_NT)
VERSION := dev
VERSION_TAG := dev
HOST_OS := windows
HOST_ARCH := n/a
NATIVE_LINUX_ARM64 := 0
# Detecção no cmd. Se este Make já corre no Git Bash, não voltar a invocar `if exist`.
ifneq ($(findstring bash,$(SHELL)),)
_HAS_GIT_BASH := yes
_NEED_BASH :=
else
_HAS_GIT_BASH := $(shell if exist "C:\Program Files\Git\bin\bash.exe" echo yes)
_NEED_BASH := $(if $(filter yes,$(_HAS_GIT_BASH)),yes,)
endif
else
VERSION     := $(or $(VERSION),$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev"))
VERSION_TAG := $(shell echo "$(VERSION)" | tr '@/ ' '---')
HOST_OS   := $(shell uname -s | tr '[:upper:]' '[:lower:]')
HOST_ARCH := $(shell uname -m)
# Binário de deploy é Linux aarch64. Mac ARM (Darwin) NÃO conta como nativo.
NATIVE_LINUX_ARM64 := $(shell \
	if [ "$(HOST_OS)" = "linux" ] && { [ "$(HOST_ARCH)" = "aarch64" ] || [ "$(HOST_ARCH)" = "arm64" ]; }; then \
		echo 1; \
	else \
		echo 0; \
	fi)
endif

IMAGE_ARM64 := $(IMAGE_ARM64_PREFIX):linux-arm64-$(VERSION_TAG)
OTA_TAR     := dist/vigia-onboard-ota-$(VERSION).tar.gz

# `.env` em KEY=VALUE (veja .env.example). Só estas chaves vão para o ambiente
# das receitas — `export` sozinho exporta também require_* e o $(error) dispara
# com mensagem vazia (`Makefile:38: *** .  Stop.`) assim que o .env existe.
ONBOARD_ENV_KEYS := CAPTURE_SOURCE SHOW_VIDEO SHOW_YOLO_PLOT CAPTURE_LOOP YOLO_MODEL YOLO_IMGSZ SHOW_PLOT BLUR_VIDEO FRAME_RATE CLASSIFIER SLIDER_WINDOW FALL_SHM_NAME STREAM_CONTROL_SHM_NAME LIVE_SHM_NAME CLIP_SHM_NAME CLIP_WINDOW_S CLIP_MAX_PAYLOAD DATA_DIR VIGIA_OTA_DIR VIGIA_INSTALL_ROOT DEBUG BLE_ENABLED WIFI_MOCK WIFI_MOCK_RESULT LCD_ENABLED MOCK_WIFI_SSID MOCK_WIFI_PASSWORD MOCK_API_BASE_URL MOCK_FIWARE_API_KEY MOCK_STREAM_INGEST_URL
ifneq ($(wildcard $(CURDIR)/.env),)
include $(CURDIR)/.env
export $(ONBOARD_ENV_KEYS)
endif

# Checagens sem `test` POSIX (Make avalia $(wildcard) nos dois SO).
require_dir  = $(if $(wildcard $(1)/.),,$(error Projeto '$(1)' não encontrado.))
require_file = $(if $(wildcard $(1)),,$(error $(2)))
unexport require_dir require_file

.PHONY: help run $(PROJECTS) ensure-model install-build-deps build build-linux-arm64 \
	build-linux-arm64-native build-linux-arm64-docker package-linux-arm64 package-deploy \
	package-ota clean clean-dist

help:
	@echo Uso: make projeto
	@echo Inicializa o ambiente e executa o modulo.
	@echo   make capture                  setup + loop de captura (+ thread core)
	@echo   make capture SETUP_ONLY=1     so venv/deps/modelo
	@echo   make integration              setup + processo de integracao
	@echo   make integration SETUP_ONLY=1 so venv/deps
	@echo   make interface                setup + control plane
	@echo   make interface SETUP_ONLY=1   so venv/deps
	@echo   make run                      capture + integration + interface em paralelo
	@echo Configuracao: .env nesta pasta (veja .env.example).
	@echo Windows: HOST_PYTHON=py (ou python). macOS: python3.12+.
	@echo Projetos: $(PROJECTS)
	@echo Instalador (Linux ARM64 / Raspberry Pi OS, servico Vigia):
	@echo   make ensure-model             export NCNN em capture/models/yolo/
	@echo   make build-linux-arm64        bundle + zip de deploy
	@echo   make package-ota              tarball OTA
	@echo Host: $(HOST_OS)/$(HOST_ARCH) — native linux/arm64: $(NATIVE_LINUX_ARM64)

run:
	$(MAKE) -j$(words $(PROJECTS)) $(PROJECTS)

# O Ultralytics AutoUpdate chama `pip` ao exportar ONNX/CoreML. O runtime
# coloca bin/ (Unix) ou Scripts/ (Windows) do venv no PATH.
$(PROJECTS):
	$(call require_dir,$@)
	$(call require_file,$@/__main__.py,'$@' ainda não tem __main__.py.)
	@$(HOST_PYTHON) -m $@ $(if $(SETUP_ONLY),--setup-only,)

ensure-model:
	@$(PYTHON) scripts/ensure_yolo_model.py

# Espelha a sequência do Dockerfile.linux-arm64-binary (torch CPU + headless OpenCV).
# Só para build nativo na placa/CI — não usar no desktop para correr main.py.
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
	pyinstaller --clean --noconfirm vigia-onboard.spec

build-linux-arm64:
ifeq ($(NATIVE_LINUX_ARM64),1)
	@$(MAKE) build-linux-arm64-native
else ifeq ($(OS)_$(_HAS_GIT_BASH),Windows_NT_)
	@echo ERRO: Git Bash nao encontrado em "C:\Program Files\Git\bin\bash.exe".
	@echo Instale Git for Windows para gerar o bundle Linux ARM64 a partir do Windows.
	@exit 1
else ifeq ($(_NEED_BASH),yes)
	@echo Host $(HOST_OS)/$(HOST_ARCH) nao e linux/arm64 — usando Docker.
	@$(MAKE) $@ SHELL="C:/Program Files/Git/bin/bash.exe" .SHELLFLAGS="-c"
else
	@echo "Host $(HOST_OS)/$(HOST_ARCH) não é linux/arm64 — usando Docker."
	@$(MAKE) build-linux-arm64-docker
endif

build-linux-arm64-native: ensure-model
	@echo "──────────────────────────────────────────────"
	@echo " Build nativo: $(APP_NAME) — Linux ARM64"
	@echo " Host: $(HOST_OS)/$(HOST_ARCH)"
	@echo " Versão: $(VERSION)"
	@echo "──────────────────────────────────────────────"
	@mkdir -p dist;
	pyinstaller --clean --noconfirm vigia-onboard.spec;
	@$(MAKE) package-linux-arm64

build-linux-arm64-docker: ensure-model
	@echo "──────────────────────────────────────────────"
	@echo " Build Docker: $(APP_NAME) — Linux ARM64"
	@echo " Versão: $(VERSION)"
	@echo "──────────────────────────────────────────────"
	@mkdir -p dist;
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
	@rm -rf $(OUT_DIR);
	@cid=$$(docker create $(IMAGE_ARM64)) || exit 1; \
		docker cp $$cid:/vigia $(OUT_DIR) || { docker rm -f $$cid 2>/dev/null; exit 1; }; \
		docker rm -v $$cid
	@$(MAKE) package-linux-arm64 FROM_DOCKER=1

package-linux-arm64:
	@mkdir -p dist;
	@if [ "$(FROM_DOCKER)" != "1" ]; then \
		if [ ! -d "$(DIST_BUNDLE)" ]; then \
			echo "ERRO: $(DIST_BUNDLE) não encontrado após PyInstaller."; \
			exit 1; \
		fi; \
		rm -rf $(OUT_DIR); \
		mv $(DIST_BUNDLE) $(OUT_DIR); \
	fi
	@test -x $(OUT_DIR)/$(BINARY_NAME) || chmod +x $(OUT_DIR)/$(BINARY_NAME)
	@if command -v file >/dev/null 2>&1; then \
		info=$$(file "$(OUT_DIR)/$(BINARY_NAME)"); \
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
	@tar -czf $(OUT_TAR) -C dist $(APP_NAME)-linux-arm64;
	@$(MAKE) package-deploy
	@echo ""
	@echo "Build concluído."
	@echo "   Pasta : $(OUT_DIR)"
	@echo "   Bundle: $(OUT_TAR)"
	@echo "   Deploy: $(OUT_DEPLOY)"
	@echo ""
	@echo "   Para enviar à placa (um único ficheiro):"
	@echo "   scp $(OUT_DEPLOY) usuario@<ip-da-placa>:/tmp/"
	@echo "   ssh usuario@<ip> 'cd /tmp && unzip -o vigia-onboard-deploy.zip -d vigia-onboard-deploy && sudo ./vigia-onboard-deploy/install-on-board.sh'"

package-deploy:
	@test -f "$(OUT_TAR)" || { echo "ERRO: $(OUT_TAR) em falta. Corra make build-linux-arm64 antes."; exit 1; }
	@command -v zip >/dev/null 2>&1 || { echo "ERRO: 'zip' não está instalado."; exit 1; }
	@rm -f $(OUT_DEPLOY);
	@rm -rf dist/.deploy-staging;
	@mkdir -p dist/.deploy-staging;
	@cp $(OUT_TAR) \
		deploy/install-on-board.sh \
		deploy/install.sh \
		deploy/uninstall.sh \
		deploy/vigia.service \
		deploy/vigia_reset_config.sh \
		deploy/vigia_reset_wifi.sh \
		dist/.deploy-staging/;
	@chmod +x dist/.deploy-staging/install-on-board.sh \
		dist/.deploy-staging/install.sh \
		dist/.deploy-staging/uninstall.sh \
		dist/.deploy-staging/vigia_reset_config.sh \
		dist/.deploy-staging/vigia_reset_wifi.sh;
	@cd dist/.deploy-staging && zip -q -r ../$(APP_NAME)-deploy.zip .
	@rm -rf dist/.deploy-staging;
	@echo "Pacote deploy: $(OUT_DEPLOY)"

package-ota:
ifeq ($(_NEED_BASH),yes)
	@$(MAKE) $@ SHELL="C:/Program Files/Git/bin/bash.exe" .SHELLFLAGS="-c"
else
	@if [ ! -f "$(OUT_TAR)" ]; then \
		echo "ERRO: $(OUT_TAR) não encontrado. Rode make build-linux-arm64 primeiro."; \
		exit 1; \
	fi
	@echo "──────────────────────────────────────────────"
	@echo " Pacote OTA: vigia-onboard-ota-$(VERSION)"
	@echo "──────────────────────────────────────────────"
	@rm -rf $(OTA_STAGING);
	@mkdir -p $(OTA_STAGING);
	@cp "$(OUT_TAR)" "$(OTA_STAGING)/$(APP_NAME)-linux-arm64.tar.gz";
	@cp deploy/install.sh deploy/uninstall.sh deploy/vigia.service \
		deploy/vigia_reset_config.sh deploy/vigia_reset_wifi.sh "$(OTA_STAGING)/";
	@chmod +x "$(OTA_STAGING)/install.sh" "$(OTA_STAGING)/uninstall.sh" \
		"$(OTA_STAGING)/vigia_reset_config.sh" "$(OTA_STAGING)/vigia_reset_wifi.sh";
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
		vigia.service \
		vigia_reset_config.sh \
		vigia_reset_wifi.sh \
		$(APP_NAME)-linux-arm64.tar.gz;
	@rm -rf $(OTA_STAGING);
	@echo ""
	@echo "Pacote OTA: $(OTA_TAR)"
endif

clean: clean-dist

clean-dist:
ifeq ($(_NEED_BASH),yes)
	@$(MAKE) $@ SHELL="C:/Program Files/Git/bin/bash.exe" .SHELLFLAGS="-c"
else
	@rm -rf build dist/;
	@docker rmi $(IMAGE_ARM64) 2>/dev/null || true
	@echo "Artefatos de build removidos."
endif
