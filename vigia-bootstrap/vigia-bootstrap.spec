# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir — bundle linux/arm64 para /opt/vigia/bootstrap/

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

datas = []
binaries = []
hiddenimports = [
    *collect_submodules("provision"),
    *collect_submodules("ui"),
    "gpiozero",
    "lgpio",
    "RPLCD",
    "smbus2",
    "bless",
    "cryptography",
    "getmac",
    "dotenv",
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
        "IPython",
        "jupyter",
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
    name="vigia-bootstrap",
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
    name="vigia-bootstrap",
)
