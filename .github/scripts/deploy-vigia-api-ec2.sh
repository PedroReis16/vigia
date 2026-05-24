#!/usr/bin/env bash
# Deploy vigia-api na EC2 via docker compose.
# Invocado por .github/workflows/service-release.yml (appleboy/ssh-action).
# Requer: VERSION (tag SemVer da imagem, ex.: 1.0.0).

set -euo pipefail

SERVICE="${SERVICE:-vigia}"
VERSION="${VERSION:?VERSION env var is required}"

echo "==> Deploy de vigia-api v${VERSION} em $(pwd)"

if [ ! -f docker-compose.yaml ] && [ ! -f docker-compose.yml ]; then
  echo "::error::docker-compose.yaml não encontrado em $(pwd)."
  exit 1
fi

# A imagem no compose é resolvida via ${VIGIA_API_IMAGE_TAG} no .env,
# então precisamos atualizá-lo antes do pull.
if [ -f .env ] && grep -qE '^VIGIA_API_IMAGE_TAG=' .env; then
  sed -i "s|^VIGIA_API_IMAGE_TAG=.*|VIGIA_API_IMAGE_TAG=${VERSION}|" .env
else
  echo "VIGIA_API_IMAGE_TAG=${VERSION}" >> .env
fi
echo "==> VIGIA_API_IMAGE_TAG -> ${VERSION}"

docker compose pull "$SERVICE"
docker compose up -d --remove-orphans "$SERVICE"

echo "==> Deploy de vigia-api v${VERSION} concluído."
