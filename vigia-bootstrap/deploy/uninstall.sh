#!/usr/bin/env bash
# Remove vigia-bootstrap (serviço, binário, scripts e pacotes apt que o install.sh adicionou).
# Uso (na placa, como root):
#   sudo vigia-bootstrap-uninstall
#   sudo vigia-bootstrap-uninstall --purge-data   # também apaga /opt/vigia identity/network/.env
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root (sudo)." >&2
  exit 1
fi

PURGE_DATA=0
for arg in "$@"; do
  case "${arg}" in
    --purge-data) PURGE_DATA=1 ;;
    -h|--help)
      echo "Uso: sudo $0 [--purge-data]"
      echo "  --purge-data  remove identity.json, network.json e /opt/vigia/.env"
      exit 0
      ;;
    *)
      echo "Opção desconhecida: ${arg}" >&2
      exit 1
      ;;
  esac
done

INSTALL_ROOT="/opt/vigia"
BUNDLE_DIR="${INSTALL_ROOT}/bootstrap"
STATE_DIR="/var/lib/vigia-bootstrap"
APT_MARK="${STATE_DIR}/apt-packages.txt"

echo "→ A parar e desactivar vigia-bootstrap.service..."
systemctl stop vigia-bootstrap.service 2>/dev/null || true
systemctl disable vigia-bootstrap.service 2>/dev/null || true
rm -f /etc/systemd/system/vigia-bootstrap.service
systemctl daemon-reload
systemctl reset-failed vigia-bootstrap.service 2>/dev/null || true

echo "→ A remover binário e scripts..."
rm -rf "${BUNDLE_DIR}"
rm -f /usr/local/bin/vigia_reset_config.sh
rm -f /usr/local/bin/vigia_reset_wifi.sh
rm -f /usr/local/bin/vigia-bootstrap-uninstall

if [[ -f "${APT_MARK}" ]]; then
  mapfile -t pkgs < "${APT_MARK}"
  if [[ ${#pkgs[@]} -gt 0 ]]; then
    echo "→ A remover pacotes apt instalados por este pacote: ${pkgs[*]}"
    export DEBIAN_FRONTEND=noninteractive
    apt-get remove -y "${pkgs[@]}" || true
    apt-get autoremove -y || true
  fi
fi
rm -rf "${STATE_DIR}"

if [[ "${PURGE_DATA}" -eq 1 ]]; then
  echo "→ A remover dados de utilizador em ${INSTALL_ROOT}..."
  rm -f "${INSTALL_ROOT}/.env"
  rm -f "${INSTALL_ROOT}/identity.json"
  rm -f "${INSTALL_ROOT}/network.json"
fi

echo ""
echo "✅ vigia-bootstrap removido."
echo "   I2C permanece activo (outros serviços podem usá-lo)."
if [[ "${PURGE_DATA}" -eq 0 ]]; then
  echo "   Dados em ${INSTALL_ROOT} mantidos (use --purge-data para apagar)."
fi
