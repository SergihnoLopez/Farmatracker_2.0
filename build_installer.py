"""
BUILD AUTOMATICO - FarmaTrack
Genera ejecutable con PyInstaller + instalador con Inno Setup.

Dependencias obligatorias:
  pip install pyinstaller customtkinter bcrypt pillow fpdf2
  pip install pandas openpyxl reportlab pdfplumber tkcalendar

Dependencias opcionales:
  pip install pywin32 opencv-python xlrd
"""

import os
import sys
import glob
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime

# ==============================================================================
# CONFIGURACION
# ==============================================================================

APP_NAME = "FarmaTrack"
APP_VERSION = "1.1"
APP_PUBLISHER = "Drogueria Irlandesa"
MAIN_FILE = "main.py"
ICON_PATH = "resources/icono.ico"
DB_FILE = "farma_pro_stocker.db"

INNO_PATHS = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
INSTALLER_FILES_DIR = BASE_DIR / "installer_files"
LOG_DIR = BASE_DIR / "build_logs"

# Carpetas del proyecto que se empaquetan
CARPETAS_PROYECTO = ["config", "models", "controllers", "views", "utils", "resources"]

# Modulos que NO usa el proyecto -> excluir para reducir tamano
EXCLUDES = [
    "matplotlib", "scipy", "scikit-learn", "sklearn",
    "notebook", "jupyter", "IPython",
    "pytest", "unittest", "test", "_pytest",
    "setuptools", "pip", "wheel",
    "pygments",
]


# ==============================================================================
# LOG
# ==============================================================================

_log_lines = []


def _log(prefix, texto):
    linea = f"  {prefix} {texto}"
    print(linea)
    _log_lines.append(linea)


def _titulo(texto):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {texto}")
    print(sep)
    _log_lines.append(f"\n{texto}")


def _ok(texto):     _log("[OK]", texto)
def _warn(texto):   _log("[!!]", texto)
def _error(texto):  _log("[XX]", texto)
def _info(texto):   _log("[..]", texto)


def guardar_log():
    """Guarda el log del build en un archivo."""
    LOG_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"build_{ts}.log"
    log_path.write_text("\n".join(_log_lines), encoding="utf-8")
    _ok(f"Log guardado: {log_path.name}")


def encontrar_inno():
    for ruta in INNO_PATHS:
        if Path(ruta).exists():
            return ruta
    return None


def _tiempo(inicio):
    seg = time.time() - inicio
    if seg < 60:
        return f"{seg:.0f}s"
    return f"{seg / 60:.1f}min"


# ==============================================================================
# PASO 1 - DETECTAR MODULOS DEL PROYECTO AUTOMATICAMENTE
# ==============================================================================

def detectar_modulos_proyecto():
    """Escanea las carpetas del proyecto y devuelve hidden imports reales."""
    modulos = []
    for carpeta in CARPETAS_PROYECTO:
        ruta = BASE_DIR / carpeta
        if not ruta.is_dir():
            continue
        modulos.append(carpeta)
        for py in ruta.glob("*.py"):
            if py.stem == "__init__":
                continue
            modulos.append(f"{carpeta}.{py.stem}")
    return modulos


# ==============================================================================
# PASO 2 - VERIFICAR ENTORNO
# ==============================================================================

