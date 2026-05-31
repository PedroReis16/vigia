# CI Pipeline — Vigia Fall Detection

## Visão geral

O workflow `.github/workflows/onboard-release.yml` é a pipeline **única** do projeto `fall-detection` dentro do monorepo Vigia. Cobre todo o ciclo: valida, testa, audita, faz o build ARM64, publica o tar.gz na vigia-api/MinIO e cria a GitHub Release.

```
onboard-release.yml  →  valida + testa + audita + build ARM64
                        + publica na vigia-api + cria GitHub Release
```

Não existe um workflow separado de deploy: a publicação do tar.gz na vigia-api **é** o "deploy" do fall-detection. A partir desse momento, o `vigia-bootstrap` rodando em cada Raspberry Pi 5 detecta a nova versão consultando `/v1/devices/version/find-for-updates` e baixa o artefato — é um modelo OTA / deploy assíncrono.

## Jobs e ordem de execução

```
validate            ← validações leves, fail-fast (ubuntu-latest)
    ↓ needs
┌───┴──────────────────────────────────────┐
security  quality    test_unit  test_integration
(gitleaks (pylint    (pytest    (pytest -m
pip-audit) bandit)   -m not     integration)
                     integration)
└───┬──────────────────────────────────────┘
    ↓ todos devem passar
publish_release     ← build ARM64 + publica vigia-api + audit trail (Deployment)
    ↓
tag_release         ← tag Git + GitHub Release com release notes
```

## Validações obrigatórias

Todas as etapas abaixo bloqueiam a pipeline em caso de falha.

| Etapa | Job | O que valida |
|-------|-----|-------------|
| Formato de versão | `validate` | `MAJOR.MINOR.PATCH` (ex: `1.2.3`) |
| Branch de origem | `validate` | Branch configurada (atualmente `refactor/project-release`; será `master` após o merge) |
| Arquivos essenciais | `validate` | `pyproject.toml`, `CHANGELOG.md`, `main.py`, `Makefile`, `Dockerfile.linux-arm64-binary`, etc. |
| Entrada no CHANGELOG | `validate` | `## [X.Y.Z]` ou `# [X.Y.Z]` presente em `fall-detection/CHANGELOG.md` |
| Unicidade da tag | `validate` | `vigia-fall-detection@X.Y.Z` não pode existir já |
| Secrets scan | `security` | Gitleaks varre o histórico do checkout |
| Dependências vulneráveis | `security` | pip-audit via `requirements-headless.txt` |
| Lint | `quality` | pylint em `src/app` |
| SAST | `quality` | bandit em `src/app` (severidade média+) |
| Testes unitários | `test_unit` | `pytest -m "not integration"` |
| Testes de integração | `test_integration` | `pytest -m integration` (fake FIWARE com aiohttp TestServer) |
| Build ARM64 | `publish_release` | `docker buildx` produz binário Linux/arm64 |
| Publicação na vigia-api | `publish_release` | `POST /v1/devices/version/register` retorna 2xx |

## `publish_release` — build ARM64 e deploy efetivo

Este é o job que **substitui** o conceito de "deploy" separado: a publicação do tar.gz na vigia-api torna a nova versão disponível para todos os dispositivos do parque automaticamente.

| Etapa | Descrição |
|-------|-----------|
| Audit trail — Deployment record | Cria um GitHub Deployment (environment `production`) com status inicial `in_progress` |
| `docker buildx build` | Constrói a imagem ARM64 via `release/Dockerfile.linux-arm64-binary` em runner `ubuntu-24.04-arm` |
| Extração do bundle | `docker cp` extrai o bundle PyInstaller onedir do container |
| Empacotamento | Gera `dist/vigia-fall-detection-linux-arm64.tar.gz` |
| Publicação | `curl POST` no endpoint `/v1/devices/version/register` da vigia-api (multipart/form-data) |
| Audit trail — final | Atualiza o Deployment para `success` ou `failure` |

**Secret obrigatório:** `VIGIA_API_BASE_URL` apontando para a API de produção.

O job aparece na aba **Environments → production** do repositório, permitindo inspeção do histórico de deploys e (se configurado em Settings → Environments) regras de proteção.

## Etapas opcionais / não bloqueantes

| Etapa | Status | Condição para ativar |
|-------|--------|---------------------|
| Hardware tests (Raspberry Pi 5) | Comentado no workflow | Configurar runner self-hosted com labels `[self-hosted, linux, arm64, raspberry-pi]` e implementar `tests/hardware/` |
| DAST | Não aplicável | App é binário embarcado sem interface HTTP durante CI. Realizar testes de campo manualmente na Raspberry Pi 5. |

## Etapas que exigem runner self-hosted / Raspberry Pi

O job `test_hardware` (comentado no workflow) requer:
- Runner GitHub Actions self-hosted instalado na Raspberry Pi 5
- Labels configuradas: `self-hosted`, `linux`, `arm64`, `raspberry-pi`
- Testes implementados em `fall-detection/tests/hardware/`

Até que o runner esteja disponível, o job usa `continue-on-error: true` e não bloqueia o release.

**Sugestão de testes de hardware a implementar:**
- Smoke: binário inicia e encerra sem erro
- Camera: dispositivo de câmera é detectado pelo sistema operacional
- Model: modelo ONNX (`model/classifier_svm.onnx`) carrega corretamente
- MQTT: conexão com broker MQTT local é estabelecida

## Isolamento do monorepo

- O workflow não usa filtro `paths` no `on:` porque é disparado exclusivamente via `workflow_dispatch` (manual). Não há trigger automático em push.
- Todos os comandos de lint, teste e auditoria usam `working-directory: fall-detection`.
- O pip-audit audita apenas `requirements-headless.txt` do `fall-detection`, não o ambiente global.
- Nenhum comando analisa ou modifica projetos irmãos (`vigia-services`, `vigia_ui`, `docker-compose`).

## Separação de testes

Os testes são separados por marker pytest:

| Comando | Escopo |
|---------|--------|
| `pytest -m "not integration"` | Testes unitários (mocks, sem rede) |
| `pytest -m integration` | Testes de integração (aiohttp TestServer como fake FIWARE) |

**Estrutura dos testes:**
```
tests/
  __init__.py
  unit/
    __init__.py
    *_tests.py              ← testes unitários (mocks, sem rede)
    requests/
      __init__.py
      *_tests.py            ← testes unitários de builders HTTP
  integration/
    __init__.py
    conftest.py             ← fixtures: fake FIWARE server (aiohttp TestServer)
    fake_fiware_app.py      ← servidor FIWARE simulado
    integration_settings_helpers.py
    mqtt_fake_client.py
    *_tests.py              ← testes marcados com @pytest.mark.integration
```

## Como executar

1. Acesse **Actions → Vigia Fall Detection — Onboard Release**
2. Clique em **Run workflow**
3. Informe a versão no formato `MAJOR.MINOR.PATCH` (ex: `1.2.3`)
4. Certifique-se de que `fall-detection/CHANGELOG.md` tem uma entrada para essa versão
5. Execute a partir da branch configurada no job `validate`

Ao final da execução:
- `vigia-fall-detection-linux-arm64.tar.gz` estará disponível na vigia-api (MinIO)
- Uma GitHub Release `vigia-fall-detection@X.Y.Z` terá sido criada
- Um registro de Deployment estará visível em **Environments → production**
- Os Raspberry Pi do parque vão detectar e baixar a nova versão na próxima checagem do `vigia-bootstrap`
