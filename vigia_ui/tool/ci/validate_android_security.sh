#!/usr/bin/env bash
# Valida configurações de segurança Android (AndroidManifest, build.gradle, permissões).
# Uso: validate_android_security.sh <service_path>
# Exemplo: validate_android_security.sh vigia_ui
set -euo pipefail

SERVICE_PATH="${1:-.}"
ERRORS=0
WARNINGS=0

MAIN_MANIFEST="$SERVICE_PATH/android/app/src/main/AndroidManifest.xml"
BUILD_GRADLE="$SERVICE_PATH/android/app/build.gradle.kts"

# ─── AndroidManifest.xml principal ───────────────────────────────────────────
echo "==> AndroidManifest.xml principal"

if [ ! -f "$MAIN_MANIFEST" ]; then
  echo "::error::$MAIN_MANIFEST não encontrado."
  exit 1
fi

# android:debuggable="true" não deve estar no manifest principal de produção
if grep -q 'android:debuggable="true"' "$MAIN_MANIFEST"; then
  echo "::error::AndroidManifest.xml principal contém android:debuggable=\"true\"."
  echo "  Essa flag só é aceitável no manifest de debug (android/app/src/debug/)."
  echo "  Remova-a do manifest principal antes de fazer release."
  ERRORS=$((ERRORS + 1))
else
  echo "✓ android:debuggable não está definido como true no manifest principal."
fi

# android:usesCleartextTraffic="true" é uma má prática para apps de produção
if grep -q 'android:usesCleartextTraffic="true"' "$MAIN_MANIFEST"; then
  echo "::warning::AndroidManifest.xml permite tráfego HTTP não cifrado (usesCleartextTraffic=true)."
  echo "  Firebase/FCM opera exclusivamente via HTTPS. Verifique se essa flag é necessária."
  WARNINGS=$((WARNINGS + 1))
else
  echo "✓ Tráfego cleartext não habilitado no manifest principal."
fi

# android:allowBackup — se não definido, padrão é true (risco de exfiltração em APKs de debug)
if ! grep -q 'android:allowBackup' "$MAIN_MANIFEST"; then
  echo "::warning::android:allowBackup não definido explicitamente (padrão: true)."
  echo "  Considere adicionar android:allowBackup=\"false\" se o app lida com dados sensíveis."
  WARNINGS=$((WARNINGS + 1))
else
  echo "✓ android:allowBackup definido explicitamente."
fi

# ─── Permissões ──────────────────────────────────────────────────────────────
echo ""
echo "==> Permissões Android declaradas"

PERMISSIONS=$(grep -oE 'android:name="android\.permission\.[^"]*"' "$MAIN_MANIFEST" \
  | sed 's/android:name="\([^"]*\)"/\1/' || true)

if [ -z "$PERMISSIONS" ]; then
  echo "  (nenhuma permissão uses-permission declarada)"
else
  echo "$PERMISSIONS" | while IFS= read -r perm; do
    echo "  - $perm"
  done
fi

# Permissões esperadas para este projeto (Firebase Messaging + notificações locais)
KNOWN_SAFE=(
  "android.permission.POST_NOTIFICATIONS"
  "android.permission.RECEIVE_BOOT_COMPLETED"
  "android.permission.VIBRATE"
  "android.permission.INTERNET"
  "android.permission.ACCESS_NETWORK_STATE"
  "android.permission.WAKE_LOCK"
  "android.permission.FOREGROUND_SERVICE"
  "android.permission.FOREGROUND_SERVICE_DATA_SYNC"
  "android.permission.SCHEDULE_EXACT_ALARM"
)

SENSITIVE_PATTERN="(CAMERA|RECORD_AUDIO|READ_CONTACTS|WRITE_CONTACTS|ACCESS_FINE_LOCATION|ACCESS_COARSE_LOCATION|READ_EXTERNAL_STORAGE|WRITE_EXTERNAL_STORAGE|READ_PHONE_STATE|SEND_SMS|RECEIVE_SMS|CALL_PHONE|READ_CALL_LOG|WRITE_CALL_LOG|PROCESS_OUTGOING_CALLS|BODY_SENSORS|READ_CALENDAR|WRITE_CALENDAR)"

if [ -n "$PERMISSIONS" ]; then
  while IFS= read -r perm; do
    IS_KNOWN=false
    for known in "${KNOWN_SAFE[@]}"; do
      if [ "$perm" = "$known" ]; then IS_KNOWN=true; break; fi
    done

    if ! $IS_KNOWN && echo "$perm" | grep -qE "$SENSITIVE_PATTERN"; then
      echo "::warning::Permissão sensível encontrada: $perm"
      echo "  Verifique se é realmente necessária para o funcionamento do app."
      WARNINGS=$((WARNINGS + 1))
    fi
  done <<< "$PERMISSIONS"
fi

# ─── build.gradle.kts ────────────────────────────────────────────────────────
echo ""
echo "==> build.gradle.kts"

if [ ! -f "$BUILD_GRADLE" ]; then
  echo "::error::$BUILD_GRADLE não encontrado."
  ERRORS=$((ERRORS + 1))
else
  # applicationId não deve ser namespace de exemplo
  if grep -q 'applicationId = "com.example' "$BUILD_GRADLE"; then
    echo "::error::applicationId usa namespace de exemplo (com.example.*)."
    echo "  Defina um applicationId único antes de fazer release."
    ERRORS=$((ERRORS + 1))
  else
    APP_ID=$(grep -oE 'applicationId = "[^"]*"' "$BUILD_GRADLE" | sed 's/applicationId = "\([^"]*\)"/\1/' | head -1 || echo "não detectado")
    echo "✓ applicationId: $APP_ID"
  fi

  # Release signing com debug keys é uma pendência conhecida (não bloqueia — é um WARNING)
  if grep -q 'signingConfigs.getByName("debug")' "$BUILD_GRADLE"; then
    echo "::warning::Release build usa debug signing config."
    echo "  Configure signing com chaves de produção antes de distribuir o APK em produção."
    echo "  Referência: android/app/build.gradle.kts — buildTypes.release.signingConfig"
    WARNINGS=$((WARNINGS + 1))
  else
    echo "✓ Release signing config não usa chaves de debug."
  fi

  # CoreLibraryDesugaring habilitado (requerido para Java 17 + minSdk antigo)
  if grep -q 'isCoreLibraryDesugaringEnabled = true' "$BUILD_GRADLE"; then
    echo "✓ CoreLibraryDesugaring habilitado."
  fi
fi

# ─── Resultado ───────────────────────────────────────────────────────────────
echo ""
echo "=== Resultado ==="
echo "Erros críticos : $ERRORS"
echo "Avisos         : $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo "::error::$ERRORS erro(s) crítico(s) encontrado(s). Corrija antes de prosseguir com o release."
  exit 1
fi

if [ "$WARNINGS" -gt 0 ]; then
  echo "✓ Validações Android concluídas com $WARNINGS aviso(s). Revise os ::warning:: acima."
else
  echo "✓ Validações Android concluídas sem erros ou avisos."
fi
