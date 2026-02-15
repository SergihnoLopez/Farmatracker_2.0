"""
Tests unitarios para utils/formatters.py
"""
import pytest
from utils.formatters import (
    format_precio_display,
    format_precio_miles,
    parse_precio_text,
    clean_codigo_barras
)


class TestFormatPrecioDisplay:
    """Tests para formateo de precios para mostrar"""
    
    def test_precio_entero(self):
        """Precio entero sin decimales"""
        assert format_precio_display(1000.0) == "$1.000"
    
    def test_precio_con_decimales_redondeo(self):
        """Precio con decimales se redondea"""
        assert format_precio_display(1234.56) == "$1.235"
    
    def test_precio_cero(self):
        """Precio cero"""
        assert format_precio_display(0.0) == "$0"
    
    def test_precio_grande(self):
        """Precio grande con separadores"""
        assert format_precio_display(1234567.0) == "$1.234.567"
    
    def test_precio_negativo(self):
        """Precio negativo (edge case)"""
        assert format_precio_display(-1000.0) == "$-1.000"
    
    def test_precio_decimal_bajo(self):
        """Precio menor a 1"""
        assert format_precio_display(0.99) == "$1"
    
    def test_precio_redondeo_hacia_arriba(self):
        """Redondeo hacia arriba desde 0.5"""
        assert format_precio_display(1234.5) == "$1.235"
    
    def test_precio_muy_grande(self):
        """Precio millonario"""
        assert format_precio_display(9999999.0) == "$9.999.999"


class TestFormatPrecioMiles:
    """Tests para formateo con separador de miles"""
    
    def test_numero_entero(self):
        """Número entero simple"""
        assert format_precio_miles(1000) == "$1.000"
    
    def test_numero_float(self):
        """Número float"""
        assert format_precio_miles(1234.56) == "$1.235"
    
    def test_numero_string(self):
        """Número como string"""
        assert format_precio_miles("1000") == "$1.000"
    
    def test_numero_cero(self):
        """Número cero"""
        assert format_precio_miles(0) == "$0"
    
    def test_valor_no_numerico(self):
        """Valor no numérico retorna string original"""
        resultado = format_precio_miles("ABC")
        assert resultado == "ABC"
    
    def test_none(self):
        """Valor None"""
        resultado = format_precio_miles(None)
        assert "None" in resultado
    
    def test_numero_negativo(self):
        """Número negativo"""
        assert format_precio_miles(-1000) == "$-1.000"


class TestParsePrecioText:
    """Tests para parseo de texto a precio"""
    
    def test_numero_simple(self):
        """Número simple sin formato"""
        assert parse_precio_text("1000") == 1000.0
    
    def test_numero_con_punto_miles(self):
        """Número con punto como separador de miles"""
        assert parse_precio_text("1.000") == 1000.0
    
    def test_numero_con_coma_decimal(self):
        """Número con coma como decimal"""
        assert parse_precio_text("1,50") == 1.5
    
    def test_numero_formato_colombiano(self):
        """Formato colombiano: 1.234.567,89"""
        assert parse_precio_text("1.234.567,89") == 1234567.89
    
    def test_numero_formato_americano(self):
        """Formato americano: 1,234,567.89"""
        assert parse_precio_text("1,234,567.89") == 1234567.89
    
    def test_numero_con_simbolo_pesos(self):
        """Número con símbolo $ eliminado"""
        assert parse_precio_text("$1000") == 1000.0
    
    def test_numero_con_espacios(self):
        """Número con espacios"""
        assert parse_precio_text(" 1 000 ") == 1000.0
    
    def test_numero_con_apostrofe(self):
        """Número con apóstrofe inicial (Excel)"""
        assert parse_precio_text("'1000") == 1000.0
    
    def test_texto_vacio(self):
        """Texto vacío retorna None"""
        assert parse_precio_text("") is None
    
    def test_texto_none(self):
        """None retorna None"""
        assert parse_precio_text(None) is None
    
    def test_texto_no_numerico(self):
        """Texto completamente no numérico"""
        assert parse_precio_text("ABC") is None
    
    def test_numero_solo_digitos(self):
        """Número solo dígitos (isdigit path)"""
        assert parse_precio_text("12345") == 12345.0
    
    def test_numero_negativo(self):
        """Número negativo"""
        assert parse_precio_text("-1000") == -1000.0
    
    def test_decimal_con_punto(self):
        """Decimal con punto"""
        assert parse_precio_text("1.5") == 1.5
    
    def test_multiple_puntos_miles(self):
        """Múltiples puntos como separadores de miles"""
        assert parse_precio_text("1.234.567") == 1234567.0
    
    def test_coma_como_miles(self):
        """Comas como separadores de miles"""
        assert parse_precio_text("1,234,567") == 1234567.0
    
    def test_formato_mixto_europeo(self):
        """Formato europeo con miles y decimales"""
        assert parse_precio_text("1.500,50") == 1500.5
    
    def test_formato_solo_coma_decimal(self):
        """Solo coma como decimal (europeo)"""
        assert parse_precio_text("5,99") == 5.99
    
    def test_precio_excel_apostrofe_formato(self):
        """Precio de Excel con apóstrofe y formato"""
        assert parse_precio_text("'1.234,56") == 1234.56


