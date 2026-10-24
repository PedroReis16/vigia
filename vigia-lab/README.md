# vigia-lab

Captura e avaliação de quedas usando **o mesmo pipeline do `vigia-onboard`**
(yolo26s-pose, mesmos parâmetros do YOLO, mesmo filtro e mesma cadência de
entrega, mesmas dependências). Roda no notebook (Windows); não vai para a
Raspberry. Nada em `vigia-onboard/` é alterado.

Motivo: o `keypoint_extraction` (yolov8n-pose@640, conf 0,4, iou 0,5) não era
fiel ao vigia, o que enfraquecia os testes. Aqui os parâmetros são **lidos do
próprio código do onboard** (`capture/capture_runner.py`, `_YOLO_STREAM_KWARGS`,
via AST) e cada tomada grava uma ficha técnica com versões, hashes e SHA do commit.

## O que cada tomada grava (`captures/<cenario>/`)

| Arquivo | Conteúdo |
|---|---|
| `<take>_pN.npy` / `_labels.npy` / `_t.npy` | por pessoa: keypoints (T,17,3) com conf<0,3 zerada, rótulo (0=ADL, 2=FALL), tempo (s) por frame — formato compatível com o `keypoint_extraction` |
| `<take>_raw.npz` | TODOS os frames processados pelo YOLO, keypoints PRÉ-filtro, `t_wall`, `t_mono`, `delivered`, `yolo_ms`, brilho |
| `<take>_decisions.csv` | decisões de GRU 34, GRU 37 e Math (label, alert, prob/score, latência) |
| `<take>_meta.json` | ficha técnica, métricas de qualidade, semáforo, marcas da Ana, resets de histórico |
| `<take>.avi` | vídeo bruto (MJPG). Fica fora do Git |
| `manifest.csv` | uma linha por pessoa; colunas antigas + `event_t`, `video_path`, `quality_verdict`, `meta_path` |

## Instalação

1. Worktree da branch (`feat/vigia-lab`, a partir de `origin/develop`).
2. Python **3.12 ou 3.13** (o `py` padrão aqui é 3.14: usar `py -3.13`):
   ```bash
   py -3.13 -m venv vigia-onboard/.venv
   vigia-onboard/.venv/Scripts/python.exe -m pip install -r vigia-onboard/requirements.txt -r vigia-onboard/requirements-dev.txt
   ```
3. Modelos dos GRUs (não existem no onboard; já vêm versionados em `vigia-lab/models/`).
   Só para atualizá-los a partir do `fall-classifier-bench`:
   ```bash
   cd vigia-lab
   ../vigia-onboard/.venv/Scripts/python.exe scripts/provision_models.py --src <caminho>/fall-classifier-bench
   ```
   Confere os hashes contra `models.lock.json`.
4. A 1ª execução exporta o `yolo26s-pose` para ONNX (~10 s, baixa o `.pt`).

## Uso

```bash
cd vigia-lab
make lab          # interface para a Ana (janela)   =  python -m vigia_lab
make test         # pytest

# sem janela:
python -m vigia_lab --scenario queda_de_frente --duration 10
python -m vigia_lab --replay clip.mp4 --scenario sentando --duration 12   # sem câmera
```

Teclas: menu `setas` / `Tab` (filtra FALL/ADL) / `Enter` inicia / `Esc` sai.
Durante a gravação `m` marca o instante da queda, `x` ou `Esc` aborta.
Resumo: `Enter` salva e grava a próxima, `r` descarta e repete, `Esc` salva e volta ao menu.
**A janela precisa de foco** (clique nela) para receber as teclas.
Protocolo de clipe: contagem 3 s, depois 10 s (≈3 s antes, ≈2 s de evento, ≥5 s depois).

## Gravar leve + analisar offline (fluxo recomendado para coletar dados)

O app ao vivo (`python -m vigia_lab`) satura a CPU de notebooks fracos e entrega menos de 10 quadros/s
aos modelos. Para coletar dados sem essa limitação, separe a coleta da análise:

```bash
# 1) COLETA (notebook de campo, a Ana opera): só câmera + vídeo, ~30 fps
python -m vigia_lab record                    # --duration 10 --resolution 640x480 --out captures
# 2) ANÁLISE (máquina potente): YOLO + GRU 34 + GRU 37 + matemático sobre os vídeos
python -m vigia_lab process --captures captures --pose-fps 6,8,10,15 --ids baseline,grace
# 3) tabela resumo (também gerada ao fim do process)
python -m vigia_lab report --root reprocessed
```

`record`: menu de cenários, contagem de 3 s, duração fixa de 10 s (tecla `d` alterna para manual: a Ana
encerra com Espaço/Enter). Durante a gravação: `m` marca o INÍCIO da queda, `n` o FIM (contato com o
chão), `u` desfaz, `x` aborta. Ao terminar, uma verificação rápida de pose (~1 s) e as métricas da câmera
geram o semáforo da captura (fps medido, quadros perdidos, brilho, tronco visível). Cada tomada grava:
`<take>.avi` (MJPG), `<take>_frames.npz` (tempo real de cada frame), `<take>_capture.json` (marcas,
métricas, ficha técnica) e uma linha em `recordings.csv`.

