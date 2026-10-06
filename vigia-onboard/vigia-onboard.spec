# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir — bundle linux/arm64 para /opt/vigia/onboard/
# Binário: vigia  (serviço systemd vigia.service, nome "Vigia")
# O NCNN entra em models/yolo/ na raiz do bundle (sys._MEIPASS), que é onde
# shared.yolo_export procura quando o executável está congelado.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

_NCNN = Path("capture/models/yolo/yolo26s-pose_ncnn_model")
if not (_NCNN / "model.ncnn.param").is_file() or not (_NCNN / "model.ncnn.bin").is_file():
    raise SystemExit(
        "ERRO: export NCNN em falta em capture/models/yolo/yolo26s-pose_ncnn_model. "
        "Corra make ensure-model antes do PyInstaller."
    )

datas = [
    (str(_NCNN), "models/yolo/yolo26s-pose_ncnn_model"),
]
binaries = []
hiddenimports = []

_gru = Path("core/models/gru_2classes.onnx")
if _gru.is_file():
    datas.append((str(_gru), "core/models"))

# pkg_resources → jaraco.* (namespaces; collect_submodules("jaraco") não basta).
for pkg in ("jaraco.text", "jaraco.functools", "jaraco.context"):
    try:
        jd, jb, jh = collect_all(pkg)
        datas += jd
        binaries += jb
        hiddenimports += jh
    except Exception:
        pass

try:
    ud, ub, uh = collect_all("ultralytics")
    datas += ud
    binaries += ub
    hiddenimports += uh
except Exception:
    hiddenimports += collect_submodules("ultralytics")

hiddenimports += [
    "capture",
    "core",
    "integration",
    "interface",
    "stream",
    "stream.mp_compat",
    "stream.rtmp",
    "stream.stream_runner",
    "stream.clips_runner",
    "shared",
    "shared.yolo_export",
    "pkg_resources",
    "cv2",
    "numpy",
    "PIL",
    "yaml",
    "dotenv",
    "loguru",
    "lap",
    "getmac",
    "paho.mqtt.client",
    "onnxruntime",
    "gpiozero",
    "lgpio",
    "RPLCD",
    "smbus2",
    "bless",
    *collect_submodules("interface"),
    *collect_submodules("core"),
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        # Não excluir "wheel": hooks do setuptools (PyInstaller recente) fazem
        # alias_module("wheel", ...) e falham se já estiver ExcludedModule.
        "IPython",
        "jupyter",
        "matplotlib.tests",
        "numpy.tests",
        "torch.utils.tensorboard",
        "sklearn",
        "joblib",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vigia",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="vigia",
)
