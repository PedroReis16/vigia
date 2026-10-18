# vigia-lab no notebook — passo a passo e contexto para o Claude

Este arquivo existe para você (Erik) abrir um chat do Claude no notebook, apontar para esta
pasta e retomar de onde paramos. Ele não repete o `README.md` (que descreve o módulo): aqui
estão **como instalar do zero**, **o que já foi validado**, **o que está pendente** e um
**prompt pronto** para colar no chat.

## 1. Pegar o código

Repositório do Pedro (`git@github.com:PedroReis16/vigia.git`), branch `feat/vigia-lab`, criada a
partir de `origin/develop` (`2fb8341`). O módulo é a pasta `vigia-lab/`, irmã de `vigia-onboard/`.

```bash
git clone git@github.com:PedroReis16/vigia.git vigia-wt     # use um caminho curto, sem espaços
cd vigia-wt
git checkout feat/vigia-lab
```

Se o repositório já existe no notebook: `git fetch origin && git worktree add ../vigia-wt feat/vigia-lab`.

## 2. Ambiente (Windows, Python 3.12 ou 3.13)

O Python padrão do `py` pode ser o 3.14: use o 3.13 de forma explícita (o `lap==0.5.13` do
onboard não tem garantia no 3.14). O lab usa **o mesmo `.venv` e o mesmo `requirements.txt` do
`vigia-onboard`** — não existe ambiente próprio.

```bash
py -3.13 -m venv vigia-onboard/.venv
vigia-onboard/.venv/Scripts/python.exe -m pip install --upgrade pip
vigia-onboard/.venv/Scripts/python.exe -m pip install -r vigia-onboard/requirements.txt -r vigia-onboard/requirements-dev.txt
```

Download grande (torch CPU via ultralytics). A GPU não é usada: o pipeline do vigia fixa
`device="cpu"` e roda o ONNX no `onnxruntime` de CPU.

## 3. Modelos dos GRUs (já versionados nesta branch)

Os dois ONNX vêm no clone, em `vigia-lab/models/` (`gru34/models/gru_2classes.onnx` e
`gru37/gru_2classes_v2.onnx`, ~180 KB cada). O `gru_2classes.onnx` (34 features) **não existe no
onboard**, por isso o lab o traz junto. O `yolo26s-pose` NÃO vai no Git: é exportado sozinho
na primeira execução (precisa de internet).

Nada a fazer neste passo. O `provision_models.py` só serve para **atualizar** os modelos a partir do
repositório `fall-classifier-bench` (`git@github.com:EForamiglio/fall-detection.git`, branch
`avaliacao-cenarios-campo`); ele confere os hashes contra o `models.lock.json`:

```bash
cd vigia-lab
../vigia-onboard/.venv/Scripts/python.exe scripts/provision_models.py --src <caminho>/fall-classifier-bench
```

Se algum hash divergir do `models.lock.json`, não use: os resultados não seriam comparáveis
(o teste `drift_tests.py` também falha nesse caso).

## 4. Conferir e rodar

```bash
cd vigia-lab
../vigia-onboard/.venv/Scripts/python.exe -m pytest -q          # esperado: 54 passed
PYTHONPATH=. ../vigia-onboard/.venv/Scripts/python.exe -m vigia_lab --ids grace     # janela para a Ana
```

(No Git Bash o `PYTHONPATH=.` é necessário; com `make lab` ele já vai embutido.) Na primeira execução
o `yolo26s-pose` é baixado e exportado para ONNX (~10 s, precisa de internet).

Clique na janela para ela receber as teclas. Menu: setas/`Tab`/`Enter`. Gravando: `m` marca o
início da queda, `x` ou `Esc` aborta. Resumo: `Enter` salva e inicia outra, `r` descarta e repete.
Cada tomada dura 10 s após contagem de 3 s. Os arquivos saem em `vigia-lab/captures/`
(ignorado pelo Git — contém vídeo das pessoas).

Sem câmera: `python -m vigia_lab --replay clipe.mp4 --scenario sentando --duration 12`.

## 5. O que já foi validado (neste computador, 17/10/2026)

- 54 testes passam; replay de vídeo ponta a ponta; 3 tomadas reais com câmera USB.
- Parâmetros do YOLO lidos do código do Pedro; ficha técnica registra versões, hashes e SHA.
- **Vazamento da câmera corrigido** (o Ultralytics não fecha o `LoadStreams` ao parar o gerador;
  `pose_source.close_stream` resolve): log sem avisos MSMF e fps estável entre tomadas.
