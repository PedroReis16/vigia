# Pipeline de Release — Vigia UI

## Visão geral

O `mobile-release.yml` (`.github/workflows/mobile-release.yml`) é a pipeline DevSecOps **única** do projeto Flutter `vigia_ui`. Ele cobre todo o ciclo de release: validação, testes, análise de segurança, build do APK assinado e publicação da GitHub Release com o APK anexado como asset.

```
mobile-release.yml  →  valida + testa + audita + build APK + GitHub Release (com APK)
```

Não existe um workflow separado de deploy: o "deploy" do app mobile é a publicação da GitHub Release com o APK assinado anexado — é de lá que o APK é baixado pelos usuários finais.

## Como acionar

A pipeline é acionada manualmente via **workflow_dispatch** no GitHub Actions:

1. Acesse **Actions → Vigia UI — Mobile Release → Run workflow**
2. Informe a versão no formato semver: `X.Y.Z` (ex: `1.0.0`)
3. A pipeline só aceita disparos da branch configurada (ver job `preflight`)

### Pré-requisitos antes de acionar

- [ ] `pubspec.yaml` contém `version: X.Y.Z` (ou `X.Y.Z+<build>`)
- [ ] `vigia_ui/CHANGELOG.md` tem a seção `## [X.Y.Z]` com as notas da versão
- [ ] A tag `vigia-ui@X.Y.Z` ainda não existe no repositório
- [ ] Todos os secrets de assinatura Android estão cadastrados (ver "Setup do CI/CD" no `vigia_ui/README.md`)

## Jobs da pipeline

### Fluxo de execução

```
preflight (fail-fast leve)
    │
    ├── security_secrets    (GitLeaks — paralelo)
    ├── setup_validation    (Flutter + Firebase — paralelo)
    ├── quality             (format + analyze — paralelo)
    ├── tests               (unit + widget — paralelo)
    ├── android_security    (manifest + gradle — paralelo)
    ├── dependency_security (osv-scanner — paralelo)
    └── integration_tests   (evolutivo — paralelo)
                │
                └── build_apk           (APK assinado; precisa de todos os gates acima)
                         │
                         └── release_and_deploy  (tag + GitHub Release com APK + audit trail)
```

### 1. `preflight` — obrigatório, fail-fast

Executa validações leves sem instalar nenhuma ferramenta pesada. Uma falha aqui aborta toda a pipeline imediatamente.

| Validação | Script |
|-----------|--------|
| Formato semver `X.Y.Z` | `tool/ci/validate_version.sh` |
| `pubspec.yaml` contém a versão | `tool/ci/validate_version.sh` |
| `CHANGELOG.md` tem a seção `## [X.Y.Z]` | `tool/ci/validate_version.sh` |
| Tag `vigia-ui@X.Y.Z` ainda não existe | inline no workflow |
| Branch de origem é a esperada | inline no workflow |
| Estrutura mínima de arquivos presente | `tool/ci/validate_structure.sh` |
| Arquivos sensíveis ausentes do repo | `tool/ci/validate_structure.sh` |

### 2. `security_secrets` — obrigatório

GitLeaks escaneia todo o repositório (monorepo) em busca de secrets vazados. Uma falha bloqueia o release.

### 3. `setup_validation` — obrigatório

Instala Flutter e valida:
- `flutter pub get` funciona sem erros
- `firebase.json` é JSON válido com appId e projectId Android
- `google-services.json` **não está** versionado (somente `.example` é aceito)
- Exibe dependências desatualizadas (informativo, não bloqueia)

### 4. `quality` — obrigatório

| Comando | Comportamento em falha |
|---------|------------------------|
| `dart format --set-exit-if-changed lib test` | Bloqueia — código deve estar formatado |
| `flutter analyze --fatal-warnings` | Bloqueia — warnings são tratados como erros |

### 5. `tests` — obrigatório

Executa `flutter test --reporter=expanded`. Cobre:
- **Unit tests** — qualquer arquivo em `test/` que teste lógica pura
- **Widget tests** — `test/widget_test.dart` (testa `MyApp` sem Firebase)

Os testes não requerem `google-services.json` porque `test/` importa `app.dart` diretamente, sem inicializar Firebase.

### 6. `android_security` — obrigatório

Valida sem instalar Gradle. Usa `tool/ci/validate_android_security.sh`:

| Verificação | Nível |
|-------------|-------|
| `android:debuggable="true"` no manifest principal | Erro (bloqueia) |
| `applicationId` não é `com.example.*` | Erro (bloqueia) |
| `usesCleartextTraffic="true"` | Aviso |
| `allowBackup` não definido explicitamente | Aviso |
| Release signing com debug keys | Aviso |
| Permissões sensíveis inesperadas | Aviso |

### 7. `dependency_security` — obrigatório

