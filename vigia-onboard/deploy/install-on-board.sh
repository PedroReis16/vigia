#!/usr/bin/env bash
# Entrada única na placa: instala o serviço Vigia e remove o pacote temporário.
# Uso (após extrair o zip em /tmp):
#   sudo ./install-on-board.sh
# Ou:
#   unzip -o vigia-onboard-deploy.zip -d /tmp/vigia-onboard-deploy
#   sudo /tmp/vigia-onboard-deploy/install-on-board.sh
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root (sudo)." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAR="${ROOT}/vigia-onboard-linux-arm64.tar.gz"
INSTALLER="${ROOT}/install.sh"

if [[ ! -f "${TAR}" ]]; then
  echo "ERRO: ${TAR} não encontrado." >&2
  exit 1
fi
if [[ ! -f "${INSTALLER}" ]]; then
  echo "ERRO: ${INSTALLER} não encontrado." >&2
  exit 1
fi

chmod +x "${INSTALLER}" \
  "${ROOT}/uninstall.sh" \
  "${ROOT}/vigia_reset_config.sh" \
  "${ROOT}/vigia_reset_wifi.sh" 2>/dev/null || true

echo "→ Instalando o serviço Vigia a partir do pacote deploy..."
bash "${INSTALLER}" "${TAR}"

PARENT="$(dirname "${ROOT}")"
for zip in \
  "${PARENT}/vigia-onboard-deploy.zip" \
  "/tmp/vigia-onboard-deploy.zip" \
  "${HOME}/vigia-onboard-deploy.zip"
do
  if [[ -f "${zip}" ]]; then
    echo "→ Removendo ${zip}"
    rm -f "${zip}"
  fi
done

echo "→ Removendo pasta temporária ${ROOT}"
rm -rf "${ROOT}"

echo ""
echo "✅ Deploy concluído. Pacote temporário removido."
echo "   Status: systemctl status vigia.service"
