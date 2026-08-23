#!/usr/bin/env bash
# Reset de vínculo de utilizador na placa (botão longo Desvincular).
# Mantém identity.json, network.json, .env e perfis Wi‑Fi do NetworkManager
# para permitir parear um novo utilizador na mesma rede/dispositivo.
# Não reinicia o fall: o bootstrap reabre o beacon de pareamento.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root." >&2
  exit 1
fi

DATA_DIR="${DATA_DIR:-/opt/vigia}"

echo "→ A parar fall-detection (se existir)..."
systemctl stop fall-detection.service 2>/dev/null || true

echo "→ A limpar dados locais do fall (mantém identidade e rede)..."
rm -rf "${DATA_DIR}/fall-detection/data"
rm -rf "${DATA_DIR}/DB"
rm -rf "${DATA_DIR}/data"

echo "✅ Vínculo local limpo. Rede e identidade preservadas — o bootstrap deve reabrir o pareamento BLE."
