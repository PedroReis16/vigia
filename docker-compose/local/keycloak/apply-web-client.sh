#!/bin/bash
# Reaplica o cliente público vigia-web (redirects, PKCE e audience).
# --import-realm ignora o realm quando ele já existe.
set -eu

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080/auth}"
ADMIN_USER="${KC_BOOTSTRAP_ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${KC_BOOTSTRAP_ADMIN_PASSWORD:-admin}"
REALM="${KEYCLOAK_REALM:-vigia}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-vigia-web}"

i=0
until /opt/keycloak/bin/kcadm.sh config credentials \
  --server "$KEYCLOAK_URL" \
  --realm master \
  --user "$ADMIN_USER" \
  --password "$ADMIN_PASSWORD"
do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "Keycloak admin API não ficou pronta a tempo" >&2
    exit 1
  fi
  sleep 3
done

CLIENT_UUID=""
i=0
until [ -n "$CLIENT_UUID" ]
do
  CLIENT_UUID=$(/opt/keycloak/bin/kcadm.sh get clients -r "$REALM" -q clientId="$CLIENT_ID" --fields id --format csv --noquotes | awk 'NF && $1 != "id" { print $1; exit }')
  if [ -n "$CLIENT_UUID" ]; then
    break
  fi
  i=$((i + 1))
  if [ "$i" -gt 20 ]; then
    echo "Cliente $CLIENT_ID não encontrado no realm $REALM" >&2
    exit 1
  fi
  sleep 3
done

/opt/keycloak/bin/kcadm.sh update "clients/$CLIENT_UUID" -r "$REALM" \
  -s 'redirectUris=["http://localhost:4200/*","http://localhost:81/*","http://localhost/*"]' \
  -s 'webOrigins=["+"]' \
  -s 'publicClient=true' \
  -s 'standardFlowEnabled=true' \
  -s 'implicitFlowEnabled=false' \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s 'attributes."post.logout.redirect.uris"=+'

if ! /opt/keycloak/bin/kcadm.sh get "clients/$CLIENT_UUID/protocol-mappers/models" -r "$REALM" | grep -q 'vigia-api-audience'; then
  /opt/keycloak/bin/kcadm.sh create "clients/$CLIENT_UUID/protocol-mappers/models" -r "$REALM" \
    -s name=vigia-api-audience \
    -s protocol=openid-connect \
    -s protocolMapper=oidc-audience-mapper \
    -s 'config."included.custom.audience"=vigia-api' \
    -s 'config."access.token.claim"=true' \
    -s 'config."id.token.claim"=false' \
    -s 'config."introspection.token.claim"=true'
fi

echo "Cliente $CLIENT_ID atualizado no realm $REALM"
