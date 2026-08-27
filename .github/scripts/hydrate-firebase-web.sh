#!/usr/bin/env bash
# Hidrata config Firebase Web (public/firebase-config.js + environment.prod.ts).
# Uso:
#   REQUIRE_SECRET=1  — falha se FIREBASE_WEB_CONFIG_JSON_BASE64 estiver vazio (release)
#   sem REQUIRE_SECRET — mantém placeholders (analyze/test)
set -euo pipefail

SERVICE_PATH="${SERVICE_PATH:-vigia-web}"
CONFIG_JS="${SERVICE_PATH}/public/firebase-config.js"
ENV_PROD="${SERVICE_PATH}/src/environments/environment.prod.ts"

write_config_js() {
  local api_key="$1"
  local auth_domain="$2"
  local project_id="$3"
  local messaging_sender_id="$4"
  local app_id="$5"

  cat > "${CONFIG_JS}" <<EOF
self.FIREBASE_CONFIG = {
  apiKey: '${api_key}',
  authDomain: '${auth_domain}',
  projectId: '${project_id}',
  messagingSenderId: '${messaging_sender_id}',
  appId: '${app_id}',
};
EOF
}

write_env_prod() {
  local api_key="$1"
  local auth_domain="$2"
  local project_id="$3"
  local messaging_sender_id="$4"
  local app_id="$5"
  local vapid_key="$6"

  python3 - <<PY
from pathlib import Path
import re

path = Path("${ENV_PROD}")
content = path.read_text()
block = f'''  firebase: {{
    apiKey: '${api_key}',
    authDomain: '${auth_domain}',
    projectId: '${project_id}',
    messagingSenderId: '${messaging_sender_id}',
    appId: '${app_id}',
    vapidKey: '${vapid_key}',
  }} satisfies FirebaseEnvironmentConfig,'''

content, count = re.subn(
    r"  firebase: \{[\s\S]*?\} satisfies FirebaseEnvironmentConfig,",
    block,
    content,
    count=1,
)
if count != 1:
    raise SystemExit("Could not patch firebase block in environment.prod.ts")
path.write_text(content)
PY
}

if [ -n "${FIREBASE_WEB_CONFIG_JSON_BASE64:-}" ]; then
  CONFIG_JSON="$(echo "${FIREBASE_WEB_CONFIG_JSON_BASE64}" | base64 -d)"
  API_KEY="$(echo "${CONFIG_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin)['apiKey'])")"
  AUTH_DOMAIN="$(echo "${CONFIG_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin)['authDomain'])")"
  PROJECT_ID="$(echo "${CONFIG_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin)['projectId'])")"
  MESSAGING_SENDER_ID="$(echo "${CONFIG_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin)['messagingSenderId'])")"
  APP_ID="$(echo "${CONFIG_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin)['appId'])")"
  VAPID_KEY="$(echo "${CONFIG_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin)['vapidKey'])")"

  if [[ "${API_KEY}" == YOUR_* || "${VAPID_KEY}" == YOUR_* ]]; then
    echo "::error::Secret FIREBASE_WEB_CONFIG_JSON_BASE64 ainda contém placeholders."
    exit 1
  fi

  write_config_js "${API_KEY}" "${AUTH_DOMAIN}" "${PROJECT_ID}" "${MESSAGING_SENDER_ID}" "${APP_ID}"
  write_env_prod "${API_KEY}" "${AUTH_DOMAIN}" "${PROJECT_ID}" "${MESSAGING_SENDER_ID}" "${APP_ID}" "${VAPID_KEY}"
  echo "✓ Firebase web config hidratado a partir do secret."
  exit 0
fi

if [ "${REQUIRE_SECRET:-0}" = "1" ]; then
  echo "::error::Secret FIREBASE_WEB_CONFIG_JSON_BASE64 não configurado."
  exit 1
fi

echo "✓ Firebase web config mantido com placeholders (ok para analyze/test)."
exit 0
