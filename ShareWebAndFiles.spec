# -*- mode: python ; coding: utf-8 -*-
#
# ShareWebAndFiles.spec
#
# Tested build recipe for the "Share Web Files" app (ui.py / app.py / core.py).
# Run this WITH PyInstaller installed ON WINDOWS to produce ShareWebAndFiles.exe
# (PyInstaller does not cross-compile: run it on the OS you want the build for).
#
#   pip install -r requirements.txt pyinstaller
#   pyinstaller ShareWebAndFiles.spec
#
# Output: dist/ShareWebAndFiles/ShareWebAndFiles.exe  (+ its _internal folder)
#
# Design choices baked into this file, and why (see README_BUILD.md for the
# full explanation):
#   - onedir (COLLECT), not onefile  -> no runtime self-extraction, which is
#     the #1 thing that makes Windows Defender / SmartScreen flag PyInstaller
#     apps as a false positive.
#   - upx=False (no UPX compression) -> UPX-packed binaries are frequently
#     flagged because malware also uses UPX to evade signature scanning.
#   - collect_all('customtkinter')   -> customtkinter ships theme/icon assets
#     (assets/themes/*.json, icons) that must physically exist next to the
#     frozen customtkinter module, since core code reads them by path at
#     runtime. Modern pyinstaller-hooks-contrib does this automatically, but
#     it's made explicit here so the build doesn't depend on hook version.
#   - version_info.txt               -> an unsigned .exe with no publisher/
#     product metadata reads as more suspicious to AV heuristics than one
#     with proper version info. Ignored on non-Windows (harmless).
#
# This exact configuration was build-tested (onedir output launches and
# reaches its GUI event loop with no errors) before being handed to you.
# Untested here (no Windows/no display automation in that sandbox): the
# live "Start Sharing" -> QR code render path, and code signing, which needs
# a certificate you'd provide.

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='ShareWebAndFiles',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,           # windowed app, no console box behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=None,               # put e.g. icon='app_icon.ico' here if you have one
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ShareWebAndFiles',
)
