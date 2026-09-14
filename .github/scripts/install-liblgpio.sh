#!/usr/bin/env bash
# Instala liblgpio (joan2937/lg) em /usr/local — requisito do pip `lgpio`.
# Compila em /tmp (não no workspace) e só instala headers/.so (sem setup.py).
# Popula ~/.cache/vigia-liblgpio-${LG_VERSION} para reuso entre runs do Actions.
set -euo pipefail

LG_VERSION="${LG_VERSION:-0.2.2}"
CACHE_DIR="${HOME}/.cache/vigia-liblgpio-${LG_VERSION}"
PREFIX="/usr/local"

install_from_prefix() {
  local src="$1"
  sudo install -d "${PREFIX}/include" "${PREFIX}/lib"
  sudo install -m 0644 "${src}/include/lgpio.h" "${PREFIX}/include/lgpio.h"
  sudo install -m 0755 "${src}/lib/liblgpio.so.1" "${PREFIX}/lib/liblgpio.so.1"
  sudo ln -sfn liblgpio.so.1 "${PREFIX}/lib/liblgpio.so"
  sudo ldconfig
}

if [[ -f "${CACHE_DIR}/lib/liblgpio.so.1" && -f "${CACHE_DIR}/include/lgpio.h" ]]; then
  echo "liblgpio ${LG_VERSION}: restaurando do cache (${CACHE_DIR})"
  install_from_prefix "${CACHE_DIR}"
  exit 0
fi

echo "liblgpio ${LG_VERSION}: compilando (cache miss)"
WORKDIR="$(mktemp -d /tmp/lg-XXXXXX)"
cleanup() { rm -rf "${WORKDIR}"; }
trap cleanup EXIT

cd "${WORKDIR}"
wget -q "https://github.com/joan2937/lg/archive/refs/tags/v${LG_VERSION}.tar.gz"
tar -xzf "v${LG_VERSION}.tar.gz"
SRC="${WORKDIR}/lg-${LG_VERSION}"

# Só a lib C — sem `make install` completo (evita setup.py + ficheiros root).
make -C "${SRC}" liblgpio.so

mkdir -p "${CACHE_DIR}/include" "${CACHE_DIR}/lib"
cp "${SRC}/lgpio.h" "${CACHE_DIR}/include/lgpio.h"
cp "${SRC}/liblgpio.so.1" "${CACHE_DIR}/lib/liblgpio.so.1"
ln -sfn liblgpio.so.1 "${CACHE_DIR}/lib/liblgpio.so"

install_from_prefix "${CACHE_DIR}"
echo "liblgpio ${LG_VERSION}: instalado e cacheado em ${CACHE_DIR}"
