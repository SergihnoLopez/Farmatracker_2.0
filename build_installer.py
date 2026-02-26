import os
import shutil
import subprocess
from pathlib import Path

# ==============================
# CONFIGURACIÓN
# ==============================

APP_NAME = "FarmaTrack"
APP_VERSION = "1.0"
MAIN_FILE = "main.py"
ICON_PATH = "resources/icono.ico"

# Base de datos por defecto
DB_FILE = "farma_pro_stocker.db"

# Ruta donde está instalado Inno Setup
INNO_COMPILER = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"


# ==============================
# LIMPIAR BUILDS ANTERIORES
# ==============================

def limpiar_builds():
    print("🧹 Limpiando builds anteriores...")

    for carpeta in [DIST_DIR, BUILD_DIR]:
        if carpeta.exists():
            shutil.rmtree(carpeta)

    spec_file = BASE_DIR / f"{APP_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()

    print("✅ Limpieza completada\n")


# ==============================
# GENERAR EJECUTABLE
# ==============================
def preparar_base_datos_instalador():
    print("📦 Preparando base de datos para instalador...")

    db_path = BASE_DIR / DB_FILE
    installer_db_dir = BASE_DIR / "installer_files"
    installer_db_dir.mkdir(exist_ok=True)

    if db_path.exists():
        shutil.copy2(db_path, installer_db_dir / DB_FILE)
        print("✅ Base de datos copiada para instalador\n")
    else:
        print("⚠ No se encontró database.db\n")
def generar_exe():
    print("⚙ Generando ejecutable con PyInstaller...")

    comando = [
        "pyinstaller",
        MAIN_FILE,
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--icon", ICON_PATH,
        "--add-data", "config;config",
        "--add-data", "models;models",
        "--add-data", "controllers;controllers",
        "--add-data", "views;views",
        "--add-data", "utils;utils",
        "--add-data", "resources;resources"
    ]

    subprocess.run(comando, check=True)

    print("✅ Ejecutable generado correctamente\n")


# ==============================
# GENERAR SCRIPT INNO SETUP
# ==============================

def generar_script_inno():
    print("📝 Generando script de instalador...")

    iss_content = f"""
[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
DefaultDirName={{pf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir=.
OutputBaseFilename={APP_NAME}_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\\{APP_NAME}.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "installer_files\\{DB_FILE}"; DestDir: "{{app}}\\default_db"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{commondesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "Ejecutar {APP_NAME}"; Flags: nowait postinstall skipifsilent
"""

    iss_path = BASE_DIR / "installer.iss"
    iss_path.write_text(iss_content, encoding="utf-8")

    print("✅ Script installer.iss creado\n")

    return iss_path


# ==============================
# COMPILAR INSTALADOR
# ==============================

def compilar_instalador(iss_path):
    print("📦 Compilando instalador con Inno Setup...")

    if not Path(INNO_COMPILER).exists():
        print("❌ No se encontró Inno Setup en la ruta configurada.")
        print("Modifica INNO_COMPILER en el script.")
        return

    subprocess.run([INNO_COMPILER, str(iss_path)], check=True)

    print("✅ Instalador generado correctamente\n")


# ==============================
# MAIN
# ==============================

def main():
    print("=" * 60)
    print("  BUILD AUTOMÁTICO - FARMA TRACK")
    print("=" * 60)
    print()

    limpiar_builds()
    generar_exe()
    preparar_base_datos_instalador()
    iss_path = generar_script_inno()
    compilar_instalador(iss_path)

    print("🎉 PROCESO COMPLETADO")


if __name__ == "__main__":
    main()