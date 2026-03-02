"""
Tests unitarios para utils/validators.py
"""
import pytest
from utils.validators import (
    validate_codigo_barras,
    validate_precio,
    validate_cantidad,
    validate_fecha,
    sanitize_sql_column
)


class TestValidateCodigoBarras:
    """Tests para validación de códigos de barras"""
    
    def test_codigo_valido_numerico(self):
        """Código numérico válido"""
        assert validate_codigo_barras("7501234567890") == True
    
    def test_codigo_valido_alfanumerico(self):
        """Código alfanumérico válido"""
        assert validate_codigo_barras("ABC123XYZ") == True
    
    def test_codigo_con_guiones(self):
        """Código con guiones válido"""
        assert validate_codigo_barras("123-456-789") == True
    
    def test_codigo_vacio(self):
        """Código vacío inválido"""
        assert validate_codigo_barras("") == False
    
    def test_codigo_muy_largo(self):
        """Código mayor a 50 caracteres inválido"""
        assert validate_codigo_barras("A" * 51) == False
    
    def test_codigo_con_espacios(self):
        """Código con espacios inválido"""
        assert validate_codigo_barras("123 456 789") == False
    
    def test_codigo_con_caracteres_especiales(self):
        """Código con caracteres especiales inválido"""
        assert validate_codigo_barras("123@456#789") == False
    
    def test_codigo_none(self):
        """Código None inválido"""
        assert validate_codigo_barras(None) == False
    
    def test_codigo_con_letras_minusculas(self):
        """Código con minúsculas válido"""
        assert validate_codigo_barras("abc123xyz") == True
    
    def test_codigo_con_letras_mayusculas(self):
        """Código con mayúsculas válido"""
        assert validate_codigo_barras("ABC123XYZ") == True


class TestValidatePrecio:
    """Tests para validación de precios"""
    
    def test_precio_entero_valido(self):
        """Precio entero válido"""
        assert validate_precio("1000") == 1000.0
    
    def test_precio_decimal_valido(self):
        """Precio con decimales válido"""
        assert validate_precio("1500.50") == 1500.50
    
    def test_precio_cero_valido(self):
        """Precio cero válido"""
        assert validate_precio("0") == 0.0
    
    def test_precio_negativo_invalido(self):
        """Precio negativo inválido"""
        assert validate_precio("-100") is None
    
    def test_precio_texto_invalido(self):
        """Texto no numérico inválido"""
        assert validate_precio("abc") is None
    
    def test_precio_vacio_invalido(self):
        """Precio vacío inválido"""
        assert validate_precio("") is None
    
    def test_precio_muy_grande(self):
        """Precio muy grande válido"""
        assert validate_precio("999999999.99") == 999999999.99
    
    def test_precio_con_comas(self):
        """Precio con comas (formato europeo) - debería fallar"""
        # El validador actual no maneja formatos, solo float directo
        assert validate_precio("1,500.50") is None
    
    def test_precio_float_directo(self):
        """Precio como float"""
        assert validate_precio(1500.75) == 1500.75
    
    def test_precio_none(self):
        """Precio None inválido"""
        assert validate_precio(None) is None


class TestValidateCantidad:
    """Tests para validación de cantidades"""
    
    def test_cantidad_valida(self):
        """Cantidad positiva válida"""
        assert validate_cantidad("10") == 10
    
    def test_cantidad_cero_valida(self):
        """Cantidad cero válida"""
        assert validate_cantidad("0") == 0
    
    def test_cantidad_negativa_invalida(self):
        """Cantidad negativa inválida"""
        assert validate_cantidad("-5") is None
    
    def test_cantidad_decimal_invalida(self):
        """Cantidad decimal inválida"""
        assert validate_cantidad("10.5") is None
    
    def test_cantidad_texto_invalido(self):
        """Texto no numérico inválido"""
        assert validate_cantidad("abc") is None
    
    def test_cantidad_vacia_invalida(self):
        """Cantidad vacía inválida"""
        assert validate_cantidad("") is None
    
    def test_cantidad_muy_grande(self):
        """Cantidad muy grande válida"""
        assert validate_cantidad("999999") == 999999
    
    def test_cantidad_con_espacios(self):
        """Cantidad con espacios - debería fallar"""
        assert validate_cantidad("10 ") is None  # strip debería hacerse antes
    
    def test_cantidad_int_directo(self):
        """Cantidad como int"""
        assert validate_cantidad(25) == 25
    
    def test_cantidad_none(self):
        """Cantidad None inválida"""
        assert validate_cantidad(None) is None


class TestValidateFecha:
    """Tests para validación de fechas"""
    
    def test_fecha_valida(self):
        """Fecha en formato correcto"""
        assert validate_fecha("2024-12-31") == True
    
    def test_fecha_actual_valida(self):
        """Fecha actual válida"""
        assert validate_fecha("2026-02-15") == True
    
    def test_fecha_vacia_valida(self):
        """Fecha vacía válida (opcional)"""
        assert validate_fecha("") == True
    
    def test_fecha_formato_invalido_barras(self):
        """Fecha con barras inválida"""
        assert validate_fecha("31/12/2024") == False
    
    def test_fecha_formato_invalido_puntos(self):
        """Fecha con puntos inválida"""
        assert validate_fecha("31.12.2024") == False
    
    def test_fecha_incompleta(self):
        """Fecha incompleta inválida"""
        assert validate_fecha("2024-12") == False
    
    def test_fecha_mes_invalido(self):
        """Fecha con mes inválido"""
        assert validate_fecha("2024-13-01") == False
    
    def test_fecha_dia_invalido(self):
        """Fecha con día inválido"""
        assert validate_fecha("2024-02-30") == False
    
    def test_fecha_none(self):
        """Fecha None inválida"""
        assert validate_fecha(None) == False
    
    def test_fecha_año_bisiesto(self):
        """Fecha en año bisiesto válida"""
        assert validate_fecha("2024-02-29") == True
    
    def test_fecha_año_no_bisiesto(self):
        """Fecha 29 feb en año no bisiesto inválida"""
        assert validate_fecha("2023-02-29") == False


