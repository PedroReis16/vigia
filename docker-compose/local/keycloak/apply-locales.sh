#!/bin/bash
# Liga inglês e português no realm vigia, com pt-BR como padrão. O compose
# roda este script uma vez, depois que o Keycloak sobe.
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

cat > /tmp/realm-locales.json <<'EOF'
{
  "internationalizationEnabled": true,
  "supportedLocales": ["en", "pt-BR"],
  "defaultLocale": "pt-BR"
}
EOF

i=0
until /opt/keycloak/bin/kcadm.sh update "realms/$REALM" --merge -f /tmp/realm-locales.json
do
  i=$((i + 1))
  if [ "$i" -gt 20 ]; then
    echo "Não foi possível gravar os locales no realm $REALM" >&2
    exit 1
  fi
  sleep 3
done

echo "Locales do realm $REALM: en, pt-BR (padrão pt-BR)"
