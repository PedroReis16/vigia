# CI Pipeline — Vigia Fall Detection

## Visão geral

O workflow `.github/workflows/onboard-deploy.yml` é o portão de qualidade do projeto `fall-detection` dentro do monorepo Vigia. Ele valida, testa e prepara o release antes de qualquer deploy ao dispositivo embarcado.

```
onboard-deploy.yml  →  cria a GitHub Release (tag Git + release notes)
deploy-trigger.yml  →  (futuro) consome a Release, faz o build do binário
                        ARM64 e instala na Raspberry Pi 5
```

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
tag_release         ← tag Git + GitHub Release (sem deploy)
```

## Validações obrigatórias

Todas as etapas abaixo bloqueiam a pipeline em caso de falha.

| Etapa | Job | O que valida |
|-------|-----|-------------|
| Formato de versão | `validate` | `MAJOR.MINOR.PATCH` (ex: `1.2.3`) |
| Branch de origem | `validate` | Deve ser `master` ou `main` |
| Arquivos essenciais | `validate` | `pyproject.toml`, `CHANGELOG.md`, `main.py`, `Makefile`, `Dockerfile.linux-arm64-binary`, etc. |
| Entrada no CHANGELOG | `validate` | `## [X.Y.Z]` ou `# [X.Y.Z]` presente em `fall-detection/CHANGELOG.md` |
| Unicidade da tag | `validate` | `vigia-fall-detection@X.Y.Z` não pode existir já |
| Secrets scan | `security` | Gitleaks varre o histórico do checkout |
| Dependências vulneráveis | `security` | pip-audit via `requirements-headless.txt` |
| Lint | `quality` | pylint em `src/app` |
| SAST | `quality` | bandit em `src/app` (severidade média+) |
| Testes unitários | `test_unit` | `pytest -m "not integration"` |
| Testes de integração | `test_integration` | `pytest -m integration` (fake FIWARE com aiohttp TestServer) |

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

## Conexão com deploy-trigger.yml

O workflow `deploy-trigger.yml` (existente) é voltado para a **Vigia API** (serviço Docker). No futuro, um workflow equivalente para o `fall-detection` deverá:

1. Consumir a GitHub Release criada por este workflow (`vigia-fall-detection@X.Y.Z`)
2. Fazer o build do binário ARM64 via `make build-linux-arm64` (requer Docker buildx)
3. Copiar o artefato via SCP para a Raspberry Pi 5
4. Reiniciar o serviço systemd (`fall-detection.service`)

Este workflow propositalmente **não faz o deploy** — a criação da Release é o sinal de "pronto para deploy" que o futuro trigger consumirá.

## Como executar

1. Acesse **Actions → Vigia Fall Detection — Onboard Deploy**
2. Clique em **Run workflow**
3. Informe a versão no formato `MAJOR.MINOR.PATCH` (ex: `1.2.3`)
4. Certifique-se de que `fall-detection/CHANGELOG.md` tem uma entrada para essa versão
5. Execute a partir da branch `master`