def verificar_entorno():
    _titulo("PASO 1 - VERIFICANDO ENTORNO")

    errores = []
    v = sys.version.split()[0]
    _info(f"Python {v}")

    # PyInstaller
    try:
        import PyInstaller
        _ok(f"PyInstaller {PyInstaller.__version__}")
    except ImportError:
        _error("PyInstaller no instalado -> pip install pyinstaller")
        errores.append("pyinstaller")

    # Dependencias obligatorias
    deps = [
        ("customtkinter",  "customtkinter"),
        ("bcrypt",          "bcrypt"),
        ("PIL",             "pillow"),
        ("fpdf",            "fpdf2"),
        ("pandas",          "pandas"),
        ("openpyxl",        "openpyxl"),
        ("reportlab",       "reportlab"),
        ("pdfplumber",      "pdfplumber"),
        ("tkcalendar",      "tkcalendar"),
    ]

    deps_opcionales = [
        ("cv2",         "opencv-python",  "Video en login"),
        ("win32print",  "pywin32",        "Impresion directa Windows"),
        ("xlrd",        "xlrd",           "Lectura .xls antiguos"),
    ]

    for mod, pkg in deps:
        try:
            __import__(mod)
            _ok(pkg)
        except ImportError:
            _error(f"{pkg} -> pip install {pkg}")
            errores.append(pkg)

    for mod, pkg, desc in deps_opcionales:
        try:
            __import__(mod)
            _ok(f"{pkg} ({desc})")
        except ImportError:
            _warn(f"{pkg} no instalado - {desc}")

    # Inno Setup
    inno = encontrar_inno()
    if inno:
        _ok("Inno Setup 6")
    else:
        _warn("Inno Setup no encontrado (solo se generara el .exe)")

    # Archivos criticos
    if not (BASE_DIR / MAIN_FILE).exists():
        _error(f"{MAIN_FILE} no encontrado")
        errores.append(MAIN_FILE)

    for carpeta in CARPETAS_PROYECTO:
        if not (BASE_DIR / carpeta).is_dir():
            _error(f"Carpeta {carpeta}/ no encontrada")
            errores.append(carpeta)

    if errores:
        _error(f"Faltantes: {', '.join(errores)}")
        return False

    _ok("Entorno listo")
    return True


# ==============================================================================
# PASO 2 - LIMPIAR BUILDS ANTERIORES
# ==============================================================================

def limpiar_builds():
    _titulo("PASO 2 - LIMPIANDO BUILDS ANTERIORES")

    n = 0
    for carpeta in [DIST_DIR, BUILD_DIR, INSTALLER_FILES_DIR]:
        if carpeta.exists():
            shutil.rmtree(carpeta)
            n += 1
    for patron in ["*.spec", "installer.iss"]:
        for f in BASE_DIR.glob(patron):
            f.unlink()
            n += 1
    _ok(f"Eliminados: {n} elementos")


# ==============================================================================
# PASO 3 - PREPARAR ARCHIVOS
# ==============================================================================

def preparar_archivos_instalador():
    _titulo("PASO 3 - PREPARANDO ARCHIVOS")

    INSTALLER_FILES_DIR.mkdir(exist_ok=True)

    # Base de datos
    db_path = BASE_DIR / DB_FILE
    if db_path.exists():
        shutil.copy2(db_path, INSTALLER_FILES_DIR / DB_FILE)
        mb = db_path.stat().st_size / (1024 * 1024)
        _ok(f"Base de datos ({mb:.1f} MB)")
    else:
        _warn(f"{DB_FILE} no encontrado")

    # ctk_design_system.py
    ctk_ds = BASE_DIR / "ctk_design_system.py"
    if ctk_ds.exists():
        _ok("ctk_design_system.py")
    else:
        _warn("ctk_design_system.py no encontrado")

    # Fuentes e icono
    resources = BASE_DIR / "resources"
    if resources.is_dir():
        fuentes = list(resources.glob("*.ttf")) + list(resources.glob("*.TTF"))
        if fuentes:
            _ok(f"Fuentes TTF: {len(fuentes)}")
        if (resources / "icono.ico").exists():
            _ok("Icono: icono.ico")

    # Detectar modulos
    modulos = detectar_modulos_proyecto()
    _ok(f"Modulos del proyecto: {len(modulos)}")

    return modulos


# ==============================================================================
# PASO 4 - GENERAR EJECUTABLE
# ==============================================================================

