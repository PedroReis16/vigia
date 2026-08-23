# vigia_ui

App Flutter do Vigia (Android / iOS).

## Firebase (credenciais)

`lib/firebase_options.dart` **não é versionado** (contém apiKeys).

### Setup local

```bash
# Opção A — FlutterFire CLI
dart pub global activate flutterfire_cli
flutterfire configure

# Opção B — a partir do exemplo
cp lib/firebase_options.dart.example lib/firebase_options.dart
# edite apiKey / appId / etc. com os valores do Console Firebase
```

`android/app/google-services.json` também é gitignored — copie de
`google-services.json.example` ou baixe no Firebase Console.

### CI (GitHub Actions)

Secrets necessários no repositório:

| Secret | Uso |
|--------|-----|
| `FIREBASE_OPTIONS_DART_BASE64` | `firebase_options.dart` real (base64) |
| `GOOGLE_SERVICES_JSON_BASE64` | `google-services.json` (base64) |
| `ANDROID_KEYSTORE_BASE64` | keystore de release |
| `ANDROID_KEYSTORE_PASSWORD` / `ANDROID_KEY_ALIAS` / `ANDROID_KEY_PASSWORD` | assinatura |

Gerar o base64 do `firebase_options.dart` (PowerShell):

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("vigia_ui\lib\firebase_options.dart"))
```

Bash:

```bash
base64 -w0 vigia_ui/lib/firebase_options.dart
```
