# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['server/training_server.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('generated', 'generated'),  
    ],
    hiddenimports=[
        'grpc',
        'grpc._cython.cygrpc',
        'google',
        'google.protobuf',
    ],
    excludes=[
        'matplotlib',                
        'numpy.random._pickle',
        'scipy',                      
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
    name='training_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='training_server',
)
