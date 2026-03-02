# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('controllers', 'controllers'), ('models', 'models'), ('views', 'views'), ('utils', 'utils'), ('config', 'config'), ('resources', 'resources'), ('ctk_design_system.py', '.')]
binaries = []
hiddenimports = ['controllers', 'controllers.dashboard', 'controllers.facturas', 'controllers.inventario', 'controllers.pedidos', 'controllers.ventas', 'models', 'models.database', 'views', 'views.actualizador_window', 'views.agregar_producto_window', 'views.backup_window', 'views.dashboard_panel', 'views.facturas_window', 'views.inventario_window', 'views.kit_window', 'views.liquidador_window', 'views.login_window', 'views.main_window', 'views.pedidos_window', 'views.pedido_centro_window', 'views.reporte_ventas_window', 'views.tension_window', 'views.venta_window', 'views.verificacion_window', 'utils', 'utils.backup', 'utils.formatters', 'utils.pdf_generator', 'utils.sip_extractor', 'utils.validators', 'config', 'config.settings', 'resources', 'customtkinter', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'bcrypt', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'fpdf', 'fpdf.fpdf', 'fpdf.fonts', 'fpdf.html', 'fpdf2', 'reportlab', 'reportlab.platypus', 'reportlab.lib.pagesizes', 'reportlab.lib.styles', 'reportlab.lib.units', 'reportlab.lib.colors', 'pandas', 'openpyxl', 'xlrd', 'tkcalendar', 'sqlite3', 'decimal', 'json', 'csv']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fpdf')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('reportlab')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('tkcalendar')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
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
    a.binaries,
    a.datas,
    [],
    name='FarmaTrack',
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
    icon=['resources\\icono.ico'],
)
