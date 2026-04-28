# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['coach_app.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.'), ('..\\mvpgg.png', '.')],
    hiddenimports=['pystray._win32', 'PIL._imagingtk', 'PIL.Image', 'PIL.ImageDraw', 'mss.windows', 'httpx', 'app_config', 'tray_icon', 'live_coach', 'live_game_client', 'minimap_capture', 'event_bus', 'settings', 'db', 'schemas', 'customtkinter', 'winsound'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MVPApp',
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
