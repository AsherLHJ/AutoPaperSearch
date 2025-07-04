# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Main.py'],
    pathex=['c:\\Github\\AutoPaperSearch'],  # 确保这是您的项目根目录
    binaries=[],
    datas=[
        ('config.json', '.'),  # 配置文件
        ('language/', 'language/'),   # 语言文件夹
        ('lib/*.py', 'lib/'),   # lib目录下的所有Python文件
        ('icon/icon.ico', 'icon/'),  # 图标文件
    ],
    hiddenimports=['openai'],  # 根据install_requirements.py中的依赖
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
    name='AutoPaperSearch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为True以显示控制台窗口，便于查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/icon.ico',  # 添加图标
)