"""
Configuración central de la aplicación
✅ MIGRADO A CUSTOMTKINTER
"""
import os
from pathlib import Path

# ==============================================================================
# 📁 RUTAS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "farma_pro_stocker.db"
RESOURCES_DIR = BASE_DIR / "resources"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
LOGS_DIR.mkdir(exist_ok=True)
RESOURCES_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 🎨 CONFIGURACIÓN DE UI - CUSTOMTKINTER
# ==============================================================================

# IMPORTANTE: Importar desde el sistema de diseño CustomTkinter
try:
    from ctk_design_system import (
        Colors,
        Fonts,
        Dimensions,
        initialize_customtkinter,
        configure_treeview_style
    )

    # Alias para compatibilidad con código existente
    FONT_FAMILY = Fonts.FAMILY
    FONT_SIZE = Fonts.BODY_SIZE
    FONT_STYLE = Fonts.BODY

    # Colores para compatibilidad
    BG_COLOR = Colors.BACKGROUND
    BTN_COLOR = Colors.PRIMARY
    BTN_FG = Colors.SURFACE

except ImportError:
    # Fallback temporal
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

# Hash de "007"
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
    Debe llamarse UNA VEZ al inicio de la aplicación (en main.py).
    """
    try:
        # Inicializar CustomTkinter
        initialize_customtkinter()

        # Configurar estilo de Treeview
        configure_treeview_style()

        import logging
        logging.info("Sistema de diseño CustomTkinter inicializado correctamente")
    except Exception as e:
        import logging
        logging.error(f"Error al inicializar sistema de diseño: {e}")