class TestCleanCodigoBarras:
    """Tests para limpieza de códigos de barras"""
    
    def test_codigo_limpio(self):
        """Código sin caracteres especiales"""
        assert clean_codigo_barras("7501234567890") == "7501234567890"
    
    def test_codigo_con_espacios(self):
        """Código con espacios eliminados"""
        assert clean_codigo_barras("750 123 456") == "750123456"
    
    def test_codigo_con_apostrofe(self):
        """Código con apóstrofe inicial (Excel)"""
        assert clean_codigo_barras("'7501234567890") == "7501234567890"
    
    def test_codigo_con_espacios_laterales(self):
        """Código con espacios al inicio y fin"""
        assert clean_codigo_barras("  7501234567890  ") == "7501234567890"
    
    def test_codigo_con_zero_width_space(self):
        """Código con espacio de ancho cero"""
        assert clean_codigo_barras("750\u200b123") == "750123"
    
    def test_codigo_vacio(self):
        """Código vacío"""
        assert clean_codigo_barras("") == ""
    
    def test_codigo_solo_espacios(self):
        """Código solo espacios"""
        assert clean_codigo_barras("   ") == ""
    
    def test_codigo_numero_entero(self):
        """Código como número se convierte a string"""
        assert clean_codigo_barras(123456) == "123456"
    
    def test_codigo_mixto_caracteres_invisibles(self):
        """Código con múltiples caracteres invisibles"""
        assert clean_codigo_barras("'  750\u200b123  ") == "750123"
    
    def test_codigo_con_guiones_mantiene(self):
        """Código con guiones se mantienen"""
        assert clean_codigo_barras("750-123-456") == "750-123-456"


# ============================================================
# TESTS PARAMETRIZADOS
# ============================================================

@pytest.mark.parametrize("precio,esperado", [
    (1000, "$1.000"),
    (1234567, "$1.234.567"),
    (0, "$0"),
    (999, "$999"),
    (1000000, "$1.000.000"),
])
def test_format_display_parametrizado(precio, esperado):
    """Test parametrizado para format_precio_display"""
    assert format_precio_display(precio) == esperado


@pytest.mark.parametrize("texto,esperado", [
    ("1000", 1000.0),
    ("1.000", 1000.0),
    ("1,000", 1000.0),
    ("1.234.567", 1234567.0),
    ("1,234,567", 1234567.0),
    ("1.234,56", 1234.56),
    ("1,234.56", 1234.56),
    ("$1000", 1000.0),
    ("'1000", 1000.0),
    ("", None),
    ("ABC", None),
])
def test_parse_precio_parametrizado(texto, esperado):
    """Test parametrizado para parse_precio_text"""
    assert parse_precio_text(texto) == esperado


@pytest.mark.parametrize("codigo,esperado", [
    ("123", "123"),
    ("  123  ", "123"),
    ("'123", "123"),
    ("1 2 3", "123"),
    ("123\u200b456", "123456"),
    ("'  123  ", "123"),
])
def test_clean_codigo_parametrizado(codigo, esperado):
    """Test parametrizado para clean_codigo_barras"""
    assert clean_codigo_barras(codigo) == esperado


# ============================================================
# TESTS DE INTEGRACIÓN
# ============================================================

class TestIntegracionFormatters:
    """Tests de integración entre formateadores"""
    
    def test_ciclo_completo_precio(self):
        """Parse y format de precio en ciclo completo"""
        texto_original = "1.234,56"
        precio = parse_precio_text(texto_original)
        texto_formateado = format_precio_display(precio)
        
        assert precio == 1234.56
        assert texto_formateado == "$1.235"  # Redondeado
    
    def test_precios_colombianos_multiples(self):
        """Varios precios en formato colombiano"""
        precios_texto = ["1.000", "5.000", "12.500", "100.000"]
        precios_parseados = [parse_precio_text(p) for p in precios_texto]
        
        assert precios_parseados == [1000.0, 5000.0, 12500.0, 100000.0]
    
    def test_limpiar_y_formatear_codigo(self):
        """Limpiar código y usarlo"""
        codigo_sucio = "'  750123456  "
        codigo_limpio = clean_codigo_barras(codigo_sucio)
        
        assert codigo_limpio == "750123456"
        assert len(codigo_limpio) == 9
    
    def test_formato_consistente_precios(self):
        """Formateo consistente de varios precios"""
        precios = [100, 1000, 10000, 100000]
        formateados = [format_precio_display(p) for p in precios]
        
        assert formateados == ["$100", "$1.000", "$10.000", "$100.000"]


# ============================================================
# TESTS DE EDGE CASES
# ============================================================

class TestEdgeCases:
    """Tests de casos extremos"""
    
    def test_precio_muy_grande(self):
        """Precio extremadamente grande"""
        precio = 999999999999.99
        resultado = format_precio_display(precio)
        assert "$" in resultado
    
    def test_precio_muy_pequeño(self):
        """Precio muy pequeño"""
        precio = 0.01
        resultado = format_precio_display(precio)
        assert resultado == "$0"  # Se redondea a 0
    
    def test_parse_precio_formato_invalido_extremo(self):
        """Formato completamente inválido"""
        assert parse_precio_text("@#$%^&*()") is None
    
    def test_codigo_unicode_especial(self):
        """Código con caracteres Unicode especiales"""
        codigo = "ABC\u200b\u200c\u200dXYZ"
        limpio = clean_codigo_barras(codigo)
        assert limpio == "ABCXYZ"
    
    def test_multiples_separadores_consecutivos(self):
        """Precio con múltiples separadores consecutivos"""
        # Comportamiento actual puede variar
        resultado = parse_precio_text("1...000")
        # Verificar que no lance excepción
        assert resultado is None or isinstance(resultado, float)
