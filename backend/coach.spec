# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para o CoachApp.
Gera uma pasta one-dir em dist/CoachApp/.
"""
import customtkinter
import os

ctk_path = os.path.dirname(customtkinter.__file__)

block_cipher = None

a = Analysis(
    ["coach_app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("config.json", "."),
        ("../mvpgg.png", "."),
        (ctk_path, "customtkinter"),
    ],
    hiddenimports=[
        "pystray._win32",
        "PIL._imagingtk",
        "PIL.Image",
        "PIL.ImageDraw",
        "mss.windows",
        "httpx",
        "app_config",
        "tray_icon",
        "live_coach",
        "live_game_client",
        "minimap_capture",
        "event_bus",
        "settings",
        "db",
        "schemas",
        "customtkinter",
        "winsound",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "scipy"],
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
    name="MVPApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MVPApp",
)
