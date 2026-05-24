#!/usr/bin/env bash
# Deploy vigia-api on EC2 via docker compose.
# Invoked by .github/workflows/service-release.yml (appleboy/ssh-action).
# Required env: VERSION (SemVer image tag, e.g. 1.0.0)

set -euo pipefail

SERVICE="${SERVICE:-vigia}"
VERSION="${VERSION:?VERSION env var is required}"

read_image_tag() {
  local line=""
  if [ ! -f .env ]; then
    return 0
  fi
  line=$(grep -E '^(VIGIA_API_IMAGE_TAG|IMAGE_TAG)=' .env 2>/dev/null | head -n1 || true)
  if [ -n "$line" ]; then
    echo "$line" | cut -d= -f2-
  fi
}

write_image_tag() {
  local tag="$1"
  if [ -d .env ]; then
    echo "::error::'.env' em $(pwd) é um diretório — remova ou renomeie na VM."
    exit 1
  fi
  if [ ! -f .env ] || [ ! -s .env ]; then
    printf 'VIGIA_API_IMAGE_TAG=%s\n' "$tag" > .env
    return 0
  fi
  if grep -qE '^VIGIA_API_IMAGE_TAG=' .env; then
    sed -i "s|^VIGIA_API_IMAGE_TAG=.*|VIGIA_API_IMAGE_TAG=${tag}|" .env
  elif grep -qE '^IMAGE_TAG=' .env; then
    sed -i "s|^IMAGE_TAG=.*|VIGIA_API_IMAGE_TAG=${tag}|" .env
  else
    printf 'VIGIA_API_IMAGE_TAG=%s\n' "$tag" >> .env
  fi
}

service_is_running() {
  docker compose ps --status running -q "$SERVICE" 2>/dev/null | grep -q .
}

echo "==> Deploy de vigia-api v${VERSION}"
echo "==> Diretório de deploy: $(pwd)"
ls -la docker-compose.y*ml compose.y*ml .env 2>/dev/null || true

COMPOSE_FILE=""
for candidate in docker-compose.yaml docker-compose.yml compose.yaml compose.yml; do
  if [ -f "$candidate" ]; then
    COMPOSE_FILE="$candidate"
    break
  fi
done
if [ -z "$COMPOSE_FILE" ]; then
  echo "::error::Arquivo compose não encontrado em $(pwd)."
  echo "Esperado: docker-compose.yaml (ou .yml / compose.yaml)."
  exit 1
fi
echo "==> Compose: ${COMPOSE_FILE}"

PREV_VERSION="$(read_image_tag || true)"
if [ -z "$PREV_VERSION" ]; then
  echo "==> Versão anterior: <não registrada>"
else
  echo "==> Versão anterior: ${PREV_VERSION}"
fi

write_image_tag "$VERSION"
echo "==> VIGIA_API_IMAGE_TAG -> ${VERSION}"
grep -E '^(VIGIA_API_IMAGE_TAG|IMAGE_TAG|DOCKERHUB_USERNAME)=' .env 2>/dev/null || true

echo "==> Baixando nova imagem..."
docker compose pull "$SERVICE"

echo "==> Subindo nova versão..."
docker compose up -d --remove-orphans "$SERVICE"

echo "==> Aguardando estabilização (15s)..."
sleep 15

if service_is_running; then
  echo "==> Container '${SERVICE}' está running."
else
  echo "::error::Container '${SERVICE}' não está running após o deploy."
  docker compose ps "$SERVICE" || true
  echo "==> Últimas 100 linhas de log:"
  docker compose logs --tail=100 "$SERVICE" || true

  if [ -n "$PREV_VERSION" ] && [ "$PREV_VERSION" != "$VERSION" ]; then
    echo "==> Revertendo para ${PREV_VERSION} ..."
    write_image_tag "$PREV_VERSION"
    docker compose pull "$SERVICE" || true
    docker compose up -d --remove-orphans "$SERVICE"
    sleep 10
    if service_is_running; then
      echo "::warning::Rollback concluído — serviço em v${PREV_VERSION}."
    else
      echo "::warning::Rollback executado, mas o container ainda não está running."
    fi
  else
    echo "::warning::Sem versão anterior registrada — rollback não executado."
  fi
  exit 1
fi

echo "==> Limpando imagens obsoletas..."
docker image prune -f

echo "==> Deploy de vigia-api v${VERSION} concluído com sucesso."
