# -*- mode: python ; coding: utf-8 -*-
# onefile (padrão local): `make build` — exige muita RAM no link final (torch).
# onedir (Docker): PYINSTALLER_ONEDIR=1 — pico de memória menor; use no Makefile linux/arm64.

import os

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_submodules

block_cipher = None
onedir = os.environ.get("PYINSTALLER_ONEDIR", "").strip() in ("1", "true", "yes")

datas = [("model/classifier_svm.onnx", "model")]
binaries = []
hiddenimports = []

# Bibliotecas nativas indispensáveis (evita collect_all completo de torch).
for pkg in ("onnxruntime",):
    try:
        binaries += collect_dynamic_libs(pkg)
    except Exception:
        pass

# pkg_resources → jaraco.* (namespaces; collect_submodules("jaraco") não basta).
for pkg in ("jaraco.text", "jaraco.functools", "jaraco.context"):
    try:
        jd, jb, jh = collect_all(pkg)
        datas += jd
        binaries += jb
        hiddenimports += jh
    except Exception:
        pass

hiddenimports += [
    *collect_submodules("ultralytics"),
    "pkg_resources",
    "cv2",
    "pandas",
    "pandas.plotting",
    "numpy",
    "PIL",
    "yaml",
    "multipart",
    "paho.mqtt.client",
    "aiohttp",
    "dotenv",
    "schedule",
    "loguru",
    "zmq",
]

a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "wheel",
        "IPython",
        "jupyter",
        "matplotlib.tests",
        "numpy.tests",
        "pandas.tests",
        # Não excluir torch.distributed nem torch.testing (cadeia de import do torch).
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

if onedir:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="vigia-fall-detection",
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
        name="vigia-fall-detection",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="vigia-fall-detection",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
