"""
Funciones de validación de datos
"""
import re
from datetime import datetime
from typing import Optional


def validate_codigo_barras(codigo: str) -> bool:
    """Valida que el código de barras sea válido"""
    if not codigo or len(codigo) > 50:
        return False
    # Solo alfanuméricos y guiones
    return bool(re.match(r'^[A-Za-z0-9\-]+$', codigo))


def validate_precio(precio: str) -> Optional[float]:
    """Valida y convierte precio a float"""
    try:
        precio_float = float(precio)
        if precio_float < 0:
            return None
        return precio_float
    except (ValueError, TypeError):
        return None


def validate_cantidad(cantidad: str) -> Optional[int]:
    """Valida y convierte cantidad a int"""
    try:
        cantidad_int = int(cantidad)
        if cantidad_int < 0:
            return None
        return cantidad_int
    except (ValueError, TypeError):
        return None


def validate_fecha(fecha: str) -> bool:
    """Valida formato de fecha YYYY-MM-DD"""
    if not fecha:
        return True  # Fecha opcional
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def sanitize_sql_column(column_name: str) -> Optional[str]:
    """Valida nombre de columna contra lista blanca"""
    allowed_columns = {
        'descripcion', 'proveedor', 'unidad', 'cantidad',
        'precio_compra', 'precio_venta', 'impuesto',
        'bonificacion', 'grupo', 'subgrupo', 'fecha_vencimiento'
    }

    column_clean = column_name.lower().replace(" ", "_")

    if column_clean in allowed_columns:
        return column_clean
    return None
