# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

spec_file = Path(SPECPATH).resolve()
root = spec_file.parent
for p in [root, *root.parents]:
    if (p / "pyproject.toml").is_file() and (p / "src" / "agentloom").is_dir():
        root = p
        break
script = root / "src" / "agentloom" / "__main__.py"

a = Analysis(
    [str(script)],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[],
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
    name="AgentLoom",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    name="AgentLoom",
)
