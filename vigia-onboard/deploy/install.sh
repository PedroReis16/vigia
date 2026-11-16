#!/usr/bin/env bash
# Instala o bundle PyInstaller onedir do serviço Vigia (Linux ARM64 / Raspberry Pi OS),
# dependências de sistema (ffmpeg, OpenCV/torch, lgpio, I2C) e activa vigia.service.
# Uso (na placa, como root):
#   sudo ./install.sh /tmp/vigia-onboard-linux-arm64.tar.gz
#
# OTA (chamado pelo próprio serviço): VIGIA_OTA_APPLY=1 substitui o bundle sem
# parar o unit e agenda systemctl restart daqui a 45s, depois do health-check.
set -euo pipefail

TAR="${1:-}"
if [[ -z "${TAR}" || ! -f "${TAR}" ]]; then
  echo "Uso: sudo $0 /caminho/para/vigia-onboard-linux-arm64.tar.gz" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root (sudo)." >&2
  exit 1
fi

OTA_APPLY="${VIGIA_OTA_APPLY:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_SRC="${SCRIPT_DIR}/vigia.service"
RESET_SRC="${SCRIPT_DIR}/vigia_reset_config.sh"
WIFI_RESET_SRC="${SCRIPT_DIR}/vigia_reset_wifi.sh"
UNINSTALL_SRC="${SCRIPT_DIR}/uninstall.sh"
if [[ ! -f "${UNIT_SRC}" ]]; then
  UNIT_SRC="$(dirname "${TAR}")/vigia.service"
fi
if [[ ! -f "${UNIT_SRC}" ]]; then
  echo "ERRO: vigia.service não encontrado junto ao script nem ao tarball." >&2
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
BUNDLE_DIR="${INSTALL_ROOT}/onboard"
EXTRACTED_NAME="vigia-onboard-linux-arm64"
BINARY_NAME="vigia"
STATE_DIR="/var/lib/vigia-onboard"
APT_MARK="${STATE_DIR}/apt-packages.txt"
# Runtime na placa (o binário PyInstaller já traz os módulos Python).
APT_PACKAGES=(ffmpeg libgomp1 libglib2.0-0 libgl1 libsm6 libxext6 liblgpio1 i2c-tools)

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

if [[ "${OTA_APPLY}" != "1" ]]; then
  echo "→ A desactivar serviços antigos (bootstrap / fall-detection), se existirem..."
  systemctl disable --now vigia-bootstrap.service 2>/dev/null || true
  systemctl disable --now fall-detection.service 2>/dev/null || true

  echo "→ Parando serviço Vigia (se existir)..."
  systemctl stop vigia.service 2>/dev/null || true
fi

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
  if ! echo "${info}" | grep -Eqi 'aarch64|ARM aarch64'; then
    echo "ERRO: executável não é ARM64. Este instalador é para Raspberry Pi OS (aarch64)." >&2
    exit 1
  fi
fi

echo "→ Instalando unit systemd vigia.service (Vigia)..."
install -m 644 "${UNIT_SRC}" /etc/systemd/system/vigia.service

if [[ -f "${RESET_SRC}" ]]; then
  echo "→ Instalando vigia_reset_config.sh..."
  install -m 755 "${RESET_SRC}" /usr/local/bin/vigia_reset_config.sh
fi
if [[ -f "${WIFI_RESET_SRC}" ]]; then
  echo "→ Instalando vigia_reset_wifi.sh..."
  install -m 755 "${WIFI_RESET_SRC}" /usr/local/bin/vigia_reset_wifi.sh
fi
if [[ -f "${UNINSTALL_SRC}" ]]; then
  echo "→ Instalando vigia-uninstall..."
  install -m 755 "${UNINSTALL_SRC}" /usr/local/bin/vigia-uninstall
fi

systemctl daemon-reload

if [[ "${OTA_APPLY}" == "1" ]]; then
  echo "→ OTA: bundle substituído sem parar o serviço Vigia."
  systemctl stop vigia-ota-restart.timer vigia-ota-restart.service 2>/dev/null || true
  if command -v systemd-run >/dev/null 2>&1; then
    systemd-run --on-active=45s --timer-property=AccuracySec=1s \
      --unit=vigia-ota-restart --collect \
      systemctl restart vigia.service \
      || echo "   Aviso: não foi possível agendar o restart. Corra: sudo systemctl restart vigia"
  else
    echo "   Aviso: systemd-run em falta. Corra: sudo systemctl restart vigia"
  fi
else
  systemctl enable vigia.service
  systemctl start vigia.service || true
fi

echo ""
echo "✅ Serviço Vigia instalado em ${BUNDLE_DIR}"
echo "   Status : systemctl status vigia.service"
echo "   Logs   : journalctl -u vigia.service -n 80 --no-pager"
echo "   Remover: sudo vigia-uninstall"
echo "   .env   : opcional em ${INSTALL_ROOT}/.env (DATA_DIR, SHOW_VIDEO, DEBUG, WIFI_MOCK, BLE e LCD vêm do unit)"
if [[ ! -e /dev/i2c-1 ]]; then
  echo "   LCD    : reboot uma vez se o I2C acabou de ser activado."
fi
