"""
Funciones de formateo de datos
"""
import re
from typing import Optional


def format_precio_display(precio: float) -> str:
    """Formatea precio para mostrar: $1.234.567"""
    return f"${int(round(precio)):,}".replace(",", ".")


def format_precio_miles(valor) -> str:
    """Formatea valor como precio con separador de miles"""
    try:
        return f"${int(round(float(valor))):,}".replace(",", ".")
    except:
        return str(valor)


def parse_precio_text(valor_texto) -> Optional[float]:
    """
    Convierte texto de precio a float.
    Maneja enteros, apóstrofos, espacios y formatos con separadores.
    """
    if valor_texto is None:
        return None

    # Convertir a string y limpiar
    s = str(valor_texto).strip().lstrip("'").strip()

    if not s:
        return None

    # Caso simple: solo dígitos
    if s.isdigit():
        return float(s)

    # Eliminar todo excepto dígitos, punto, coma y signo
    s = re.sub(r"[^\d,.\-]", "", s)

    if not s:
        return None

    num_commas = s.count(",")
    num_dots = s.count(".")

    try:
        # Ambos separadores presentes
        if num_commas and num_dots:
            if s.rfind(",") > s.rfind("."):
                # Formato: 1.234.567,89 (europeo)
                s = s.replace(".", "").replace(",", ".")
            else:
                # Formato: 1,234,567.89 (americano)
                s = s.replace(",", "")

        # Solo comas
        elif num_commas:
            parts = s.split(",")
            if len(parts[-1]) == 3 and len(parts) > 1:
                # Formato: 1,234 (miles)
                s = s.replace(",", "")
            else:
                # Formato: 1,23 (decimal)
                s = s.replace(",", ".")

        # Solo puntos
        elif num_dots:
            parts = s.split(".")
            if len(parts[-1]) == 3 and len(parts) > 1:
                # Formato: 1.234 (miles)
                s = s.replace(".", "")

        return float(s)
    except:
        return None


def clean_codigo_barras(codigo: str) -> str:
    """Limpia código de barras de caracteres invisibles"""
    return (
        str(codigo)
        .strip()
        .lstrip("'")
        .replace(" ", "")
        .replace("\u200b", "")  # Zero-width space
    )