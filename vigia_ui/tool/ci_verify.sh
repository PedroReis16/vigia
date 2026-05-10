#!/usr/bin/env bash
# Validação local alinhada ao job project_quality do CI (.github/workflows/continuos-integration.yml).
# Requer Flutter/Dart no PATH (mesma linha que `flutter doctor`).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dart format --output=none --set-exit-if-changed lib test
flutter analyze --fatal-warnings
flutter test
