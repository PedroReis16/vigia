#!/bin/bash
# Garante o usuário admin do realm vigia (client vigia-web) e liga os eventos
# que sincronizam esse usuário na API. --import-realm ignora o realm quando
# ele já existe.
set -eu

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080/auth}"
ADMIN_USER="${KC_BOOTSTRAP_ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${KC_BOOTSTRAP_ADMIN_PASSWORD:-admin}"
REALM="${KEYCLOAK_REALM:-vigia}"

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

i=0
until /opt/keycloak/bin/kcadm.sh update events/config -r "$REALM" \
  -s eventsEnabled=true \
  -s adminEventsEnabled=true \
  -s 'eventsListeners=["jboss-logging","vigia-webhook"]' \
  -s 'enabledEventTypes=["REGISTER","LOGIN","UPDATE_PROFILE","UPDATE_EMAIL","DELETE_ACCOUNT"]'
do
  i=$((i + 1))
  if [ "$i" -gt 20 ]; then
    echo "Não foi possível ligar os eventos no realm $REALM" >&2
    exit 1
  fi
  sleep 3
done

cat > /tmp/vigia-admin-user.json <<'EOF'
{
  "ifResourceExists": "SKIP",
  "users": [
    {
      "id": "05ae0d5a-5ef8-44c4-a6de-df0725cdd39b",
      "username": "admin",
      "enabled": true,
      "emailVerified": true,
      "firstName": "Super",
      "lastName": "Admin",
      "email": "admin@vigia.local",
      "attributes": {
        "phone": ["11999999999"]
      },
      "credentials": [
        {
          "type": "password",
          "value": "admin",
          "temporary": false
        }
      ],
      "realmRoles": ["default-roles-vigia"],
      "clientRoles": {
        "realm-management": ["realm-admin"]
      }
    }
  ]
}
EOF

i=0
until /opt/keycloak/bin/kcadm.sh create partialImport -r "$REALM" -f /tmp/vigia-admin-user.json
do
  i=$((i + 1))
  if [ "$i" -gt 20 ]; then
    echo "Não foi possível garantir o usuário admin no realm $REALM" >&2
    exit 1
  fi
  sleep 3
done

echo "Usuário admin garantido no realm $REALM"
