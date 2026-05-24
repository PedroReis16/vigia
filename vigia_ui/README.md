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

A pipeline `Vigia UI — Mobile Release` (`.github/workflows/mobile-release.yml`) cobre todo o ciclo: validação, testes, build do APK assinado e publicação da GitHub Release com o APK anexado como asset. O job `build_apk` precisa de **cinco secrets** para hidratar arquivos sensíveis no runner sem versioná-los no repositório.

### Secrets obrigatórios

Cadastre em **Settings → Secrets and variables → Actions** (ou no environment `production` se quiser escopar):

| Secret | Conteúdo |
|--------|----------|
| `GOOGLE_SERVICES_JSON_BASE64` | base64 do `vigia_ui/android/app/google-services.json` |
| `ANDROID_KEYSTORE_BASE64` | base64 do keystore `.jks` de release |
| `ANDROID_KEYSTORE_PASSWORD` | senha do keystore |
| `ANDROID_KEY_ALIAS` | alias da chave de assinatura |
| `ANDROID_KEY_PASSWORD` | senha da chave |

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

### 2. Gerar o conteúdo base64 do keystore Android

A partir do arquivo `.jks` de release (gerado uma vez com `keytool -genkey -v -keystore release.keystore -keyalg RSA -keysize 2048 -validity 10000 -alias vigia-ui`):

**Linux / macOS:**

```bash
base64 -w 0 release.keystore > release-keystore.b64
cat release-keystore.b64               # copie esse conteúdo
```

**Windows (PowerShell):**

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("release.keystore")) | Set-Clipboard
```

Cadastre o resultado como `ANDROID_KEYSTORE_BASE64`. Os três secrets restantes (`ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`) vão como texto plano — são as credenciais do keystore. **Nunca versione o `.jks` nem essas senhas.**

### 3. (iOS, futuro)

Quando habilitar build iOS, replicar a estratégia com `GOOGLE_SERVICE_INFO_PLIST_BASE64` para o `GoogleService-Info.plist` e os equivalentes de assinatura iOS (provisioning profile + certificado p12).

### 4. Como os secrets são consumidos

O job `build_apk` do `mobile-release.yml` hidrata, usa e remove todos os arquivos sensíveis no próprio runner — eles nunca persistem após o build:

1. `GOOGLE_SERVICES_JSON_BASE64` → `android/app/google-services.json`
2. `ANDROID_KEYSTORE_BASE64` → `android/app/release.keystore`
3. As três senhas → `android/key.properties`
4. `flutter build apk --release` produz o APK assinado
5. Step `if: always()` remove os três arquivos do runner (mesmo em falha)

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

Para o pipeline completo (formatação, análise, testes, secrets, OSV, build do APK assinado e publicação da GitHub Release) execute o workflow **Vigia UI — Mobile Release** em GitHub Actions.
