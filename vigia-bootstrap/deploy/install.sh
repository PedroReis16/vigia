#!/usr/bin/env bash
# Instala o bundle PyInstaller onedir e ativa vigia-bootstrap.service.
# Uso (na placa, como root):
#   sudo ./install.sh /tmp/vigia-bootstrap-linux-arm64.tar.gz
set -euo pipefail

TAR="${1:-}"
if [[ -z "${TAR}" || ! -f "${TAR}" ]]; then
  echo "Uso: sudo $0 /caminho/para/vigia-bootstrap-linux-arm64.tar.gz" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root (sudo)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_SRC="${SCRIPT_DIR}/vigia-bootstrap.service"
RESET_SRC="${SCRIPT_DIR}/vigia_reset_config.sh"
if [[ ! -f "${UNIT_SRC}" ]]; then
  UNIT_SRC="$(dirname "${TAR}")/vigia-bootstrap.service"
fi
if [[ ! -f "${UNIT_SRC}" ]]; then
  echo "ERRO: vigia-bootstrap.service não encontrado junto ao script nem ao tarball." >&2
  exit 1
fi
if [[ ! -f "${RESET_SRC}" ]]; then
  RESET_SRC="$(dirname "${TAR}")/vigia_reset_config.sh"
fi

INSTALL_ROOT="/opt/vigia"
BUNDLE_DIR="${INSTALL_ROOT}/bootstrap"
EXTRACTED_NAME="vigia-bootstrap-linux-arm64"
BINARY_NAME="vigia-bootstrap"

echo "→ Parando serviço (se existir)..."
systemctl stop vigia-bootstrap.service 2>/dev/null || true

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
  mkdir -p "${BUNDLE_DIR}"
  mv "${tmpdir}"/* "${BUNDLE_DIR}/"
else
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
install -m 644 "${UNIT_SRC}" /etc/systemd/system/vigia-bootstrap.service

if [[ -f "${RESET_SRC}" ]]; then
  echo "→ Instalando vigia_reset_config.sh..."
  install -m 755 "${RESET_SRC}" /usr/local/bin/vigia_reset_config.sh
fi

systemctl daemon-reload
systemctl enable --now vigia-bootstrap.service

echo ""
echo "✅ Instalado em ${BUNDLE_DIR}"
echo "   Status: systemctl status vigia-bootstrap.service"
echo "   Logs  : journalctl -u vigia-bootstrap.service -n 80 --no-pager"
echo "   .env  : opcional em ${INSTALL_ROOT}/.env (EnvironmentFile=-/opt/vigia/.env)"
