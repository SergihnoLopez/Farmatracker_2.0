"""
BUILD AUTOMATICO - FarmaTrack 2.0
Genera EXE con PyInstaller y crea instalador con Inno Setup 6
Incluye soporte completo para fpdf / fpdf2
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ==========================================================
# CONFIGURACION
# ==========================================================

APP_NAME = "FarmaTrack"
APP_VERSION = "2.0"
APP_PUBLISHER = "Drogueria Irlandesa"

MAIN_FILE = "main.py"
DB_FILE = "farma_pro_stocker.db"
ICON_PATH = "resources/icono.ico"

PROJECT_FOLDERS = [
    "controllers",
    "models",
    "views",
    "utils",
    "config",
    "resources"
]

INNO_PATHS = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe"
]

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"

# ==========================================================
# UTILIDADES
# ==========================================================

def log(msg):
    print(f"[INFO] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")

def clean_previous_build():
    log("Limpiando builds anteriores...")

    for folder in [DIST_DIR, BUILD_DIR]:
        if folder.exists():
            shutil.rmtree(folder)

    for file in BASE_DIR.glob("*.spec"):
        file.unlink()

    iss = BASE_DIR / "installer.iss"
    if iss.exists():
        iss.unlink()

    log("Build limpio.")


def find_inno():
    for path in INNO_PATHS:
        if Path(path).exists():
            return path
    return None


def detect_project_modules():
    modules = []
    for folder in PROJECT_FOLDERS:
        folder_path = BASE_DIR / folder
        if folder_path.exists():
            modules.append(folder)
            for py in folder_path.glob("*.py"):
                if py.stem != "__init__":
                    modules.append(f"{folder}.{py.stem}")
    return modules


# ==========================================================
# PYINSTALLER
# ==========================================================

def build_exe():
    log("Generando ejecutable con PyInstaller...")

    modules = detect_project_modules()
    sep = ";" if os.name == "nt" else ":"

    cmd = [
        "pyinstaller",
        MAIN_FILE,
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm"
    ]

    if (BASE_DIR / ICON_PATH).exists():
        cmd += ["--icon", ICON_PATH]

    # Agregar carpetas del proyecto
    for folder in PROJECT_FOLDERS:
        if (BASE_DIR / folder).exists():
            cmd += ["--add-data", f"{folder}{sep}{folder}"]

    # Archivos sueltos en raíz
    if (BASE_DIR / "ctk_design_system.py").exists():
        cmd += ["--add-data", f"ctk_design_system.py{sep}."]

    # Hidden imports internos
    for mod in modules:
        cmd += ["--hidden-import", mod]

    # Dependencias externas críticas
    hidden_imports = [

        # UI
        "customtkinter",
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",

        # Seguridad
        "bcrypt",

        # Imagen
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",

        # PDF - FPDF / FPDF2
        "fpdf",
        "fpdf.fpdf",
        "fpdf.fonts",
        "fpdf.html",
        "fpdf2",

        # Reportlab
        "reportlab",
        "reportlab.platypus",
        "reportlab.lib.pagesizes",
        "reportlab.lib.styles",
        "reportlab.lib.units",
        "reportlab.lib.colors",

        # Excel / datos
        "pandas",
        "openpyxl",
        "xlrd",

        # Otros
        "tkcalendar",
        "sqlite3",
        "decimal",
        "json",
        "csv"
    ]

    for h in hidden_imports:
        cmd += ["--hidden-import", h]

    # Collect-all para paquetes con assets internos
    cmd += ["--collect-all", "customtkinter"]
    cmd += ["--collect-all", "fpdf"]
    cmd += ["--collect-all", "reportlab"]
    cmd += ["--collect-all", "tkcalendar"]

    log("Compilando... puede tardar 1-3 minutos.")
    subprocess.run(cmd, cwd=BASE_DIR)

    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if exe_path.exists():
        log(f"EXE generado correctamente: {exe_path}")
        return True
    else:
        error("No se generó el ejecutable.")
        return False


# ==========================================================
# GENERAR INSTALLER.ISS
# ==========================================================

def generate_iss():
    log("Generando installer.iss...")

    iss_content = f"""
[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
AppPublisher={APP_PUBLISHER}
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir=.
OutputBaseFilename={APP_NAME}_Installer_v{APP_VERSION}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={{app}}\\{APP_NAME}.exe
SetupIconFile={ICON_PATH}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Opciones adicionales:"

[Files]
Source: "dist\\{APP_NAME}.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{DB_FILE}"; DestDir: "{{app}}\\default_db"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{autodesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "Ejecutar {APP_NAME}"; Flags: nowait postinstall skipifsilent
"""

    iss_path = BASE_DIR / "installer.iss"
    iss_path.write_text(iss_content, encoding="utf-8-sig")
    return iss_path


# ==========================================================
# COMPILAR INSTALADOR
# ==========================================================

def build_installer():
    inno = find_inno()

    if not inno:
        error("Inno Setup no encontrado.")
        print("Descargar desde: https://jrsoftware.org/isdl.php")
        return

    iss = generate_iss()

    log("Compilando instalador con Inno Setup...")
    subprocess.run([inno, str(iss)], cwd=BASE_DIR)

    log("Instalador generado correctamente.")


# ==========================================================
# MAIN
# ==========================================================

def main():
    print("=" * 60)
    print("BUILD AUTOMATICO FARMA TRACK 2.0")
    print("=" * 60)

    clean_previous_build()

    if not build_exe():
        return

    build_installer()

    print("\nProceso finalizado correctamente.")


if __name__ == "__main__":
    main()