# =============================================================================
# Makefile — vigia-onboard-test
# Targets:
#   make run         Compila (se preciso) e executa o binário
#   make build       Compila (Conan+CMake na 1ª vez)
#   make configure   Força Conan + CMake
#   make clean       Remove pasta build/
# =============================================================================

# Chocolatey make aponta SHELL=sh.exe, mas sh nao esta no PATH; usa Git Bash.
ifeq ($(OS),Windows_NT)
  SHELL := C:/Program Files/Git/bin/bash.exe
  .SHELLFLAGS := -c
endif

APP_NAME   := vigia-capture-cpp
BUILD_DIR  := build
CONFIG     ?= Debug
PROFILE    := $(if $(filter Release,$(CONFIG)),windows-msvc-release,windows-msvc-debug)

EXE            := $(BUILD_DIR)/$(CONFIG)/$(APP_NAME).exe
TOOLCHAIN_FILE := $(BUILD_DIR)/conan_toolchain.cmake

POWERSHELL ?= powershell.exe
CONAN      := "$(POWERSHELL)" -NoProfile -ExecutionPolicy Bypass -File scripts/conan.ps1

.PHONY: help all deps configure build run env clean

.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  make run         Compila (se preciso) e executa $(EXE)"
	@echo "  make build       Compila ($(CONFIG)); Conan+CMake se ainda nao configurou"
	@echo "  make configure   Forca Conan + CMake"
	@echo "  make deps        So Conan install"
	@echo "  make env         Copia example.env -> .env se faltar"
	@echo "  make clean       Remove $(BUILD_DIR)/"
	@echo ""
	@echo "Variaveis: CONFIG=Debug|Release  (atual: $(CONFIG))"

all: build

deps:
	$(CONAN) install . -of $(BUILD_DIR) --build=missing \
		--profile:host=profiles/$(PROFILE) \
		--profile:build=profiles/$(PROFILE)

configure: deps
	cmake -B $(BUILD_DIR) -S . \
		-DCMAKE_TOOLCHAIN_FILE=$(TOOLCHAIN_FILE) \
		-DCMAKE_POLICY_DEFAULT_CMP0091=NEW \
		-DCMAKE_BUILD_TYPE=$(CONFIG)

build:
	@if [ ! -f "$(TOOLCHAIN_FILE)" ]; then \
		$(MAKE) configure; \
	fi
	cmake --build $(BUILD_DIR) --config $(CONFIG)

env:
	@if [ ! -f .env ]; then cp example.env .env; echo "Criado .env a partir de example.env"; fi

run: build env
	./$(EXE)

clean:
	rm -rf $(BUILD_DIR)
	@echo "Artefatos removidos: $(BUILD_DIR)/"
