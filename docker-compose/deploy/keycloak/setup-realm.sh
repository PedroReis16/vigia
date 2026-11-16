#!/bin/bash
# Reaplica a configuração do realm vigia em produção. --import-realm só importa
# o realm quando ele ainda não existe, então tudo que mudou depois passa por aqui.
# Roda como serviço one-shot (keycloak-setup) no docker-compose do deploy.
#
# Equivale aos apply-*.sh do ambiente local, com estas diferenças:
#   - sem SMTP: e-mail desligado e redefinição de senha desligada;
#   - redirects do vigia-web vêm de WEB_REDIRECT_URIS (domínios públicos);
#   - a senha do admin do realm vem de REALM_ADMIN_PASSWORD (nunca "admin").
set -eu

KCADM=/opt/keycloak/bin/kcadm.sh
KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080/auth}"
ADMIN_USER="${KC_BOOTSTRAP_ADMIN_USERNAME:?KC_BOOTSTRAP_ADMIN_USERNAME is required}"
ADMIN_PASSWORD="${KC_BOOTSTRAP_ADMIN_PASSWORD:?KC_BOOTSTRAP_ADMIN_PASSWORD is required}"
REALM="${KEYCLOAK_REALM:-vigia}"
WEB_REDIRECT_URIS="${WEB_REDIRECT_URIS:-[\"https://vigiadeteccoes.com.br/*\",\"https://www.vigiadeteccoes.com.br/*\"]}"
APP_REDIRECT_URI="${APP_REDIRECT_URI:-vigia://auth/callback}"
USER_PROFILE_FILE="${USER_PROFILE_FILE:-/opt/keycloak/setup/user-profile.json}"

retry() {
  local tries=$1
  shift
  local i=0
  until "$@"; do
    i=$((i + 1))
    if [ "$i" -ge "$tries" ]; then
      echo "Falhou após $tries tentativas: $*" >&2
      return 1
    fi
    sleep 3
  done
}

client_uuid() {
  $KCADM get clients -r "$REALM" -q clientId="$1" --fields id --format csv --noquotes |
    while IFS= read -r line; do
      line=${line//$'\r'/}
      if [ -n "$line" ] && [ "$line" != "id" ]; then
        printf '%s\n' "$line"
        break
      fi
    done
}

ensure_audience_mapper() {
  local uuid=$1
  if ! $KCADM get "clients/$uuid/protocol-mappers/models" -r "$REALM" | grep -q 'vigia-api-audience'; then
    $KCADM create "clients/$uuid/protocol-mappers/models" -r "$REALM" \
      -s name=vigia-api-audience \
      -s protocol=openid-connect \
      -s protocolMapper=oidc-audience-mapper \
      -s 'config."included.custom.audience"=vigia-api' \
      -s 'config."access.token.claim"=true' \
      -s 'config."id.token.claim"=false' \
      -s 'config."introspection.token.claim"=true'
  fi
}

echo "Aguardando a Admin API do Keycloak em $KEYCLOAK_URL..."
retry 100 $KCADM config credentials --server "$KEYCLOAK_URL" --realm master \
  --user "$ADMIN_USER" --password "$ADMIN_PASSWORD"

# O import do realm termina depois que a Admin API responde.
retry 40 $KCADM get "realms/$REALM" --fields realm >/dev/null

# ─── Realm: locales, e-mail desligado, sem reset de senha ─────────────────────
cat > /tmp/realm-settings.json <<'EOF'
{
  "internationalizationEnabled": true,
  "supportedLocales": ["en", "pt-BR"],
  "defaultLocale": "pt-BR",
  "verifyEmail": false,
  "resetPasswordAllowed": false,
  "smtpServer": {}
}
EOF
retry 20 $KCADM update "realms/$REALM" --merge -f /tmp/realm-settings.json
retry 20 $KCADM update "authentication/required-actions/VERIFY_EMAIL" -r "$REALM" \
  -s enabled=false -s defaultAction=false
echo "Realm $REALM: locales en/pt-BR, sem SMTP, sem confirmação e sem reset de senha"

# ─── Perfil de usuário (atributo phone) ───────────────────────────────────────
retry 20 $KCADM update users/profile -r "$REALM" -f "$USER_PROFILE_FILE"
echo "Perfil de usuário do realm $REALM atualizado"

# ─── Eventos → listener vigia-webhook (sync de usuários via RabbitMQ) ─────────
retry 20 $KCADM update events/config -r "$REALM" \
  -s eventsEnabled=true \
  -s adminEventsEnabled=true \
  -s 'eventsListeners=["jboss-logging","vigia-webhook"]' \
  -s 'enabledEventTypes=["REGISTER","LOGIN","UPDATE_PROFILE","UPDATE_EMAIL","DELETE_ACCOUNT"]'
echo "Eventos do realm $REALM ligados no vigia-webhook"

# ─── Cliente vigia-web ────────────────────────────────────────────────────────
WEB_UUID="$(client_uuid vigia-web || true)"
[ -n "$WEB_UUID" ] || { echo "Cliente vigia-web não existe no realm $REALM" >&2; exit 1; }
$KCADM update "clients/$WEB_UUID" -r "$REALM" \
  -s "redirectUris=$WEB_REDIRECT_URIS" \
  -s 'webOrigins=["+"]' \
  -s 'publicClient=true' \
  -s 'standardFlowEnabled=true' \
  -s 'implicitFlowEnabled=false' \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s 'attributes."post.logout.redirect.uris"=+'
ensure_audience_mapper "$WEB_UUID"
echo "Cliente vigia-web: redirects $WEB_REDIRECT_URIS"

# ─── Cliente vigia-app (Flutter) ──────────────────────────────────────────────
APP_UUID="$(client_uuid vigia-app || true)"
if [ -z "$APP_UUID" ]; then
  $KCADM create clients -r "$REALM" -s clientId=vigia-app -s publicClient=true
  APP_UUID="$(client_uuid vigia-app)"
fi
$KCADM update "clients/$APP_UUID" -r "$REALM" \
  -s "redirectUris=[\"$APP_REDIRECT_URI\"]" \
  -s 'webOrigins=[]' \
  -s 'publicClient=true' \
  -s 'standardFlowEnabled=true' \
  -s 'implicitFlowEnabled=false' \
  -s 'directAccessGrantsEnabled=false' \
  -s 'serviceAccountsEnabled=false' \
  -s 'consentRequired=false' \
  -s 'fullScopeAllowed=true' \
  -s 'frontchannelLogout=false' \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s "attributes.\"post.logout.redirect.uris\"=$APP_REDIRECT_URI"
ensure_audience_mapper "$APP_UUID"
echo "Cliente vigia-app atualizado"

# ─── Admin do realm vigia (o import traz senha "admin": troca aqui) ───────────
if [ -n "${REALM_ADMIN_PASSWORD:-}" ]; then
  if [ -n "$($KCADM get users -r "$REALM" -q username=admin -q exact=true --fields id --format csv --noquotes | tr -d '\r' | grep -v '^id$' || true)" ]; then
    $KCADM set-password -r "$REALM" --username admin --new-password "$REALM_ADMIN_PASSWORD"
    echo "Senha do admin do realm $REALM definida a partir de REALM_ADMIN_PASSWORD"
  fi
else
  echo "REALM_ADMIN_PASSWORD vazio: senha do admin do realm $REALM não foi alterada" >&2
fi

echo "Setup do realm $REALM concluído"
