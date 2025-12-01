# dashboard_client.spec
# PyInstaller spec file for Flask Dashboard Client

block_cipher = None

a = Analysis(
    ['client/web_dashboard.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),   # Flask HTML templates
        ('generated', 'generated'),   # protobuf generated files
    ],
    hiddenimports=[
        'grpc',
        'grpc._cython.cygrpc',
        'google',
        'google.protobuf',
        'flask',
        'flask_cors',
    ],
    excludes=[
        'matplotlib',                # ✅ prevent NumPy ABI crash
        'scipy',                     # safe if unused
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # set False later if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='dashboard',
)
