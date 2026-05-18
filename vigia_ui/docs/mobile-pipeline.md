# Pipeline de Release — Vigia UI

## Visão geral

O `mobile-deploy.yml` é a pipeline DevSecOps de **preparação de release** do projeto Flutter `vigia_ui`. Ele valida, testa e audita o projeto antes de criar uma GitHub Release versionada. A geração do APK final e a distribuição para Android são responsabilidade do `deploy-trigger.yml`.

```
mobile-deploy.yml  →  valida + testa + audita + cria Release
deploy-trigger.yml →  consome a Release + gera APK + distribui
```

## Como acionar

A pipeline é acionada manualmente via **workflow_dispatch** no GitHub Actions:

1. Acesse **Actions → Vigia UI — Mobile Deploy → Run workflow**
2. Informe a versão no formato semver: `X.Y.Z` (ex: `1.0.0`)
3. A pipeline só aceita disparos de `master` ou `release/*`

### Pré-requisitos antes de acionar

- [ ] `pubspec.yaml` contém `version: X.Y.Z` (ou `X.Y.Z+<build>`)
- [ ] `vigia_ui/CHANGELOG.md` tem a seção `## [X.Y.Z]` com as notas da versão
- [ ] A tag `vigia-ui@X.Y.Z` ainda não existe no repositório

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
                └── release_preparation (só após todos passarem)
```

### 1. `preflight` — obrigatório, fail-fast

Executa validações leves sem instalar nenhuma ferramenta pesada. Uma falha aqui aborta toda a pipeline imediatamente.

| Validação | Script |
|-----------|--------|
| Formato semver `X.Y.Z` | `tool/ci/validate_version.sh` |
| `pubspec.yaml` contém a versão | `tool/ci/validate_version.sh` |
| `CHANGELOG.md` tem a seção `## [X.Y.Z]` | `tool/ci/validate_version.sh` |
| Tag `vigia-ui@X.Y.Z` ainda não existe | inline no workflow |
| Branch é `master` ou `release/*` | inline no workflow |
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

### 9. `release_preparation` — final

Só executa se **todos os jobs anteriores passaram**. Cria:
1. Tag `vigia-ui@X.Y.Z` no repositório
2. GitHub Release com:
   - Release notes extraídas do `CHANGELOG.md`
   - Metadados de release (`release-metadata.json`) para o `deploy-trigger.yml`

O APK **não é gerado aqui**.

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
| google-services.json ausente | Sim | Sim |
| Dart format | Sim | Sim |
| Flutter analyze | Sim | Sim |
| Unit/Widget tests | Sim | Sim |
| Android security (crítico) | Sim | Sim |
| Android security (avisos) | Sim | Não |
| OSV Scanner | Sim | Sim |
| Integration tests | Evolutivo | Só se existirem |
| Golden tests | Futuro | — |
| E2E / Device farm | Futuro | — |

## Configuração do Firebase no CI

O `google-services.json` está no `.gitignore` e não deve ser versionado. A estratégia do projeto:

- **Validação e testes** (`flutter analyze`, `flutter test`): não requerem o arquivo
- **Build de APK** (responsabilidade do `deploy-trigger.yml`): requer o arquivo via secret

Para configurar quando o `deploy-trigger.yml` precisar:
```
Secrets necessários no repositório GitHub:
  GOOGLE_SERVICES_JSON  — conteúdo do google-services.json de produção
```

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

## Etapas futuras — E2E e Device Farm

Testes end-to-end em dispositivos Android reais exigem infraestrutura adicional.

### Opção 1 — Firebase Test Lab (recomendado, integrado ao projeto)

```yaml
# Pré-requisitos:
#   - APK de debug gerado (requer google-services.json via secret)
#   - Service account com permissão no Firebase project (vigia-fall-detection)
#   - Secret: FIREBASE_SERVICE_ACCOUNT_JSON

- name: Build APK de debug para device farm
  working-directory: vigia_ui
  env:
    GOOGLE_SERVICES_JSON: ${{ secrets.GOOGLE_SERVICES_JSON }}
  run: |
    echo "$GOOGLE_SERVICES_JSON" > android/app/google-services.json
    flutter build apk --debug

- name: Firebase Test Lab
  run: |
    gcloud firebase test android run \
      --type instrumentation \
      --app vigia_ui/build/app/outputs/apk/debug/app-debug.apk \
      --test vigia_ui/build/app/outputs/apk/androidTest/debug/app-debug-androidTest.apk \
      --device model=Pixel2,version=28,locale=pt_BR,orientation=portrait
```

### Opção 2 — AWS Device Farm

Alternativa se o projeto migrar para infraestrutura AWS. Requer:
- AWS credentials configuradas como secrets
- APK de debug gerado

### Opção 3 — Runner com dispositivo físico

Para testes offline ou com hardware específico, configure um runner self-hosted com dispositivo Android conectado via ADB.

## Conexão com `deploy-trigger.yml`

A GitHub Release criada pelo `mobile-deploy.yml` contém o arquivo `release-metadata.json` com:

```json
{
  "service": "vigia-ui",
  "version": "1.0.0",
  "pubspec_version": "1.0.0+1",
  "tag": "vigia-ui@1.0.0",
  "commit_sha": "<sha>",
  "branch": "master",
  "flutter_channel": "stable",
  "released_at": "2026-05-18T00:00:00Z",
  "released_by": "username",
  "apk_status": "pending_deploy_trigger"
}
```

O `deploy-trigger.yml` deve:
1. Validar que a Release `vigia-ui@X.Y.Z` existe
2. Baixar o `release-metadata.json`
3. Usar `commit_sha` para fazer checkout da versão exata
4. Injetar `google-services.json` via secret
5. Executar `flutter build apk --release` com a versão correta
6. Distribuir o APK (Google Play, Firebase App Distribution, etc.)