- Sem falso alarme em `sentando` (3 modelos). Quedas: ver `captures/*_decisions.csv`.

## 6. Descobertas que importam

1. **Histórico apagado por frame sem ID.** Se o BoT-SORT devolve zero tracks num frame, as caixas
   ficam sem `boxes.id`; `unpack_raw_points` numera `0..n-1`, a pessoa 1 vira 0 e o `cleanup` apaga
   a janela dela (2 s nos GRUs, 3 s no matemático). Visto uma vez em plena queda: GRU 34 atrasou
   ~1,3 s e o matemático não alertou. Mitigação no lab: `--ids grace` (ignora caixas sem ID e
   só apaga quem some >1,5 s; `vigia_lab/idpolicy.py`). **Ainda não observado ao vivo com `grace`**
   (nas 3 tomadas o defeito não ocorreu). Nada foi alterado no `vigia-onboard`.
2. **Throttle quantiza o fps entregue.** Período mínimo de 1/12 s: câmera a 30 ou 20 fps entrega
   10/s; a 15 fps entrega 7,5/s; a 13 fps entrega ~6,5/s. O semáforo fica amarelo abaixo de 9/s.
   Com poucos frames por segundo o matemático (janela de 30 frames) quase não decide durante a queda.
3. **Custo do laço (replay, sem câmera):** YOLO ~21 ms + BoT-SORT ~10 ms (o `gmc_method:
   sparseOptFlow` custa ~10 ms; sem GMC o tracker custa ~1 ms) + janela da Ana ~11 ms ⇒ teto ~23 fps.
   Ao vivo os frames chegaram a 64–78 ms (13–15 fps): sobra espera que aponta para a câmera
   ou concorrência de CPU (o ONNX satura os núcleos). **Cada tomada nova grava `bottleneck`,
   `source_wait_ms_mean`, `consumer_ms_mean` e `cpu_pct_*` no `_meta.json` para fechar isso.**
4. `iou` efetivo = 0,7 (o vigia não passa `iou`); o app antigo usava 0,5.
5. O ONNX do GRU 34 não está no onboard (só em `vigia-fall/models/`).

## 7. Pendências

- Gravar 3–5 quedas ao vivo com `--ids grace` e comparar `untracked_frames`, intervalos sem decisão
  e tempo até o primeiro alerta; ler o `bottleneck` de cada tomada (câmera vs CPU).
- Antes de gravar: boa iluminação, fechar outros programas, plano de energia de alto desempenho.
- Contar IDs novos reais no meio do clipe (o `grace` não cobre ID novo do tracker).
- Nota do operador (`n`) não implementada; fase 2 (reprocessar a partir do vídeo/`_raw.npz`
  com outro modelo de pose) não existe.
- Levar ao Pedro: (a) frame sem `boxes.id` reinicia o histórico; (b) custo do GMC do BoT-SORT;
  (c) destino do `gru_2classes.onnx`; (d) opcional: mover `_YOLO_STREAM_KWARGS` para
  `capture/yolo_config.py`.

## 8. Regras do projeto (preferências do Erik)

- Nunca fazer commit nem push sem aprovação explícita dele.
- Não alterar `vigia-onboard/` sem combinar com o Pedro (mudança mínima e retrocompatível).
- Responder em português; explicar o porquê antes de pedir aprovação; thresholds e heurísticas
  precisam ser documentados.
- Textos da janela do OpenCV só em ASCII (sem acentos).

## 9. Prompt para colar no chat do notebook

> Estou na pasta `vigia-lab/` da branch `feat/vigia-lab` do repositório do Pedro (vigia). Leia
> `vigia-lab/COMO_USAR_NO_NOTEBOOK.md` e `vigia-lab/README.md`. Ajude-me a (1) instalar o ambiente
> do passo 2, (2) conferir que os ONNX de `vigia-lab/models/` batem com o `models.lock.json`,
> (3) rodar os testes e (4) abrir o lab com `--ids grace` para eu gravar quedas. Depois analise os
> `_meta.json` e `_decisions.csv` de `captures/` (tempo até o primeiro alerta de cada modelo,
> `untracked_frames`, `bottleneck`). Não faça commit/push sem eu pedir e não altere o `vigia-onboard`.
