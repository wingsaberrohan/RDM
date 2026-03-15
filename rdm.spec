# PyInstaller spec for RDM - Rohan's Download Manager
# Usage: pyinstaller rdm.spec

import sys

block_cipher = None

# Bundle rdm package and resources
rdm_resources = []
try:
    from PyInstaller.utils.hooks import collect_data_files
    rdm_resources = collect_data_files('rdm', include_py_files=False)
except Exception:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=rdm_resources,
    hiddenimports=[
        'rdm',
        'rdm.app',
        'rdm.core',
        'rdm.core.aria2_manager',
        'rdm.core.rpc_client',
        'rdm.core.download_manager',
        'rdm.core.category',
        'rdm.core.clipboard_monitor',
        'rdm.core.scheduler',
        'rdm.core.speed_limiter',
        'rdm.core.browser_server',
        'rdm.db',
        'rdm.db.database',
        'rdm.db.models',
        'rdm.ui',
        'rdm.ui.main_window',
        'rdm.ui.download_table',
        'rdm.ui.add_download_dialog',
        'rdm.ui.settings_dialog',
        'rdm.ui.scheduler_dialog',
        'rdm.ui.batch_download_dialog',
        'rdm.ui.category_panel',
        'rdm.ui.themes',
        'rdm.ui.speed_widget',
        'rdm.ui.system_tray',
        'rdm.utils',
        'rdm.utils.file_utils',
        'rdm.utils.url_utils',
        'aria2p',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RDM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app: no terminal window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS: create .app bundle for DMG
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='RDM.app',
        icon=None,
        bundle_identifier='com.rdm.app',
        info_plist={
            'CFBundleName': 'RDM',
            'CFBundleDisplayName': 'RDM - Rohan\'s Download Manager',
            'CFBundleVersion': '0.1.0',
            'NSHighResolutionCapable': True,
        },
    )