OSV Scanner analisa o `pubspec.lock` contra o banco [Open Source Vulnerabilities](https://osv.dev). Não requer Flutter SDK. Uma vulnerabilidade conhecida bloqueia o release.

### 8. `integration_tests` — evolutivo (não bloqueia atualmente)

Verifica se `integration_test/` existe com arquivos `.dart`:
- **Se não existir:** registra um `::notice::` e conclui com sucesso
- **Se existir:** executa `flutter test integration_test/`

Para ativar: basta criar `vigia_ui/integration_test/` com testes Flutter.

### 9. `build_apk` — obrigatório

Roda depois que **todos** os gates de qualidade, segurança e teste passaram. Hidrata arquivos sensíveis a partir de GitHub Secrets (nunca versionados) e produz o APK assinado.

| Etapa | Descrição |
|-------|-----------|
| Hidratar `google-services.json` | Decodifica `GOOGLE_SERVICES_JSON_BASE64` em `android/app/google-services.json` |
| Hidratar keystore | Decodifica `ANDROID_KEYSTORE_BASE64` em `android/app/release.keystore` |
| Gerar `key.properties` | Monta o arquivo de configuração de assinatura a partir dos secrets |
| `flutter build apk --release` | Build de release assinado |
| Renomear APK | `app-release.apk` → `vigia-ui-X.Y.Z-release.apk` |
| Upload como workflow artifact | `vigia-ui-X.Y.Z-apk` (retenção: 30 dias) |
| Cleanup | Remove arquivos sensíveis do runner (sempre, mesmo em falha) |

Se algum secret obrigatório estiver ausente, o job falha com `::error::` explícito apontando o nome do secret.

### 10. `release_and_deploy` — final

Só executa após `build_apk` concluir com sucesso. Roda no environment `production` do GitHub (permite proteções como aprovadores obrigatórios). Cria:

1. Registro de **GitHub Deployment** com status `in_progress` (audit trail)
2. Download do APK artifact gerado em `build_apk`
3. Tag `vigia-ui@X.Y.Z` no repositório
4. **GitHub Release** com:
   - Release notes extraídas do `CHANGELOG.md` + bloco de metadados
   - `vigia-ui-X.Y.Z-release.apk` anexado como asset (downloadable)
   - `release-metadata.json` anexado como asset (info estruturada da release)
5. Atualização do Deployment para `success` ou `failure`

## Setup do CI/CD — secrets necessários

Cadastre todos os secrets em **Settings → Secrets and variables → Actions** (ou no environment `production` para escopar):

| Secret | Conteúdo |
|--------|----------|
| `GOOGLE_SERVICES_JSON_BASE64` | base64 do `vigia_ui/android/app/google-services.json` |
| `ANDROID_KEYSTORE_BASE64` | base64 do keystore `.jks` de release |
| `ANDROID_KEYSTORE_PASSWORD` | senha do keystore |
| `ANDROID_KEY_ALIAS` | alias da chave de assinatura |
| `ANDROID_KEY_PASSWORD` | senha da chave |

Ver `vigia_ui/README.md` (seção "Setup do CI/CD") para passos detalhados de geração dos secrets, inclusive comandos `base64` para Linux/macOS e PowerShell para Windows.

## Validações obrigatórias vs. opcionais

| Validação | Obrigatória | Bloqueia release |
|-----------|-------------|------------------|
| Formato da versão | Sim | Sim |
| CHANGELOG atualizado | Sim | Sim |
| Tag única | Sim | Sim |
| Branch correta | Sim | Sim |
| Estrutura do projeto | Sim | Sim |
| GitLeaks | Sim | Sim |
| Firebase config | Sim | Sim |
| google-services.json ausente do repo | Sim | Sim |
| Dart format | Sim | Sim |
| Flutter analyze | Sim | Sim |
| Unit/Widget tests | Sim | Sim |
| Android security (crítico) | Sim | Sim |
| Android security (avisos) | Sim | Não |
| OSV Scanner | Sim | Sim |
| Integration tests | Evolutivo | Só se existirem |
| Build APK assinado | Sim | Sim |
| Golden tests | Futuro | — |
| E2E / Device farm | Futuro | — |

## Etapas futuras — Golden Tests

Golden tests validam a aparência visual dos widgets comparando com imagens de referência.

**Para habilitar:**
1. Adicionar `golden_toolkit` ao `pubspec.yaml`
2. Criar testes em `test/goldens/`
3. Gerar imagens base com `flutter test --update-goldens`
4. Adicionar step no job `tests`:
   ```yaml
   - name: Flutter — golden tests
     run: flutter test test/goldens/
   ```

**Atenção:** golden tests são sensíveis à versão do Flutter e plataforma. Considere fixar a versão do Flutter (usando FVM ou `flutter-action` com `flutter-version:`) para evitar falsos positivos em atualizações de canal.

## Etapas futuras — Distribuição automatizada (Play Store / Firebase App Distribution)

Hoje o APK é publicado como asset da GitHub Release; usuários baixam e instalam manualmente. Para automatizar a distribuição:

### Opção A — Google Play Store

Acrescentar um job `publish_play_store` (`needs: release_and_deploy`) que use [`r0adkll/upload-google-play`](https://github.com/r0adkll/upload-google-play) ou similar. Requer:
- Service account JSON com permissão no Google Play Console
- Configuração de internal/alpha/beta/production tracks

### Opção B — Firebase App Distribution

Útil para distribuir builds de QA antes da loja. Requer:
- Service account com permissão em Firebase App Distribution
- Configuração de grupos de testers

### Opção C — Device Farm para testes E2E

Testes end-to-end em dispositivos Android reais como gate adicional antes do release:

```yaml
# Firebase Test Lab (recomendado, integrado ao projeto):
- name: Firebase Test Lab
  run: |
    gcloud firebase test android run \
      --type instrumentation \
      --app build/app/outputs/apk/release/vigia-ui-X.Y.Z-release.apk \
      --device model=Pixel2,version=28,locale=pt_BR,orientation=portrait
```

Alternativas: AWS Device Farm; runner self-hosted com dispositivo físico conectado via ADB.
