# vigia-onboard-test (C++)

Protótipo de captura + YOLO pose em C++ (OpenCV + ONNX Runtime), espelho do
`vigia-onboard/vigia-capture` em Python.

Dependências **não** precisam estar instaladas no sistema:

| Dep | Como | Cache |
|-----|------|--------|
| OpenCV | **Conan 2** (`conanfile.txt`) | `~/.conan2` (como site-packages) |
| ONNX Runtime | zip oficial no CMake | `build/_deps/onnxruntime/` |

> ORT via Conan compilaria do fonte (abseil/protobuf/onnx/…) durante horas. O zip
> oficial da Microsoft é o equivalente a instalar uma wheel pré-compilada.

## Requisitos

- CMake 3.21+
- Visual Studio 2026 (ou Build Tools) com C++
- Python 3 + Conan 2: `python -m pip install --user "conan>=2,<3"`

## Setup (Conan ≈ venv)

Com GNU Make (atalho):

```powershell
cd vigia-onboard-test
make run              # .env + build incremental + executa
make build            # só compila
make CONFIG=Release run
make clean
```

Passo a passo manual:

```powershell
cd vigia-onboard-test

# 1) OpenCV → cache Conan (1ª vez pode compilar ~10–20 min; depois é instantâneo)
.\scripts\conan.ps1 install . -of build --build=missing `
  --profile:host=profiles/windows-msvc-debug `
  --profile:build=profiles/windows-msvc-debug

# 2) CMake (descarrega ORT automaticamente se faltar)
cmake -B build -S . `
  -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake `
  -DCMAKE_POLICY_DEFAULT_CMP0091=NEW `
  -DCMAKE_BUILD_TYPE=Debug

# 3) Build
cmake --build build --config Debug
```

No Cursor/VS Code: task **build: vigia-onboard-test** (Conan → CMake → build) ou
launch **Vigia.OnboardTest (C++)**.

O script [`scripts/conan.ps1`](scripts/conan.ps1) encontra o `conan.exe` do
`pip --user` mesmo fora do PATH.

Perfis em [`profiles/`](profiles/) fixam **MSVC 195 + gerador VS 18 2026** (a
máquina atual).

## Modelo ONNX

Reutiliza o artefato do onboard:

`../vigia-onboard/vigia-capture/models/yolo/yolo26s-pose.onnx`

## Run

```powershell
copy example.env .env   # se ainda não tiver
.\build\Debug\vigia-capture-cpp.exe
```

`q` fecha o preview. O launch do VS Code já define `cwd` + `envFile`.

## Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `CAPTURE_SOURCE` | `0` | Índice de câmera ou path de vídeo |
| `SHOW_VIDEO` | `false` | Preview OpenCV |
| `SHOW_YOLO_PLOT` | `false` | Desenhar boxes + skeleton |
| `CAPTURE_LOOP` | `false` | Repetir vídeo ao fim |
| `YOLO_MODEL` | `yolo26s-pose` | Stem ou path do `.onnx` |
| `YOLO_IMGSZ` | `320` | Usado se o artefato não fixar o input |
| `YOLO_CONF` | `0.25` | Limiar de confiança |

## Release

Repetir com `profiles/windows-msvc-release` e `--config Release`.
