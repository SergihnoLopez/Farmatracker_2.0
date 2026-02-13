"""
Configuración central de la aplicación
"""
import os
from pathlib import Path

# Rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "farma_pro_stocker.db"
RESOURCES_DIR = BASE_DIR / "resources"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
LOGS_DIR.mkdir(exist_ok=True)

# Configuración de UI
FONT_FAMILY = "Titillium Web"
FONT_SIZE = 14
FONT_STYLE = (FONT_FAMILY, FONT_SIZE)

BG_COLOR = "#f0f4f7"
BTN_COLOR = "#4CAF50"
BTN_FG = "white"

# Configuración de factura
COMPANY_NAME = "Droguería Irlandesa"
COMPANY_NIT = "1019054697-5"
COMPANY_ADDRESS = "Calle 10F 80F 03"
COMPANY_PHONE = "6019369264"
COMPANY_BRANCH = "Lagos de Castilla"

# Configuración de pedidos
CODIGO_DROGUERIA = "35389"

# Seguridad
PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TT6WrBn8eFP5J3xZ1K9mM5L6Z3Lm"  # Hash de "007"

# Anchos de columnas para inventario
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

# Validación
MAX_CODIGO_BARRAS_LENGTH = 50
MAX_DESCRIPCION_LENGTH = 200
MAX_SEARCH_RESULTS = 80