`process`: reprocessa cada vídeo simulando que o dispositivo processa `--pose-fps` quadros por segundo
(escolhe os quadros por tempo-alvo ANTES do YOLO, para o tracker ver a mesma cadência) e aplica o mesmo
throttle/filtro/modelos do vigia. Saída em `reprocessed/fps<N>_<ids>/<cenário>/` (decisões, meta, raw).
`pose_fps` é a taxa média; o throttle de 12 Hz do vigia ainda quantiza a entrega (ex.: pose a 15 fps entrega
~7,5/s ao classificador). Para o dispositivo real, meça o fps de pose na Raspberry e use esse valor.

`report`: por configuração e modelo, quedas detectadas, latência mediana, falsos alarmes em ADL, maior
intervalo sem decisão e trocas de ID. Definições (para o PFC):
- início de referência da queda = `event_t_auto` (ângulo do tronco > 60° por 2 frames), com a marca da
  operadora menos 0,4 s (atraso de reação) como reserva;
- queda "detectada" = algum `alert` em [início, fim + 2 s] (sem marca de fim: início + 5 s); o 2 s extra cobre
  a confirmação de 2 predições seguidas dos GRUs; latência = 1º alerta − início;
- ADL com "falso alarme" = qualquer `alert` no clipe.

## Histórico apagado por troca de ID (`--ids`)

Quando o tracker do Ultralytics devolve zero tracks num frame, as caixas ficam sem
`boxes.id` e o vigia numera `0..n-1`: a pessoa 1 vira 0, o `cleanup` apaga o histórico dela e
as janelas (2 s nos GRUs, 3 s no matemático) levam esse tempo para encher de novo — em plena
queda. Medido numa tomada: GRU 34 alertou 3,6 s depois do início da queda e o matemático não alertou.

- `--ids baseline` (padrão): comportamento do vigia, fiel ao deploy.
- `--ids grace`: ignora detecções sem ID e só apaga o histórico de quem some por mais de 1,5 s
  (`vigia_lab/idpolicy.py`). Aplicado só no lab; o onboard não foi alterado.
O modo fica em `ids_mode` no `_meta.json`; `untracked_frames` e `id_set_changes_delivered` medem a ocorrência.

## Fidelidade ao deploy (e onde o lab difere de propósito)

- Mesma sequência do `FrameWorker._handle`: throttle (1/FRAME_RATE) → `filter_observations`
  → `process` dos 3 modelos → `PersonRuntimeStore.cleanup` → `cleanup`. Testes de equivalência
  com o `FrameQueue` e o `FrameWorker` reais estão em `tests/`.
- Lote vazio (ninguém detectado num frame entregue) apaga o histórico de todos, como no vigia;
  cada ocorrência vai para `resets` no `_meta.json`.
- Os classificadores rodam **no mesmo laço do YOLO** (o vigia usa a thread `core-worker`):
  o custo vai em `classifier_ms_total` e `ui_ms_mean`. Não há backpressure por fila cheia.
- O GRU 37 (nosso) monta a janela numa grade de 10 fps por **timestamp**; o GRU 34 usa os
  frames entregues como o vigia.
- O timestamp é `time.time()` tirado DEPOIS do YOLO, como no deploy.

## Notas para outro assistente / chat

- **Não alterar `vigia-onboard/`.** Se for imprescindível, mudança mínima e retrocompatível,
  combinada com o Pedro. Nunca commitar/push sem aprovação do Erik.
- Verificado (testes + execução real; passo a passo e pendências em `COMO_USAR_NO_NOTEBOOK.md`): imports sem gate/SHM; kwargs via AST; export do YOLO;
  tracker reinicia com `model.predictor = None`; replay de vídeo ponta a ponta; 54 testes.
- **NÃO verificado ainda**: gravação com câmera real e interface com a Ana; se fechar o gerador
  libera a câmera no MSMF; custo do desenho da janela no fps; nota do operador (`n`) não foi
  implementada; fase 2 (reprocessamento offline a partir do vídeo/`_raw.npz`) não existe.
- O fps que chega aos classificadores é **quantizado pelo throttle** (período ≥ 1/12 s):
  câmera a 30 fps → 10/s; a 20 → 10/s; a 15 → 7,5/s. Anotar o fps entregue ao comparar takes.
- Janelas: o GRU 34 precisa de 20 frames entregues (~2 s), o Math de 30 (~3 s) e o GRU 37 de
  2 s de histórico; clipes curtos não geram decisão.
- `iou` não é passado pelo vigia → padrão do Ultralytics (0,7). Duplicatas com IoU≈0,66 podem aparecer.
- Se o YOLO não devolve `boxes.id`, o vigia usa `0,1,…` como `person_id` (pode colidir com IDs do tracker).
- Pontos a combinar com o Pedro: destino do `gru_2classes.onnx` (não está no onboard),
  PR opcional movendo `_YOLO_STREAM_KWARGS` para `capture/yolo_config.py`, reset de histórico em lote vazio.
- Textos da janela são ASCII (fontes do OpenCV não têm acentos).
