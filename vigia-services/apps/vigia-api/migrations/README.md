# Migrations (Goose)

Este diretório concentra as migrations SQL da **vigia-api**. O [Goose](https://github.com/pressly/goose) versiona e aplica mudanças no PostgreSQL.

## Como entra em produção

1. Os arquivos `*.sql` aqui são embutidos no binário em tempo de compilação (`embed.go` + `//go:embed *.sql`).
2. Ao iniciar a API, `config.InitDatabase` abre o GORM, obtém `*sql.DB` e executa `goose.Up` com esse pacote embutido.
3. O Goose registra o que já foi aplicado numa tabela de controle no banco (comportamento padrão do dialect Postgres). Novas migrations são aplicadas na ordem dos números nos nomes dos arquivos.

Ou seja: **commitar o `.sql` + gerar/deploy do binário** já inclui a migration; não é necessário copiar a pasta `migrations/` para o servidor além do executável.

**Uber Fx:** o `InitDatabase` só roda se o grafo de dependências **precisar** de `*gorm.DB`. Enquanto nenhum serviço ou repositório injetar o banco, o Fx pode nunca chamar esse provider — e as migrations não executam. O `cmd/main.go` usa `fx.Invoke(func(*gorm.DB) {})` para garantir que a conexão e o Goose rodem sempre na inicialização.

## Criar uma nova migration

### 1. Instalar o CLI do Goose (uma vez)

```bash
go install github.com/pressly/goose/v3/cmd/goose@latest
```

### 2. Gerar o arquivo

Na raiz do app (`vigia-api`), apontando o diretório deste README:

```bash
goose -dir migrations create nome_descritivo_da_mudanca sql
```

Isso cria um arquivo com timestamp no nome (ex.: `20260110120000_nome_descritivo_da_mudanca.sql`). O prefixo numérico define a ordem de execução.

### 3. Editar o SQL

Cada migration deve ter pelo menos um bloco **Up** (aplicar) e um **Down** (reverter), no formato esperado pelo Goose:

```sql
-- +goose Up
CREATE TABLE exemplo (...);

-- +goose Down
DROP TABLE IF EXISTS exemplo;
```

Para várias instruções que precisam de transação ou delimitação explícita no Postgres, use os marcadores `StatementBegin` / `StatementEnd` conforme a [documentação do Goose](https://github.com/pressly/goose/blob/master/README.md).

### 4. Validar

- Rode a API localmente com `DATABASE_CONNECTION` apontando para um banco de teste; o startup aplica as migrations pendentes.
- Ou aplique só pelo CLI (útil para debug):

```bash
goose -dir migrations postgres "$DATABASE_CONNECTION" status
goose -dir migrations postgres "$DATABASE_CONNECTION" up
```

## Boas práticas

- Um arquivo por mudança lógica (facilita revisão e rollback).
- Manter o **Down** coerente com o **Up** (reverter sem deixar o schema inconsistente).
- Alinhar tipos e nomes de tabelas/colunas com os models GORM para evitar divergência entre schema e código.

## Banco que já tinha tabelas criadas fora do Goose

Se o schema já existia (por exemplo criado só pelo GORM `AutoMigrate`), a primeira migration pode conflitar com objetos já existentes. Nesses casos é preciso alinhar manualmente (baseline / ajustar migrations / ambiente limpo). Em desenvolvimento, costuma-se usar um banco novo ou dropar objetos afetados antes de testar.
