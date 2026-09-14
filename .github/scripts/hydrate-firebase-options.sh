#!/usr/bin/env bash
# Hidrata vigia_ui/lib/firebase_options.dart a partir do secret (base64) ou do .example.
# Uso:
#   REQUIRE_SECRET=1  — falha se FIREBASE_OPTIONS_DART_BASE64 estiver vazio (build release)
#   sem REQUIRE_SECRET — usa o .example como fallback (analyze/test)
set -euo pipefail

SERVICE_PATH="${SERVICE_PATH:-vigia_ui}"
DEST="${SERVICE_PATH}/lib/firebase_options.dart"
EXAMPLE="${SERVICE_PATH}/lib/firebase_options.dart.example"

if [ -n "${FIREBASE_OPTIONS_DART_BASE64:-}" ]; then
  echo "${FIREBASE_OPTIONS_DART_BASE64}" | base64 -d > "${DEST}"
  if ! grep -q "apiKey:" "${DEST}"; then
    echo "::error::firebase_options.dart hidratado parece inválido (sem apiKey)."
    exit 1
  fi
  if grep -q "YOUR_ANDROID_API_KEY\|YOUR_IOS_API_KEY" "${DEST}"; then
    echo "::error::Secret FIREBASE_OPTIONS_DART_BASE64 ainda contém placeholders."
    exit 1
  fi
  echo "✓ firebase_options.dart hidratado a partir do secret."
  exit 0
fi

if [ "${REQUIRE_SECRET:-0}" = "1" ]; then
  echo "::error::Secret FIREBASE_OPTIONS_DART_BASE64 não configurado."
  exit 1
fi

if [ ! -f "${EXAMPLE}" ]; then
  echo "::error::Nem secret nem ${EXAMPLE} disponíveis."
  exit 1
fi

cp "${EXAMPLE}" "${DEST}"
echo "✓ firebase_options.dart copiado do .example (placeholders — ok para analyze/test)."
