#!/usr/bin/env bash
# Valida a estrutura mínima do projeto Flutter/Android antes de releases.
# Uso: validate_structure.sh <service_path>
# Exemplo: validate_structure.sh vigia_ui
set -euo pipefail

SERVICE_PATH="${1:-.}"
ERRORS=0

check_required() {
  local rel_path="$1"
  local full_path="$SERVICE_PATH/$rel_path"
  if [ ! -e "$full_path" ]; then
    echo "::error::Arquivo/diretório obrigatório ausente: $full_path"
    ERRORS=$((ERRORS + 1))
  else
    echo "✓ $rel_path"
  fi
}

check_absent() {
  local rel_path="$1"
  local reason="$2"
  local full_path="$SERVICE_PATH/$rel_path"
  if [ -e "$full_path" ]; then
    echo "::error::Arquivo sensível encontrado no repositório: $full_path"
    echo "  Motivo: $reason"
    ERRORS=$((ERRORS + 1))
  else
    echo "✓ $rel_path (ausente — correto)"
  fi
}

# ─── Estrutura Flutter ────────────────────────────────────────────────────────
echo "==> Estrutura Flutter"
check_required "pubspec.yaml"
check_required "pubspec.lock"
check_required "analysis_options.yaml"
check_required "lib"
check_required "lib/main.dart"
check_required "test"

# ─── Estrutura Android ───────────────────────────────────────────────────────
echo ""
echo "==> Estrutura Android"
check_required "android"
check_required "android/app/src/main/AndroidManifest.xml"
check_required "android/app/src/debug/AndroidManifest.xml"
check_required "android/app/build.gradle.kts"
check_required "android/build.gradle.kts"
check_required "android/settings.gradle.kts"
check_required "android/gradle.properties"
check_required "android/gradle/wrapper/gradle-wrapper.properties"

# ─── Firebase ────────────────────────────────────────────────────────────────
echo ""
echo "==> Firebase"
check_required "firebase.json"
check_required "android/app/google-services.json.example"

# ─── Arquivos sensíveis NÃO devem estar versionados ─────────────────────────
echo ""
echo "==> Arquivos sensíveis (devem estar ausentes)"
check_absent \
  "android/app/google-services.json" \
  "Contém chaves de API do Firebase — deve estar no .gitignore e ser injetado via secret em CI"
check_absent \
  "ios/Runner/GoogleService-Info.plist" \
  "Contém chaves de API do Firebase para iOS — deve estar no .gitignore"

# ─── Resultado ───────────────────────────────────────────────────────────────
echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "::error::$ERRORS problema(s) encontrado(s) na estrutura do projeto."
  exit 1
fi
echo "✓ Estrutura do projeto validada com sucesso."