def generar_exe(modulos_proyecto):
    _titulo("PASO 4 - GENERANDO EJECUTABLE")
    t0 = time.time()

    sep = ";" if os.name == "nt" else ":"

    cmd = [
        "pyinstaller", MAIN_FILE,
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
    ]

    # Icono
    if (BASE_DIR / ICON_PATH).exists():
        cmd += ["--icon", ICON_PATH]

    # Carpetas del proyecto como datos
    for carpeta in CARPETAS_PROYECTO:
        if (BASE_DIR / carpeta).is_dir():
            cmd += ["--add-data", f"{carpeta}{sep}{carpeta}"]

    # ctk_design_system.py en raiz
    if (BASE_DIR / "ctk_design_system.py").exists():
        cmd += ["--add-data", f"ctk_design_system.py{sep}."]

    # Exclusiones para reducir tamano
    for mod in EXCLUDES:
        cmd += ["--exclude-module", mod]

    # Hidden imports del proyecto (detectados automaticamente)
    for mod in modulos_proyecto:
        cmd += ["--hidden-import", mod]

    # Hidden imports de dependencias externas (try/except en el codigo)
    deps_hidden = [
        "customtkinter",
        "tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.filedialog",
        "bcrypt", "bcrypt._bcrypt",
        "PIL", "PIL.Image", "PIL.ImageTk",
        "fpdf", "fpdf.fpdf",
        "pandas", "openpyxl", "pdfplumber",
        "reportlab", "reportlab.platypus",
        "reportlab.lib.pagesizes", "reportlab.lib.styles",
        "reportlab.lib.colors", "reportlab.lib.units",
        "reportlab.pdfbase", "reportlab.pdfbase.pdfmetrics",
        "reportlab.pdfbase.ttfonts",
        "reportlab.graphics.shapes",
        "reportlab.graphics.barcode", "reportlab.graphics.barcode.qr",
        "tkcalendar",
        "sqlite3", "json", "csv", "calendar", "decimal",
        # Impresion Windows
        "win32print", "win32ui", "win32con", "win32api", "pywintypes",
    ]

    added = 0
    for mod in deps_hidden:
        root = mod.split(".")[0]
        try:
            __import__(root)
            cmd += ["--hidden-import", mod]
            added += 1
        except ImportError:
            pass

    _ok(f"Hidden imports: {len(modulos_proyecto)} proyecto + {added} dependencias")

    # Collect-all para paquetes con assets internos
    for pkg in ["customtkinter", "reportlab", "tkcalendar"]:
        try:
            __import__(pkg)
            cmd += ["--collect-all", pkg]
        except ImportError:
            pass

    # pywin32 DLLs para impresion
    try:
        import importlib.util
        spec = importlib.util.find_spec("win32print")
        if spec and spec.origin:
            win32_dir = Path(spec.origin).parent
            sys32 = win32_dir.parent / "pywin32_system32"
            if sys32.is_dir():
                dlls = list(sys32.glob("*.dll"))
                for dll in dlls:
                    cmd += ["--add-binary", f"{dll}{sep}."]
                _ok(f"DLLs pywin32: {len(dlls)} (impresion Windows)")
    except Exception:
        _warn("pywin32 no disponible")

    _info(f"Total args PyInstaller: {len(cmd)}")
    print(f"\n  Compilando... (1-3 minutos)\n")

    # Ejecutar PyInstaller con log a archivo
    LOG_DIR.mkdir(exist_ok=True)
    log_pyinstaller = LOG_DIR / "pyinstaller_output.log"

    with open(log_pyinstaller, "w", encoding="utf-8") as logf:
        resultado = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    # Leer log y mostrar solo lo relevante
    log_text = log_pyinstaller.read_text(encoding="utf-8", errors="replace")
    errores_encontrados = False
    for linea in log_text.splitlines():
        ll = linea.lower()
        if "error" in ll and "info" not in ll and "hook-" not in ll:
            print(f"    {linea}")
            errores_encontrados = True

    if resultado.returncode != 0:
        _error(f"PyInstaller fallo (codigo {resultado.returncode})")
        _info(f"Log completo: {log_pyinstaller}")
        if not errores_encontrados:
            print("\n  Ultimas 10 lineas:")
            for linea in log_text.splitlines()[-10:]:
                print(f"    {linea}")
        return False

    # Verificar exe
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if exe_path.exists():
        mb = exe_path.stat().st_size / (1024 * 1024)
        _ok(f"{exe_path.name} - {mb:.1f} MB ({_tiempo(t0)})")
        _info(f"Log PyInstaller: {log_pyinstaller}")
        return True
    else:
        _error("Ejecutable no encontrado en dist/")
        return False


