# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['SelfRemembering.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons/selfremembering.ico', 'icons'),
        ('quotes.json', '.'),
        ('sounds/tibetanbowl.mp3', 'sounds'),
        ('icons/picture.jpg', 'icons')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SelfRemembering',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