class TestSanitizeSQLColumn:
    """Tests para sanitización de nombres de columnas SQL"""
    
    def test_columna_valida_descripcion(self):
        """Columna 'descripcion' válida"""
        assert sanitize_sql_column("descripcion") == "descripcion"
    
    def test_columna_valida_cantidad(self):
        """Columna 'cantidad' válida"""
        assert sanitize_sql_column("cantidad") == "cantidad"
    
    def test_columna_con_espacios(self):
        """Columna con espacios convertida a underscore"""
        assert sanitize_sql_column("precio compra") == "precio_compra"
    
    def test_columna_con_mayusculas(self):
        """Columna con mayúsculas convertida a minúsculas"""
        assert sanitize_sql_column("DESCRIPCION") == "descripcion"
    
    def test_columna_mixta(self):
        """Columna con mayúsculas y espacios"""
        assert sanitize_sql_column("Precio Venta") == "precio_venta"
    
    def test_columna_invalida_id(self):
        """Columna 'id_producto' no está en whitelist"""
        assert sanitize_sql_column("id_producto") is None
    
    def test_columna_invalida_tabla(self):
        """Intento de inyección SQL inválido"""
        assert sanitize_sql_column("productos") is None
    
    def test_columna_invalida_comando(self):
        """Intento de comando SQL inválido"""
        assert sanitize_sql_column("DROP TABLE") is None
    
    def test_columna_vacia(self):
        """Columna vacía inválida"""
        assert sanitize_sql_column("") is None
    
    def test_columnas_validas_todas(self):
        """Verificar todas las columnas permitidas"""
        columnas_validas = [
            'descripcion', 'proveedor', 'unidad', 'cantidad',
            'precio_compra', 'precio_venta', 'impuesto',
            'bonificacion', 'grupo', 'subgrupo', 'fecha_vencimiento'
        ]
        
        for col in columnas_validas:
            assert sanitize_sql_column(col) == col, f"Falló para {col}"
    
    def test_columna_con_guion(self):
        """Columna con guion no se convierte"""
        assert sanitize_sql_column("precio-venta") is None


# ============================================================
# TESTS DE INTEGRACIÓN DE VALIDADORES
# ============================================================

class TestIntegracionValidadores:
    """Tests de integración entre validadores"""
    
    def test_producto_completo_valido(self):
        """Validar producto completo con todos los campos"""
        datos = {
            'codigo_barras': '7501234567890',
            'descripcion': 'ACETAMINOFEN 500MG',
            'cantidad': '100',
            'precio_compra': '5000',
            'precio_venta': '7000',
            'fecha_vencimiento': '2026-12-31'
        }
        
        assert validate_codigo_barras(datos['codigo_barras']) == True
        assert validate_cantidad(datos['cantidad']) == 100
        assert validate_precio(datos['precio_compra']) == 5000.0
        assert validate_precio(datos['precio_venta']) == 7000.0
        assert validate_fecha(datos['fecha_vencimiento']) == True
    
    def test_producto_con_errores_multiples(self):
        """Producto con múltiples errores de validación"""
        datos = {
            'codigo_barras': 'CODIGO CON ESPACIOS',  # Inválido
            'cantidad': '-10',  # Inválido
            'precio_compra': 'abc',  # Inválido
            'fecha_vencimiento': '31/12/2024'  # Inválido
        }
        
        assert validate_codigo_barras(datos['codigo_barras']) == False
        assert validate_cantidad(datos['cantidad']) is None
        assert validate_precio(datos['precio_compra']) is None
        assert validate_fecha(datos['fecha_vencimiento']) == False


# ============================================================
# TESTS PARAMETRIZADOS
# ============================================================

@pytest.mark.parametrize("codigo,esperado", [
    ("123", True),
    ("ABC", True),
    ("A1B2C3", True),
    ("123-456", True),
    ("", False),
    ("A" * 51, False),
    ("123 456", False),
    ("@#$", False),
])
def test_codigos_barras_parametrizado(codigo, esperado):
    """Test parametrizado para múltiples códigos"""
    assert validate_codigo_barras(codigo) == esperado


@pytest.mark.parametrize("precio,esperado", [
    ("100", 100.0),
    ("0", 0.0),
    ("9999.99", 9999.99),
    ("-100", None),
    ("abc", None),
    ("", None),
])
def test_precios_parametrizado(precio, esperado):
    """Test parametrizado para múltiples precios"""
    assert validate_precio(precio) == esperado


@pytest.mark.parametrize("cantidad,esperado", [
    ("10", 10),
    ("0", 0),
    ("999", 999),
    ("-5", None),
    ("10.5", None),
    ("abc", None),
])
def test_cantidades_parametrizado(cantidad, esperado):
    """Test parametrizado para múltiples cantidades"""
    assert validate_cantidad(cantidad) == esperado
