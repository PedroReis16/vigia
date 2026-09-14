#!/usr/bin/env bash
# Apaga só as credenciais Wi‑Fi (mantém identity.json).
# O bootstrap reabre o beacon BLE.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root." >&2
  exit 1
fi

echo "→ A parar fall-detection (se existir)..."
systemctl stop fall-detection.service 2>/dev/null || true

DATA_DIR="${DATA_DIR:-/opt/vigia}"
echo "→ A remover ${DATA_DIR}/network.json..."
rm -f "${DATA_DIR}/network.json"

if command -v nmcli >/dev/null 2>&1; then
  echo "→ A remover perfis Wi‑Fi do NetworkManager..."
  while IFS=: read -r uuid kind; do
    if [[ "${kind}" == "802-11-wireless" ]]; then
      nmcli connection delete uuid "${uuid}" >/dev/null 2>&1 || true
    fi
  done < <(nmcli -t -f UUID,TYPE connection show 2>/dev/null || true)
fi

echo "✅ Rede local limpa. O bootstrap deve reabrir o pareamento BLE."
