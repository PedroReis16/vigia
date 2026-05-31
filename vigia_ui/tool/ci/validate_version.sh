#!/usr/bin/env bash
# Valida versão, pubspec.yaml e CHANGELOG antes de criar uma release.
# Uso: validate_version.sh <version> <service_path>
# Exemplo: validate_version.sh 1.2.3 vigia_ui
set -euo pipefail

VERSION="${1:?Uso: validate_version.sh <version> <service_path>}"
SERVICE_PATH="${2:-.}"

# ─── 1. Formato semver X.Y.Z ─────────────────────────────────────────────────
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "::error::Formato de versão inválido: '$VERSION'."
  echo "Use semver X.Y.Z sem prefixo (ex: 1.2.3). Não use 'v1.2.3', '1.2.3+4' ou outros formatos."
  exit 1
fi
echo "✓ Formato de versão válido: $VERSION"

# ─── 2. pubspec.yaml contém a versão informada ───────────────────────────────
PUBSPEC="$SERVICE_PATH/pubspec.yaml"
if [ ! -f "$PUBSPEC" ]; then
  echo "::error::Arquivo $PUBSPEC não encontrado."
  exit 1
fi

# Aceita "version: X.Y.Z" ou "version: X.Y.Z+<build_number>"
if ! grep -qE "^version:[[:space:]]*${VERSION}(\+[0-9]+)?[[:space:]]*$" "$PUBSPEC"; then
  CURRENT=$(grep -E "^version:" "$PUBSPEC" | head -1 | sed 's/version:[[:space:]]*//' || echo "(não encontrada)")
  echo "::error::pubspec.yaml não contém version '$VERSION'."
  echo "Versão atual em pubspec.yaml: '$CURRENT'"
  echo "Atualize 'version:' para '$VERSION' ou '$VERSION+<build_number>' antes do release."
  exit 1
fi
echo "✓ pubspec.yaml contém a versão $VERSION"

# ─── 3. CHANGELOG contém a versão informada ──────────────────────────────────
CHANGELOG="$SERVICE_PATH/CHANGELOG.md"
if [ ! -f "$CHANGELOG" ]; then
  echo "::error::Arquivo $CHANGELOG não encontrado."
  echo "Crie o CHANGELOG.md em '$SERVICE_PATH' antes de criar a release."
  exit 1
fi

# Aceita: ## [1.0.0], # [1.0.0], ## **[1.0.0]**, ## **[1.0.0]** — data opcional
if ! grep -qE "^#{1,2}[[:space:]]+\*?\*?\[${VERSION}\]" "$CHANGELOG"; then
  echo "::error::Versão '$VERSION' NÃO encontrada em $CHANGELOG."
  echo "Adicione a seção '## [$VERSION]' ao CHANGELOG antes do release."
  echo ""
  echo "Versões encontradas no CHANGELOG:"
  grep -oE "^#{1,2}[[:space:]]+\*?\*?\[[^]]+\]" "$CHANGELOG" | head -10 || echo "(nenhuma)"
  exit 1
fi
echo "✓ CHANGELOG contém entrada para versão $VERSION"
