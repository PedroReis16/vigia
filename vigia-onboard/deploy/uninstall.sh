#!/usr/bin/env bash
# Remove o serviço Vigia (unit, binário, scripts e pacotes apt que o install.sh adicionou).
# Uso (na placa, como root):
#   sudo vigia-uninstall
#   sudo vigia-uninstall --purge-data   # também apaga identity/network/classifier/.env e o OTA
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
      echo "  --purge-data  remove identity.json, network.json, classifier.json,"
      echo "                /opt/vigia/.env e /var/lib/vigia/ota"
      exit 0
      ;;
    *)
      echo "Opção desconhecida: ${arg}" >&2
      exit 1
      ;;
  esac
done

INSTALL_ROOT="/opt/vigia"
BUNDLE_DIR="${INSTALL_ROOT}/onboard"
STATE_DIR="/var/lib/vigia-onboard"
APT_MARK="${STATE_DIR}/apt-packages.txt"

echo "→ A cancelar restart OTA pendente (se existir)..."
systemctl stop vigia-ota-restart.timer vigia-ota-restart.service 2>/dev/null || true

echo "→ A parar e desactivar vigia.service..."
systemctl stop vigia.service 2>/dev/null || true
systemctl disable vigia.service 2>/dev/null || true
rm -f /etc/systemd/system/vigia.service
systemctl daemon-reload
systemctl reset-failed vigia.service 2>/dev/null || true

echo "→ A remover binário e scripts..."
rm -rf "${BUNDLE_DIR}"
rm -f /usr/local/bin/vigia_reset_config.sh
rm -f /usr/local/bin/vigia_reset_wifi.sh
rm -f /usr/local/bin/vigia-uninstall

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
  rm -f "${INSTALL_ROOT}/classifier.json"
  rm -rf /var/lib/vigia/ota
fi

echo ""
echo "✅ Serviço Vigia removido."
echo "   I2C permanece activo (outros serviços podem usá-lo)."
if [[ "${PURGE_DATA}" -eq 0 ]]; then
  echo "   Dados em ${INSTALL_ROOT} mantidos (use --purge-data para apagar)."
fi