# ==============================================================================
# PASO 5 - GENERAR SCRIPT INNO SETUP
# ==============================================================================

def generar_iss():
    """Genera installer.iss limpio, sin f-strings problematicos."""

    db_en_installer = (INSTALLER_FILES_DIR / DB_FILE).exists()
    icon_existe = (BASE_DIR / ICON_PATH).exists()

    L = []  # lineas del .iss

    # Cabecera
    L.append("; Instalador " + APP_NAME + " v" + APP_VERSION)
    L.append("; Generado por build_installer.py - " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    L.append("")

    # [Setup]
    L.append("[Setup]")
    L.append("AppName=" + APP_NAME)
    L.append("AppVersion=" + APP_VERSION)
    L.append("AppPublisher=" + APP_PUBLISHER)
    L.append("DefaultDirName={autopf}\\" + APP_NAME)
    L.append("DefaultGroupName=" + APP_NAME)
    L.append("OutputDir=.")
    L.append("OutputBaseFilename=" + APP_NAME + "_Installer_v" + APP_VERSION)
    L.append("Compression=lzma2/ultra64")
    L.append("SolidCompression=yes")
    L.append("WizardStyle=modern")
    L.append("PrivilegesRequired=lowest")
    L.append("UninstallDisplayIcon={app}\\" + APP_NAME + ".exe")
    L.append("DisableProgramGroupPage=yes")
    if icon_existe:
        L.append("SetupIconFile=" + ICON_PATH)
    L.append("")

    # [Languages]
    L.append("[Languages]")
    L.append('Name: "spanish"; MessagesFile: "compiler:Languages\\Spanish.isl"')
    L.append('Name: "english"; MessagesFile: "compiler:Default.isl"')
    L.append("")

    # [Tasks] - SIN flag Flags:checked (causa error en Inno 6.7+)
    L.append("[Tasks]")
    L.append('Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Opciones adicionales:"')
    L.append("")

    # [Files]
    L.append("[Files]")
    L.append('Source: "dist\\' + APP_NAME + '.exe"; DestDir: "{app}"; Flags: ignoreversion')
    if db_en_installer:
        L.append('Source: "installer_files\\' + DB_FILE + '"; DestDir: "{app}\\default_db"; Flags: ignoreversion')
    L.append("")

    # [Icons]
    L.append("[Icons]")
    L.append('Name: "{group}\\' + APP_NAME + '"; Filename: "{app}\\' + APP_NAME + '.exe"')
    L.append('Name: "{autodesktop}\\' + APP_NAME + '"; Filename: "{app}\\' + APP_NAME + '.exe"; Tasks: desktopicon')
    L.append("")

    # [Run]
    L.append("[Run]")
    L.append('Filename: "{app}\\' + APP_NAME + '.exe"; Description: "Ejecutar ' + APP_NAME + '"; Flags: nowait postinstall skipifsilent')
    L.append("")

    # [UninstallDelete]
    L.append("[UninstallDelete]")
    L.append('Type: filesandordirs; Name: "{localappdata}\\' + APP_NAME + '\\logs"')
    L.append("")

    # Escribir con BOM para Inno Setup y CRLF
    iss_path = BASE_DIR / "installer.iss"
    iss_content = "\r\n".join(L)
    iss_path.write_text(iss_content, encoding="utf-8-sig")

    return iss_path


# ==============================================================================
# PASO 6 - COMPILAR INSTALADOR
# ==============================================================================

def compilar_instalador():
    _titulo("PASO 5 - GENERANDO INSTALADOR")

    iss_path = generar_iss()
    _ok("installer.iss generado")

    inno = encontrar_inno()
    if not inno:
        _warn("Inno Setup no encontrado")
        _info("Descargalo de: https://jrsoftware.org/isdl.php")
        _info("El .exe esta listo en: dist/" + APP_NAME + ".exe")
        return False

    _info("Compilando con Inno Setup...")

    log_inno = LOG_DIR / "inno_output.log"
    with open(log_inno, "w", encoding="utf-8") as logf:
        resultado = subprocess.run(
            [inno, str(iss_path)],
            cwd=str(BASE_DIR),
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    if resultado.returncode != 0:
        log_text = log_inno.read_text(encoding="utf-8", errors="replace")
        _error("Inno Setup fallo:")
        for linea in log_text.splitlines():
            if "error" in linea.lower() or "Error" in linea:
                print(f"    {linea}")
        _info(f"Log completo: {log_inno}")
        return False

    installer_name = APP_NAME + "_Installer_v" + APP_VERSION + ".exe"
    installer_path = BASE_DIR / installer_name
    if installer_path.exists():
        mb = installer_path.stat().st_size / (1024 * 1024)
        _ok(f"{installer_name} - {mb:.1f} MB")
        return True

    _error("Instalador no generado")
    return False


# ==============================================================================
# PASO 6 - VERIFICACION POST-BUILD
# ==============================================================================

def verificar_build():
    _titulo("VERIFICACION POST-BUILD")

    ok = True

    # Verificar exe
    exe = DIST_DIR / (APP_NAME + ".exe")
    if exe.exists():
        mb = exe.stat().st_size / (1024 * 1024)
        if mb < 5:
            _warn(f"Exe muy pequeno ({mb:.1f} MB) - puede faltar contenido")
            ok = False
        else:
            _ok(f"Ejecutable: {mb:.1f} MB")
    else:
        _error("Ejecutable no encontrado")
        ok = False

    # Verificar instalador
    installer = BASE_DIR / (APP_NAME + "_Installer_v" + APP_VERSION + ".exe")
    if installer.exists():
        mb = installer.stat().st_size / (1024 * 1024)
        _ok(f"Instalador: {mb:.1f} MB")
    else:
        _info("Instalador no generado (solo exe portable)")

    return ok


# ==============================================================================
# RESUMEN FINAL
# ==============================================================================

def resumen_final(t_total):
    _titulo("RESUMEN")

    exe = DIST_DIR / (APP_NAME + ".exe")
    installer = BASE_DIR / (APP_NAME + "_Installer_v" + APP_VERSION + ".exe")

    print()
    if exe.exists():
        mb = exe.stat().st_size / (1024 * 1024)
        _ok(f"Ejecutable:  dist/{APP_NAME}.exe  ({mb:.1f} MB)")
    else:
        _error("Ejecutable no generado")

    if installer.exists():
        mb = installer.stat().st_size / (1024 * 1024)
        _ok(f"Instalador:  {installer.name}  ({mb:.1f} MB)")

    print(f"\n  Tiempo total: {_tiempo(t_total)}")
    print()
    print("  DISTRIBUCION")
    print("  " + "-" * 56)
    print("  BD usuario:     %APPDATA%\\FarmaTrack\\")
    print("  Logs:           %APPDATA%\\FarmaTrack\\logs\\")
    print("  Impresion:      Usa impresoras de Windows")
    print("                  (termica, laser, PDF virtual, etc.)")
    print("  Portable:       dist\\FarmaTrack.exe funciona sin instalar")
    print("  " + "-" * 56)
    print()


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    t_total = time.time()

    print()
    print("  " + "=" * 56)
    print(f"  {APP_NAME} v{APP_VERSION} - {APP_PUBLISHER}")
    print("  Build: EXE + Instalador Windows")
    print("  " + "=" * 56)
    print()

    # 1. Verificar entorno
    if not verificar_entorno():
        _error("BUILD CANCELADO")
        guardar_log()
        sys.exit(1)

    # 2. Limpiar
    limpiar_builds()

    # 3. Preparar archivos y detectar modulos
    modulos = preparar_archivos_instalador()

    # 4. Generar exe
    if not generar_exe(modulos):
        _error("BUILD FALLO en PyInstaller")
        guardar_log()
        sys.exit(1)

    # 5. Generar instalador
    compilar_instalador()

    # 6. Verificacion post-build
    verificar_build()

    # 7. Resumen
    resumen_final(t_total)

    # Guardar log
    guardar_log()

    print("  BUILD COMPLETADO")
    print()


if __name__ == "__main__":
    main()