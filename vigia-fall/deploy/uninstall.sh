#!/usr/bin/env bash
# Remove vigia-fall-detection (serviço, binário e pacotes apt que o install.sh adicionou).
# Uso (na placa, como root):
#   sudo vigia-fall-detection-uninstall
#   sudo vigia-fall-detection-uninstall --purge-data   # também apaga /opt/vigia/DB
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
      echo "  --purge-data  remove /opt/vigia/DB (SQLite do fall)"
      echo "                identity.json, network.json e .env ficam (são do bootstrap)"
      exit 0
      ;;
    *)
      echo "Opção desconhecida: ${arg}" >&2
      exit 1
      ;;
  esac
done

INSTALL_ROOT="/opt/vigia"
BUNDLE_DIR="${INSTALL_ROOT}/fall-detection"
STATE_DIR="/var/lib/vigia-fall-detection"
APT_MARK="${STATE_DIR}/apt-packages.txt"

echo "→ A parar e desactivar fall-detection.service..."
systemctl stop fall-detection.service 2>/dev/null || true
systemctl disable fall-detection.service 2>/dev/null || true
rm -f /etc/systemd/system/fall-detection.service
systemctl daemon-reload
systemctl reset-failed fall-detection.service 2>/dev/null || true

echo "→ A remover binário e scripts..."
rm -rf "${BUNDLE_DIR}"
rm -f /usr/local/bin/vigia-fall-detection-uninstall

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
  echo "→ A remover dados do fall em ${INSTALL_ROOT}/DB..."
  rm -rf "${INSTALL_ROOT}/DB"
fi

echo ""
echo "✅ vigia-fall-detection removido."
if [[ "${PURGE_DATA}" -eq 0 ]]; then
  echo "   Dados em ${INSTALL_ROOT} mantidos (use --purge-data para apagar o DB)."
  echo "   identity.json / network.json / .env não são tocados (bootstrap)."
fi
