#!/usr/bin/env bash
# Instala o bundle PyInstaller onedir e ativa fall-detection.service.
# Uso (na placa, como root):
#   sudo ./install.sh /tmp/vigia-fall-detection-linux-arm64.tar.gz
set -euo pipefail

TAR="${1:-}"
if [[ -z "${TAR}" || ! -f "${TAR}" ]]; then
  echo "Uso: sudo $0 /caminho/para/vigia-fall-detection-linux-arm64.tar.gz" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root (sudo)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_SRC="${SCRIPT_DIR}/fall-detection.service"
if [[ ! -f "${UNIT_SRC}" ]]; then
  UNIT_SRC="$(dirname "${TAR}")/fall-detection.service"
fi
if [[ ! -f "${UNIT_SRC}" ]]; then
  echo "ERRO: fall-detection.service não encontrado junto ao script nem ao tarball." >&2
  exit 1
fi

INSTALL_ROOT="/opt/vigia"
BUNDLE_DIR="${INSTALL_ROOT}/fall-detection"
EXTRACTED_NAME="vigia-fall-detection-linux-arm64"
BINARY_NAME="vigia-fall-detection"

echo "→ Parando serviço (se existir)..."
systemctl stop fall-detection.service 2>/dev/null || true

echo "→ Preparando ${INSTALL_ROOT}..."
install -d -m 755 "${INSTALL_ROOT}"
rm -rf "${BUNDLE_DIR}"

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

echo "→ Extraindo ${TAR}..."
tar -xzf "${TAR}" -C "${tmpdir}"

if [[ -d "${tmpdir}/${EXTRACTED_NAME}" ]]; then
  mv "${tmpdir}/${EXTRACTED_NAME}" "${BUNDLE_DIR}"
elif [[ -x "${tmpdir}/${BINARY_NAME}" ]]; then
  # tarball sem pasta intermediária (improvável; aceita onedir na raiz)
  mkdir -p "${BUNDLE_DIR}"
  mv "${tmpdir}"/* "${BUNDLE_DIR}/"
else
  # Um único top-level dir com outro nome
  top=("${tmpdir}"/*)
  if [[ ${#top[@]} -eq 1 && -d "${top[0]}" ]]; then
    mv "${top[0]}" "${BUNDLE_DIR}"
  else
    echo "ERRO: layout do tarball inesperado em ${tmpdir}" >&2
    ls -la "${tmpdir}" >&2 || true
    exit 1
  fi
fi

if [[ ! -x "${BUNDLE_DIR}/${BINARY_NAME}" ]]; then
  if [[ -f "${BUNDLE_DIR}/${BINARY_NAME}" ]]; then
    chmod +x "${BUNDLE_DIR}/${BINARY_NAME}"
  else
    echo "ERRO: binário ${BUNDLE_DIR}/${BINARY_NAME} não encontrado após extração." >&2
    exit 1
  fi
fi

echo "→ Instalando unit systemd..."
install -m 644 "${UNIT_SRC}" /etc/systemd/system/fall-detection.service
systemctl daemon-reload
# enable: o start só sucede depois do bootstrap gravar identity.json e network.json
systemctl enable fall-detection.service
systemctl start fall-detection.service 2>/dev/null || true

echo ""
echo "✅ Instalado em ${BUNDLE_DIR}"
echo "   Status: systemctl status fall-detection.service"
echo "   Logs  : journalctl -u fall-detection.service -n 80 --no-pager"
echo "   .env  : opcional em ${INSTALL_ROOT}/.env (EnvironmentFile=-/opt/vigia/.env)"
