# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

spec_file = Path(SPECPATH).resolve()
root = spec_file.parent
for p in [root, *root.parents]:
    if (p / "pyproject.toml").is_file() and (p / "src" / "agentcrewchat").is_dir():
        root = p
        break
script = root / "src" / "agentcrewchat" / "__main__.py"
_res = root / "src" / "agentcrewchat" / "resources"
_datas = [(_res, "agentcrewchat/resources")] if _res.is_dir() else []

a = Analysis(
    [str(script)],
    pathex=[str(root / "src")],
    binaries=[],
    datas=_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "_pytest",
        "py",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AgentCrewChat",
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AgentCrewChat",
)
