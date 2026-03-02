"""
Configuración central de la aplicación
✅ MIGRADO A CUSTOMTKINTER
✅ CORREGIDO PARA INSTALADOR WINDOWS
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path

# ==============================================================================
# 📁 RUTAS
# ==============================================================================

APP_NAME = "FarmaTrack"
DB_FILE = "farma_pro_stocker.db"

# 📌 Carpeta escribible del usuario (AppData)
APPDATA_DIR = Path(os.getenv("APPDATA")) / APP_NAME
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# 📌 Recursos siguen en carpeta del programa
BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / "resources"

# 📌 Base de datos:
#    - Desarrollo (PyCharm/script): usa la DB de la raíz del proyecto directamente
#    - Producción (.exe instalado):  usa AppData para no requerir permisos de escritura
if getattr(sys, 'frozen', False):
    DB_PATH = APPDATA_DIR / DB_FILE   # exe instalado → AppData
else:
    DB_PATH = BASE_DIR / DB_FILE      # desarrollo → raíz del proyecto

# 📌 Logs en AppData
LOGS_DIR = APPDATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# ==============================================================================
# 🛡 SISTEMA SEGURO DE COPIA DE BASE
# ==============================================================================

def copiar_base_si_no_existe():
    """
    En desarrollo: no hace nada (DB_PATH ya apunta a la raíz del proyecto).
    En producción (.exe): copia la BD desde default_db/ a AppData si no existe.
    """
    if not getattr(sys, 'frozen', False):
        # Desarrollo: DB_PATH = raíz del proyecto, no hay nada que copiar
        if not DB_PATH.exists():
            print("ℹ️  DB no encontrada en raíz del proyecto — se creará vacía.")
        return

    # Producción: copiar desde default_db/ a AppData si no existe con datos
    if DB_PATH.exists() and DB_PATH.stat().st_size > 8192:
        return  # ya tiene datos reales

    origen = Path(sys.executable).parent / "default_db" / DB_FILE
    if origen.exists():
        shutil.copy2(origen, DB_PATH)
        print("✅ BD copiada desde default_db/")
    else:
        print("ℹ️  default_db no encontrada — se creará BD vacía en AppData.")


def copiar_base_original():
    """
    Copia la base original incluida en el instalador
    hacia AppData.
    """

    # Detectar si corre como exe
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = BASE_DIR

    origen = base_path / "default_db" / DB_FILE

    if origen.exists():
        shutil.copy2(origen, DB_PATH)
        print("✅ Base original restaurada correctamente en AppData.")
    else:
        print("⚠ No se encontró base original en default_db.")


# ==============================================================================
# 🎨 CONFIGURACIÓN DE UI - CUSTOMTKINTER
# ==============================================================================

try:
    from ctk_design_system import (
        Colors,
        Fonts,
        Dimensions,
        initialize_customtkinter,
        configure_treeview_style
    )

    FONT_FAMILY = Fonts.FAMILY
    FONT_SIZE = Fonts.BODY_SIZE
    FONT_STYLE = Fonts.BODY

    BG_COLOR = Colors.BACKGROUND
    BTN_COLOR = Colors.PRIMARY
    BTN_FG = Colors.SURFACE

except ImportError:
    import logging
    logging.warning("ctk_design_system.py no encontrado, usando valores por defecto")

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE = 14
    FONT_STYLE = (FONT_FAMILY, FONT_SIZE)

    BG_COLOR = "#f4f6f8"
    BTN_COLOR = "#0f6cbd"
    BTN_FG = "#ffffff"


# ==============================================================================
# 🏢 CONFIGURACIÓN DE LA EMPRESA
# ==============================================================================

COMPANY_NAME = "Droguería Irlandesa"
COMPANY_NIT = "1019054697-5"
COMPANY_ADDRESS = "Calle 10F 80F 03"
COMPANY_PHONE = "6019369264"
COMPANY_BRANCH = "Lagos de Castilla"


# ==============================================================================
# 📦 CONFIGURACIÓN DE PEDIDOS
# ==============================================================================

CODIGO_DROGUERIA = "35389"


# ==============================================================================
# 🔒 SEGURIDAD
# ==============================================================================

PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TT6WrBn8eFP5J3xZ1K9mM5L6Z3Lm"


# ==============================================================================
# 📊 CONFIGURACIÓN DE COLUMNAS (INVENTARIO)
# ==============================================================================

COLUMN_WIDTHS = {
    "id_producto": 60,
    "codigo_barras": 100,
    "descripcion": 290,
    "cantidad": 55,
    "proveedor": 190,
    "precio_compra": 90,
    "precio_venta": 75,
    "unidad": 50,
    "impuesto": 100,
    "bonificacion": 40,
    "grupo": 150,
    "subgrupo": 150,
    "fecha_vencimiento": 120
}


# ==============================================================================
# ✅ VALIDACIÓN
# ==============================================================================

MAX_CODIGO_BARRAS_LENGTH = 50
MAX_DESCRIPCION_LENGTH = 200
MAX_SEARCH_RESULTS = 80


# ==============================================================================
# 🎨 INICIALIZACIÓN
# ==============================================================================

def initialize_design_system():
    """
    Inicializa el sistema de diseño CustomTkinter.
    Debe llamarse UNA VEZ al inicio de la aplicación.
    """
    try:
        initialize_customtkinter()
        configure_treeview_style()

        import logging
        logging.info("Sistema de diseño CustomTkinter inicializado correctamente")

    except Exception as e:
        import logging
        logging.error(f"Error al inicializar sistema de diseño: {e}")