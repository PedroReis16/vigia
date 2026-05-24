# vigia_ui

App Flutter do projeto VIGIA — recebe notificações push do Firebase quando o módulo `fall-detection` detecta uma queda.

> **Nota sobre o histórico do repositório**
>
> O arquivo `android/app/google-services.json` esteve versionado nos commits `f7e9897` e `f4c462d` (Mai/2026) com as chaves reais de API. Esses commits foram **removidos do histórico** com `git filter-repo` e o arquivo agora é injetado em tempo de build via GitHub Secrets. Se você clonou o repositório antes da limpeza, faça `git fetch --all --prune` e re-checkout das branches afetadas, ou clone novamente.

---

## Pré-requisitos

| Ferramenta | Versão | Observação |
|---|---|---|
| Flutter SDK | stable | `flutter --version` (canal `stable`) |
| Android SDK / Android Studio | API 34+ | só para builds Android |
| `flutterfire_cli` | última | opcional, simplifica a configuração inicial |

---

## Setup local (necessário para rodar `flutter run`)

O app usa Firebase Cloud Messaging. O plugin Gradle `com.google.gms.google-services` (declarado em `android/app/build.gradle.kts`) **exige** o arquivo `android/app/google-services.json` no build Android. Esse arquivo contém a Android API key do Firebase e por isso **não é versionado** — está listado em `vigia_ui/.gitignore`.

### Opção A — Via `flutterfire configure` (recomendada)

```bash
dart pub global activate flutterfire_cli
cd vigia_ui
flutterfire configure --project=<seu-firebase-project-id>
```

O CLI baixa o `google-services.json` (Android) e o `GoogleService-Info.plist` (iOS) já nos caminhos certos.

### Opção B — Download manual do Firebase Console

1. Acesse o [Firebase Console](https://console.firebase.google.com/) → projeto VIGIA.
2. **Configurações do projeto → Seus apps → Android**.
3. Baixe `google-services.json` e copie para `vigia_ui/android/app/google-services.json`.
4. Para iOS: baixe `GoogleService-Info.plist` e copie para `vigia_ui/ios/Runner/GoogleService-Info.plist`.

O arquivo `android/app/google-services.json.example` mostra a estrutura esperada — útil como referência mas com placeholders no lugar das chaves.

### Validação rápida

```bash
cd vigia_ui
flutter pub get
flutter run                       # roda no dispositivo/emulador conectado
flutter test                      # roda testes unitários e de widget
flutter analyze --fatal-warnings
```

---

## Setup do CI/CD (GitHub Actions)

A pipeline `Vigia UI — Mobile Deploy` (`.github/workflows/mobile-deploy.yml`) hoje **valida, testa e prepara o release** mas não gera o APK final. Quando o job de build de APK for ativado (atualmente templated em `optional_device_farm`), ele vai precisar do `google-services.json` injetado via secret.

### 1. Gerar o conteúdo base64 do `google-services.json`

A partir de um clone local com o arquivo já configurado:

**Linux / macOS:**

```bash
base64 -w 0 vigia_ui/android/app/google-services.json > google-services.b64
cat google-services.b64                # copie esse conteúdo
```

**Windows (PowerShell):**

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("vigia_ui\android\app\google-services.json")) | Set-Clipboard
```

(o conteúdo fica direto no clipboard, pronto para colar)

### 2. Cadastrar o secret no GitHub

1. Repositório → **Settings → Secrets and variables → Actions → New repository secret**.
2. Nome: `GOOGLE_SERVICES_JSON_BASE64`
3. Value: cole o conteúdo do passo 1.
4. (iOS, futuro) repetir com `GOOGLE_SERVICE_INFO_PLIST_BASE64`.

### 3. Hidratação no workflow

Snippet a ser usado no job que compila o APK (já documentado como template no bloco `optional_device_farm` do `mobile-deploy.yml`):

```yaml
- name: Hidratar google-services.json a partir do secret
  env:
    GOOGLE_SERVICES_JSON_BASE64: ${{ secrets.GOOGLE_SERVICES_JSON_BASE64 }}
  run: |
    set -euo pipefail
    if [ -z "${GOOGLE_SERVICES_JSON_BASE64:-}" ]; then
      echo "::error::Secret GOOGLE_SERVICES_JSON_BASE64 não configurado no repositório."
      exit 1
    fi
    echo "$GOOGLE_SERVICES_JSON_BASE64" | base64 -d \
      > "$SERVICE_PATH/android/app/google-services.json"
    jq empty "$SERVICE_PATH/android/app/google-services.json" \
      || { echo "::error::google-services.json hidratado é inválido."; exit 1; }
    echo "✓ google-services.json hidratado e validado."

- name: Limpar google-services.json após o build
  if: always()
  run: rm -f "$SERVICE_PATH/android/app/google-services.json"
```

### Por que NÃO basta versionar mesmo "só a chave de cliente"?

A chave `current_key` no `google-services.json` é uma Android API key do Firebase — é embarcada no APK e, sozinha, não dá acesso direto a dados. **Mas:**

- Sem [restrições de API](https://cloud.google.com/docs/authentication/api-keys#api_key_restrictions) (package name + SHA-1) ela pode ser abusada para gerar custo no seu projeto.
- O Gitleaks (parte do pipeline DevSecOps) corretamente sinaliza esse padrão e bloqueia o build.
- Boas práticas de Google/Firebase recomendam tratá-la como confidencial e usar restrições server-side.

**Checklist obrigatório no Google Cloud Console** (independente de tudo isso):

- [ ] Aplicar **Application restrictions → Android apps** (package name + SHA-1 do certificado de release).
- [ ] Aplicar **API restrictions → Restrict key** liberando apenas as APIs realmente usadas (Firebase Cloud Messaging, Firebase Installations, Identity Toolkit etc.).
- [ ] Considerar rotacionar a chave que foi exposta no histórico antigo.

---

## Comandos úteis

```bash
flutter pub get                                   # dependências
flutter analyze --fatal-warnings                  # análise estática
dart format --output=none --set-exit-if-changed lib test
flutter test                                      # testes
flutter build apk --release                       # APK release (precisa do google-services.json)
```

Para o pipeline completo (formatação, análise, testes, secrets, OSV) execute o workflow **Vigia UI — Mobile Deploy** em GitHub Actions.
