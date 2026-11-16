---
name: commits-atomicos
description: >-
  Divide alterações pendentes em commits atômicos por feature/responsabilidade,
  com Conventional Commits e sem menção a IA, assistente ou ferramenta nas
  mensagens. Use when the user asks to commit, git commit, criar commit,
  commits atômicos, or to apply pending repository changes.
---

# Commits Atômicos, Sem Atribuição a Ferramentas

## Objetivo

Ao aplicar commits das alterações pendentes no projeto, nunca gerar um único commit "geral" com tudo
junto. As mudanças devem ser separadas em commits atômicos, cada um representando uma única feature,
correção ou responsabilidade lógica — e as mensagens devem ser indistinguíveis de um commit escrito
manualmente por um desenvolvedor.

## Processo antes de commitar

1. Revise o estado completo do repositório (`git status`, `git diff`) antes de decidir qualquer coisa.
2. Identifique os "grupos lógicos" de mudança presentes no diff. Um grupo é definido por:
   - uma única feature, correção de bug, refatoração ou tarefa de infra/config por commit;
   - não misturar, no mesmo commit, mudanças de módulos/serviços não relacionados entre si;
   - não misturar refatoração com mudança de comportamento no mesmo commit;
   - não misturar mudança de código com mudança de dependências não relacionadas no mesmo commit.
3. Defina a ordem dos commits respeitando dependências (ex.: se uma feature depende de uma migração
   de schema, a migração vai primeiro).
4. Monte cada commit com precisão cirúrgica (`git add <arquivos específicos>` ou `git add -p`),
   nunca `git add .` quando isso misturaria grupos diferentes.
5. Antes de aplicar, liste os commits planejados (ordem + mensagem de cada um) para que fique claro
   o que será feito.
6. Se algum arquivo no diff for sensível (`.env`, chaves, credenciais, certificados) ou parecer
   artefato não intencional (build, cache, log), não o inclua em nenhum commit — sinalize isso em vez
   de commitar.

## Formato das mensagens

- Conventional Commits: `tipo(escopo): descrição curta no imperativo`.
  Tipos comuns: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `build`, `ci`.
- Primeira linha: até ~72 caracteres, sem ponto final, no imperativo (ex.: "adiciona validação de
  quota no envio de imagens", não "adicionado" ou "adicionando").
- Corpo (opcional, quando o "porquê" não for óbvio pela mensagem curta): parágrafo curto explicando a
  motivação ou o contexto da decisão, não uma repetição do diff.
- Escopo entre parênteses deve refletir o módulo/serviço afetado quando fizer sentido no projeto
  (ex.: `feat(aggregation-worker): ...`, `fix(gerenciamento-storage): ...`).

## Proibido em qualquer commit, sem exceção

- Qualquer linha `Co-Authored-By: ...` referente a IA, assistente ou ferramenta.
- Qualquer menção a "Generated with", "made with", "Written by Claude/Cursor/AI/Copilot" ou
  equivalente, em qualquer idioma.
- Qualquer emoji, link ou rodapé padrão de ferramenta de geração de commit.
- Qualquer texto que revele que a mudança foi aplicada por um assistente em vez de pelo autor do
  repositório.
As mensagens devem ler como se tivessem sido escritas inteiramente pelo desenvolvedor responsável
pelo repositório.

## Relação com a documentação da estrutura do projeto

Se algum dos commits atômicos incluir uma alteração estrutural coberta pela regra
`project-docs.mdc` (novo módulo, serviço, dependência relevante, endpoint, decisão
arquitetural), garanta que a atualização correspondente esteja no mesmo commit da mudança que a
originou:

- cross-cutting da solução → `docs/project-structure.md` (estrutura atual apenas; **sem** changelog técnico nesse arquivo);
- escopo de um projeto → `docs/<NomeDoProjeto>/README.md` e/ou `docs/<NomeDoProjeto>/CHANGELOG.md`
  (changelog técnico: o que/quando mudou — único lugar para histórico técnico).

Não deixe a atualização da documentação solta ou para um commit "docs" genérico no fim, a menos que
várias mudanças não relacionadas tenham gerado, cada uma, sua própria edição na documentação.

**Não** incluir nem editar o `CHANGELOG.md` de release na raiz do projeto (`MobilePacs.*/CHANGELOG.md`
ou equivalente) como parte desse fluxo — esse arquivo é manutenção manual do desenvolvedor para
notas de build/versão e não faz parte da documentação estrutural automática.

## Regra de ouro

Cada commit, isolado, deve fazer sentido sozinho para alguém lendo o histórico do repositório depois —
tanto no conteúdo (o que mudou) quanto na mensagem (por que mudou) — sem nenhum rastro de que foi
gerado por uma ferramenta de IA.