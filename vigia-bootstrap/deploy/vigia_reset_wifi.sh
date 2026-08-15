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

echo "✅ Rede local limpa. O bootstrap deve reabrir o pareamento BLE."
