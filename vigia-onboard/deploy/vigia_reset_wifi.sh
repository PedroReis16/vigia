#!/usr/bin/env bash
# Remove só a secção network de device.json (mantém identidade e opções).
# Também apaga network.json legado, para uma placa ainda não migrada.
# Não pára o serviço Vigia: o control plane reabre o beacon BLE.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root." >&2
  exit 1
fi

DATA_DIR="${DATA_DIR:-/opt/vigia}"
echo "→ A remover a secção network de ${DATA_DIR}/device.json..."
python3 - "$DATA_DIR" <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
path = root / "device.json"
if path.is_file():
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = None
    if isinstance(data, dict) and "network" in data:
        data.pop("network", None)
        tmp = path.with_name(".device-reset.json")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
(root / "network.json").unlink(missing_ok=True)
PY

if command -v nmcli >/dev/null 2>&1; then
  echo "→ A remover perfis Wi-Fi do NetworkManager..."
  while IFS=: read -r uuid kind; do
    if [[ "${kind}" == "802-11-wireless" ]]; then
      nmcli connection delete uuid "${uuid}" >/dev/null 2>&1 || true
    fi
  done < <(nmcli -t -f UUID,TYPE connection show 2>/dev/null || true)
fi

echo "✅ Rede local limpa. O serviço Vigia deve reabrir o pareamento BLE."
