# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('config', 'config'), ('models', 'models'), ('controllers', 'controllers'), ('views', 'views'), ('utils', 'utils'), ('resources', 'resources'), ('ctk_design_system.py', '.')]
binaries = [('C:\\Users\\sergi\\PycharmProjects\\Farmatracker_2.0\\.venv\\Lib\\site-packages\\pywin32_system32\\pythoncom312.dll', '.'), ('C:\\Users\\sergi\\PycharmProjects\\Farmatracker_2.0\\.venv\\Lib\\site-packages\\pywin32_system32\\pywintypes312.dll', '.')]
hiddenimports = ['config', 'config.settings', 'models', 'models.database', 'controllers', 'controllers.dashboard', 'controllers.facturas', 'controllers.inventario', 'controllers.pedidos', 'controllers.ventas', 'views', 'views.actualizador_window', 'views.agregar_producto_window', 'views.backup_window', 'views.dashboard_panel', 'views.facturas_window', 'views.inventario_window', 'views.kit_window', 'views.liquidador_window', 'views.login_window', 'views.main_window', 'views.pedidos_window', 'views.pedido_centro_window', 'views.reporte_ventas_window', 'views.tension_window', 'views.venta_window', 'views.verificacion_window', 'utils', 'utils.backup', 'utils.formatters', 'utils.pdf_generator', 'utils.sip_extractor', 'utils.validators', 'resources', 'customtkinter', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'bcrypt', 'bcrypt._bcrypt', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'fpdf', 'fpdf.fpdf', 'pandas', 'openpyxl', 'pdfplumber', 'reportlab', 'reportlab.platypus', 'reportlab.lib.pagesizes', 'reportlab.lib.styles', 'reportlab.lib.colors', 'reportlab.lib.units', 'reportlab.pdfbase', 'reportlab.pdfbase.pdfmetrics', 'reportlab.pdfbase.ttfonts', 'reportlab.graphics.shapes', 'reportlab.graphics.barcode', 'reportlab.graphics.barcode.qr', 'tkcalendar', 'sqlite3', 'json', 'csv', 'calendar', 'decimal', 'win32print', 'win32ui', 'win32con', 'win32api', 'pywintypes']
tmp_ret = collect_all('customtkinter')
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
    excludes=['matplotlib', 'scipy', 'scikit-learn', 'sklearn', 'notebook', 'jupyter', 'IPython', 'pytest', 'unittest', 'test', '_pytest', 'setuptools', 'pip', 'wheel', 'pygments'],
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
