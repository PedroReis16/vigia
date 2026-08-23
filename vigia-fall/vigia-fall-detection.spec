# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir — bundle linux/arm64 para /opt/vigia/fall-detection/

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas = [
    ("yolo26s-pose.pt", "."),
    ("model/gru_2classes.onnx", "model"),
]
binaries = []
hiddenimports = []

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
    "capture",
    "connection",
    "database",
    "integration",
    "shared",
    "shared.bundle_paths",
    *collect_submodules("ultralytics"),
    "pkg_resources",
    "cv2",
    "numpy",
    "PIL",
    "yaml",
    "dotenv",
    "loguru",
    "getmac",
    "cryptography",
    "paho.mqtt.client",
    "onnxruntime",
    "capture.classifiers",
    "capture.models.gru_classifier",
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
