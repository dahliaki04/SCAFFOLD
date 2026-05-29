# -*- mode: python ; coding: utf-8 -*-
"""L1-33: PyInstaller Portable Build Spec.

Build command:
    pyinstaller scaffold.spec

Or equivalently:
    pyinstaller --noconfirm --onedir --windowed \\
        --collect-all ttkbootstrap \\
        --hidden-import pywin32 \\
        --hidden-import pythoncom \\
        --hidden-import orjson \\
        main.py

Output: dist/scaffold/ (portable folder, no installation required)
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all ttkbootstrap resources (themes.json, etc.) up-front so they go
# through Analysis normalization (PyInstaller 6.x rejects post-hoc 2-tuples).
ttkbootstrap_datas, ttkbootstrap_binaries, ttkbootstrap_hiddenimports = collect_all('ttkbootstrap')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=ttkbootstrap_binaries,
    datas=ttkbootstrap_datas,
    hiddenimports=[
        'orjson',
        'ttkbootstrap',
        'cryptography',
        'reportlab',
        # Windows-only: COM automation for xlwings
        'pythoncom',
        'win32com',
        'win32com.client',
    ] + ttkbootstrap_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test/dev packages from build
        'pytest',
        'hypothesis',
        'mypy',
        'black',
        'isort',
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
    name='scaffold',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX-packed binaries trigger AV false positives; safer to ship uncompressed
    console=False,  # Windowed mode (no console)
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
    upx=False,  # UPX-packed binaries trigger AV false positives; safer to ship uncompressed
    upx_exclude=[],
    name='scaffold',
)
