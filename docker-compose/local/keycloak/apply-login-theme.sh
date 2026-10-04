#!/bin/sh
# Grava loginTheme=vigia no realm master. Rode no host, com o container no ar.
set -eu

CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"

docker exec "$CONTAINER" /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080/auth \
  --realm master \
  --user "$ADMIN_USER" \
  --password "$ADMIN_PASSWORD"

docker exec "$CONTAINER" /opt/keycloak/bin/kcadm.sh update realms/master \
  -s loginTheme=vigia
