#!/usr/bin/env bash
# Reset de configuração de utilizador na placa (chamado pelo botão longo).
# Não reinicia o fall: o bootstrap reentra no beacon de pareamento.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root." >&2
  exit 1
fi

echo "→ A parar fall-detection (se existir)..."
systemctl stop fall-detection.service 2>/dev/null || true

echo "→ A remover identidade, rede e dados de utilizador..."
rm -f /opt/vigia/.env
rm -f /opt/vigia/identity.json
rm -f /opt/vigia/network.json
rm -f /opt/vigia/fall-detection/data/identity.json
rm -rf /opt/vigia/fall-detection/data
rm -rf /opt/vigia/data

if command -v nmcli >/dev/null 2>&1; then
  echo "→ A remover perfis Wi‑Fi do NetworkManager..."
  while IFS=: read -r uuid kind; do
    if [[ "${kind}" == "802-11-wireless" ]]; then
      nmcli connection delete uuid "${uuid}" >/dev/null 2>&1 || true
    fi
  done < <(nmcli -t -f UUID,TYPE connection show 2>/dev/null || true)
fi

echo "✅ Configuração de utilizador redefinida. O bootstrap deve reabrir o pareamento BLE."
