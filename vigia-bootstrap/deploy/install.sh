#!/usr/bin/env bash
# Instala o bundle PyInstaller onedir, dependências de sistema (lgpio, i2c)
# e activa vigia-bootstrap.service.
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
WIFI_RESET_SRC="${SCRIPT_DIR}/vigia_reset_wifi.sh"
UNINSTALL_SRC="${SCRIPT_DIR}/uninstall.sh"
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
if [[ ! -f "${WIFI_RESET_SRC}" ]]; then
  WIFI_RESET_SRC="$(dirname "${TAR}")/vigia_reset_wifi.sh"
fi
if [[ ! -f "${UNINSTALL_SRC}" ]]; then
  UNINSTALL_SRC="$(dirname "${TAR}")/uninstall.sh"
fi

INSTALL_ROOT="/opt/vigia"
BUNDLE_DIR="${INSTALL_ROOT}/bootstrap"
EXTRACTED_NAME="vigia-bootstrap-linux-arm64"
BINARY_NAME="vigia-bootstrap"
STATE_DIR="/var/lib/vigia-bootstrap"
APT_MARK="${STATE_DIR}/apt-packages.txt"
# Runtime na placa (não python3-lgpio: o binário PyInstaller já traz o módulo).
APT_PACKAGES=(liblgpio1 i2c-tools)

echo "→ A instalar dependências de sistema (${APT_PACKAGES[*]})..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
newly=()
for pkg in "${APT_PACKAGES[@]}"; do
  if dpkg-query -W -f='${Status}' "${pkg}" 2>/dev/null | grep -q "install ok installed"; then
    echo "   ${pkg} já instalado"
  else
    newly+=("${pkg}")
  fi
done
if [[ ${#newly[@]} -gt 0 ]]; then
  apt-get install -y "${newly[@]}"
fi
install -d -m 755 "${STATE_DIR}"
if [[ ${#newly[@]} -gt 0 ]]; then
  printf '%s\n' "${newly[@]}" > "${APT_MARK}"
else
  : > "${APT_MARK}"
fi

echo "→ A activar I2C (LCD)..."
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_i2c 0 || true
fi
modprobe i2c-dev 2>/dev/null || true
if [[ ! -e /dev/i2c-1 ]]; then
  echo "   Aviso: /dev/i2c-1 ainda não existe. Pode ser preciso reboot após o primeiro enable do I2C."
fi

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

if command -v file >/dev/null 2>&1; then
  info="$(file "${BUNDLE_DIR}/${BINARY_NAME}")"
  echo "→ Binário: ${info}"
  if echo "${info}" | grep -qi 'Mach-O'; then
    echo "ERRO: este executável é macOS (Darwin), não Linux. Gere o tarball com Docker: make build-linux-arm64" >&2
    exit 1
  fi
  if ! echo "${info}" | grep -q 'ELF'; then
    echo "ERRO: executável não é ELF Linux." >&2
    exit 1
  fi
fi

echo "→ Instalando unit systemd..."
install -m 644 "${UNIT_SRC}" /etc/systemd/system/vigia-bootstrap.service

if [[ -f "${RESET_SRC}" ]]; then
  echo "→ Instalando vigia_reset_config.sh..."
  install -m 755 "${RESET_SRC}" /usr/local/bin/vigia_reset_config.sh
fi
if [[ -f "${WIFI_RESET_SRC}" ]]; then
  echo "→ Instalando vigia_reset_wifi.sh..."
  install -m 755 "${WIFI_RESET_SRC}" /usr/local/bin/vigia_reset_wifi.sh
fi
if [[ -f "${UNINSTALL_SRC}" ]]; then
  echo "→ Instalando vigia-bootstrap-uninstall..."
  install -m 755 "${UNINSTALL_SRC}" /usr/local/bin/vigia-bootstrap-uninstall
fi

systemctl daemon-reload
systemctl enable --now vigia-bootstrap.service

echo ""
echo "✅ Instalado em ${BUNDLE_DIR}"
echo "   Status : systemctl status vigia-bootstrap.service"
echo "   Logs   : journalctl -u vigia-bootstrap.service -n 80 --no-pager"
echo "   Remover: sudo vigia-bootstrap-uninstall"
echo "   .env   : opcional em ${INSTALL_ROOT}/.env"
if [[ ! -e /dev/i2c-1 ]]; then
  echo "   LCD    : reboot uma vez se o I2C acabou de ser activado."
fi
