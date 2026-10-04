#!/bin/sh
# Liga eventos no realm master, registra o listener vigia-webhook e declara o atributo phone.
# Rode no host, com o container no ar.
set -eu

CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

docker exec "$CONTAINER" /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080/auth \
  --realm master \
  --user "$ADMIN_USER" \
  --password "$ADMIN_PASSWORD"

docker exec "$CONTAINER" /opt/keycloak/bin/kcadm.sh update events/config -r master \
  -s eventsEnabled=true \
  -s adminEventsEnabled=true \
  -s 'eventsListeners=["jboss-logging","vigia-webhook"]'

docker cp "$SCRIPT_DIR/user-profile.json" "$CONTAINER":/tmp/vigia-user-profile.json
docker exec "$CONTAINER" /opt/keycloak/bin/kcadm.sh update users/profile -r master \
  -f /tmp/vigia-user-profile.json
