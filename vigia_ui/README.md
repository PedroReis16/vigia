# vigia_ui

App Flutter do Vigia (Android / iOS).

## Firebase (credenciais — Android)

Push/FCM é **Android-only**. Execuções no **iPhone/simulador iOS** não inicializam Firebase.

No Android, o app usa `android/app/google-services.json` (gitignored). Opcionalmente,
`lib/firebase_options.dart` pode ser gerado pelo FlutterFire CLI, mas **não é necessário**
para compilar nem rodar no iOS.

### Setup local (Android / push)

```bash
# Opção A — FlutterFire CLI (gera google-services.json + firebase_options.dart)
dart pub global activate flutterfire_cli
flutterfire configure

# Opção B — google-services.json manual
cp android/app/google-services.json.example android/app/google-services.json
# edite com os valores do Console Firebase
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
