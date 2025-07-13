# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Main.py'],
    pathex=['c:\\Github\\AutoPaperSearch'],  # 确保这是您的项目根目录
    binaries=[],
    datas=[
        ('config.json', '.'),  # 配置文件
        ('language/', 'language/'),   # 语言文件夹
        ('lib/', 'lib/'),   # lib目录及其所有子目录
        ('icon/icon.ico', 'icon/'),  # 图标文件
    ],
    hiddenimports=[
        'openai',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'json',
        'threading',
        'concurrent.futures',
        'requests',
        'bibtexparser',
        'language',
        'language.language',
        'lib.config.config_loader',
        'lib.load_data.load_api_keys',
        'lib.load_data.load_paper',
        'lib.process.paper_processor',
        'lib.ui.ui',
        'lib.log.utils',
        'lib.price.price',
        'lib.tools.txt_to_bib_converter'
    ],  # 根据项目依赖添加隐藏导入
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