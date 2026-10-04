#!/usr/bin/env bash
# Reset de vínculo de utilizador na placa (botão longo Desvincular).
# Mantém identity.json, network.json e .env.
# Não pára o serviço Vigia: o control plane corre no mesmo processo e reabre o pareamento.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root." >&2
  exit 1
fi

DATA_DIR="${DATA_DIR:-/opt/vigia}"

echo "→ A limpar dados locais da captura (mantém identidade e rede)..."
rm -rf "${DATA_DIR}/onboard/data"
rm -rf "${DATA_DIR}/fall-detection/data"
rm -rf "${DATA_DIR}/DB"
rm -rf "${DATA_DIR}/data"

echo "✅ Vínculo local limpo. Rede e identidade preservadas — o serviço Vigia deve reabrir o pareamento BLE."
