#!/usr/bin/env bash
# Reset de configuração de utilizador na placa (chamado pelo botão longo).
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root." >&2
  exit 1
fi

echo "→ A parar fall-detection (se existir)..."
systemctl stop fall-detection.service 2>/dev/null || true

echo "→ A remover identidade e .env..."
rm -f /opt/vigia/.env
rm -f /opt/vigia/fall-detection/data/identity.json
rm -rf /opt/vigia/fall-detection/data

echo "→ A reiniciar fall-detection (se instalado)..."
systemctl start fall-detection.service 2>/dev/null || true

echo "✅ Configuração de utilizador redefinida."
