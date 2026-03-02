"""
Tests unitarios para models/database.py
"""
import pytest
import sqlite3
from pathlib import Path
from models.database import DatabaseManager, get_db_connection
from unittest.mock import patch, MagicMock


class TestGetDBConnection:
    """Tests para el context manager de conexión a BD"""
    
    def test_conexion_exitosa(self, clean_db):
        """Conexión a BD exitosa"""
        with patch('models.database.DB_PATH', clean_db):
            with get_db_connection() as conn:
                assert conn is not None
                assert isinstance(conn, sqlite3.Connection)
    
    def test_conexion_commit_automatico(self, clean_db):
        """Commit automático al salir del context manager"""
        with patch('models.database.DB_PATH', clean_db):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO productos (codigo_barras, descripcion)
                    VALUES ('TEST001', 'Producto Test')
                """)
            
            # Verificar que se guardó
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM productos WHERE codigo_barras = 'TEST001'")
                resultado = cursor.fetchone()
                assert resultado is not None
    
    def test_conexion_rollback_en_error(self, clean_db):
        """Rollback automático en caso de error"""
        with patch('models.database.DB_PATH', clean_db):
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO productos (codigo_barras, descripcion)
                        VALUES ('TEST002', 'Producto Test')
                    """)
                    # Provocar error
                    raise ValueError("Error de prueba")
            except ValueError:
                pass
            
            # Verificar que NO se guardó (rollback)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM productos WHERE codigo_barras = 'TEST002'")
                resultado = cursor.fetchone()
                assert resultado is None
    
    def test_row_factory_configurado(self, clean_db):
        """Row factory permite acceso por nombre de columna"""
        with patch('models.database.DB_PATH', clean_db):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO productos (codigo_barras, descripcion)
                    VALUES ('TEST003', 'Test Description')
                """)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM productos WHERE codigo_barras = 'TEST003'")
                row = cursor.fetchone()
                
                # Acceso por nombre
                assert row['codigo_barras'] == 'TEST003'
                assert row['descripcion'] == 'Test Description'


class TestBuscarProductoPorCodigo:
    """Tests para buscar_producto_por_codigo"""
    
    def test_buscar_producto_existente(self, db_con_productos):
        """Buscar producto que existe"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            assert producto is not None
            assert producto['codigo_barras'] == '7501234567890'
            assert producto['descripcion'] == 'ACETAMINOFEN 500MG X 20 TABS'
            assert producto['cantidad'] == 100
            assert producto['precio_compra'] == 5000.0
    
    def test_buscar_producto_no_existente(self, db_con_productos):
        """Buscar producto que no existe"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('9999999999999')
            
            assert producto is None
    
    def test_buscar_producto_codigo_vacio(self, clean_db):
        """Buscar con código vacío"""
        with patch('models.database.DB_PATH', clean_db):
            producto = DatabaseManager.buscar_producto_por_codigo('')
            
            assert producto is None
    
    def test_buscar_producto_retorna_dict(self, db_con_productos):
        """Resultado es un diccionario con todas las claves"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            assert isinstance(producto, dict)
            claves_esperadas = [
                'id_producto', 'codigo_barras', 'descripcion', 
                'cantidad', 'precio_compra', 'precio_venta',
                'impuesto', 'fecha_vencimiento'
            ]
            
            for clave in claves_esperadas:
                assert clave in producto


class TestBuscarProductosLike:
    """Tests para buscar_productos_like"""
    
    def test_buscar_por_descripcion_parcial(self, db_con_productos):
        """Buscar productos por descripción parcial"""
        with patch('models.database.DB_PATH', db_con_productos):
            resultados = DatabaseManager.buscar_productos_like('ACETA')
            
            assert len(resultados) == 1
            assert resultados[0][0] == '7501234567890'
            assert 'ACETAMINOFEN' in resultados[0][1]
    
    def test_buscar_por_codigo_parcial(self, db_con_productos):
        """Buscar productos por código parcial"""
        with patch('models.database.DB_PATH', db_con_productos):
            resultados = DatabaseManager.buscar_productos_like('750123')
            
            assert len(resultados) == 3  # Los 3 productos de prueba
    
    def test_buscar_sin_resultados(self, db_con_productos):
        """Búsqueda sin resultados"""
        with patch('models.database.DB_PATH', db_con_productos):
            resultados = DatabaseManager.buscar_productos_like('XXXXX')
            
            assert len(resultados) == 0
    
    def test_buscar_case_insensitive(self, db_con_productos):
        """Búsqueda no sensible a mayúsculas"""
        with patch('models.database.DB_PATH', db_con_productos):
            resultados_lower = DatabaseManager.buscar_productos_like('acetaminofen')
            resultados_upper = DatabaseManager.buscar_productos_like('ACETAMINOFEN')
            
            assert len(resultados_lower) == len(resultados_upper)
            assert len(resultados_lower) == 1
    
    def test_buscar_con_limite(self, db_con_productos):
        """Límite de resultados funciona"""
        with patch('models.database.DB_PATH', db_con_productos):
            resultados = DatabaseManager.buscar_productos_like('750', limit=2)
            
            assert len(resultados) <= 2
    
    def test_buscar_retorna_tuplas(self, db_con_productos):
        """Resultados son tuplas (codigo, descripcion)"""
        with patch('models.database.DB_PATH', db_con_productos):
            resultados = DatabaseManager.buscar_productos_like('IB')
            
            assert len(resultados) > 0
            assert isinstance(resultados[0], tuple)
            assert len(resultados[0]) == 2


class TestInsertarProducto:
    """Tests para insertar_producto"""
    
    def test_insertar_producto_completo(self, clean_db):
        """Insertar producto con todos los campos"""
        with patch('models.database.DB_PATH', clean_db):
            datos = {
                'codigo_barras': 'TEST001',
                'descripcion': 'PRODUCTO TEST',
                'proveedor': 'PROVEEDOR TEST',
                'unidad': 'CAJA',
                'cantidad': 50,
                'precio_compra': 1000.0,
                'precio_venta': 1500.0,
                'impuesto': '19% IVA',
                'bonificacion': 100.0,
                'grupo': 'GRUPO TEST',
                'subgrupo': 'SUBGRUPO TEST',
                'fecha_vencimiento': '2026-12-31'
            }
            
            resultado = DatabaseManager.insertar_producto(datos)
            assert resultado == True
            
            # Verificar que se insertó
            producto = DatabaseManager.buscar_producto_por_codigo('TEST001')
            assert producto is not None
            assert producto['descripcion'] == 'PRODUCTO TEST'
    
    def test_insertar_producto_minimo(self, clean_db):
        """Insertar producto con campos mínimos"""
        with patch('models.database.DB_PATH', clean_db):
            datos = {
                'codigo_barras': 'TEST002',
                'descripcion': 'PRODUCTO MINIMO'
            }
            
            resultado = DatabaseManager.insertar_producto(datos)
            assert resultado == True
    
    def test_insertar_producto_duplicado(self, db_con_productos):
        """Insertar producto con código duplicado falla"""
        with patch('models.database.DB_PATH', db_con_productos):
            datos = {
                'codigo_barras': '7501234567890',  # Ya existe
                'descripcion': 'DUPLICADO'
            }
            
            resultado = DatabaseManager.insertar_producto(datos)
            assert resultado == False


class TestActualizarCantidad:
    """Tests para actualizar_cantidad"""
    
    def test_actualizar_cantidad_exitoso(self, db_con_productos):
        """Actualizar cantidad de producto existente"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Obtener ID del producto
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            id_producto = producto['id_producto']
            
            # Actualizar cantidad
            resultado = DatabaseManager.actualizar_cantidad(id_producto, 200)
            assert resultado == True
            
            # Verificar cambio
            producto_actualizado = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            assert producto_actualizado['cantidad'] == 200
    
    def test_actualizar_cantidad_producto_inexistente(self, clean_db):
        """Actualizar cantidad de producto que no existe"""
        with patch('models.database.DB_PATH', clean_db):
            resultado = DatabaseManager.actualizar_cantidad(99999, 100)
            assert resultado == False
    
    def test_actualizar_cantidad_a_cero(self, db_con_productos):
        """Actualizar cantidad a cero"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            resultado = DatabaseManager.actualizar_cantidad(producto['id_producto'], 0)
            assert resultado == True
            
            producto_actualizado = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            assert producto_actualizado['cantidad'] == 0


class TestActualizarCampoProducto:
    """Tests para actualizar_campo_producto"""
    
    def test_actualizar_descripcion(self, db_con_productos):
        """Actualizar descripción de producto"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            resultado = DatabaseManager.actualizar_campo_producto(
                producto['id_producto'],
                'descripcion',
                'NUEVA DESCRIPCION'
            )
            
            assert resultado == True
            
            producto_actualizado = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            assert producto_actualizado['descripcion'] == 'NUEVA DESCRIPCION'
    
    def test_actualizar_precio_compra(self, db_con_productos):
        """Actualizar precio de compra"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            resultado = DatabaseManager.actualizar_campo_producto(
                producto['id_producto'],
                'precio_compra',
                8000.0
            )
            
            assert resultado == True
    
    def test_actualizar_campo_no_permitido(self, db_con_productos):
        """Actualizar campo no permitido (protección SQL injection)"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            # Intentar actualizar columna no permitida
            resultado = DatabaseManager.actualizar_campo_producto(
                producto['id_producto'],
                'DROP TABLE',  # Intento de inyección
                'valor'
            )
            
            assert resultado == False


class TestEliminarProducto:
    """Tests para eliminar_producto"""
    
    def test_eliminar_producto_existente(self, db_con_productos):
        """Eliminar producto que existe"""
        with patch('models.database.DB_PATH', db_con_productos):
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            
            resultado = DatabaseManager.eliminar_producto(producto['id_producto'])
            assert resultado == True
            
            # Verificar que se eliminó
            producto_eliminado = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            assert producto_eliminado is None
    
    def test_eliminar_producto_inexistente(self, clean_db):
        """Eliminar producto que no existe"""
        with patch('models.database.DB_PATH', clean_db):
            resultado = DatabaseManager.eliminar_producto(99999)
            assert resultado == False


class TestCalcularValorInventario:
    """Tests para calcular_valor_inventario"""
    
    def test_calcular_valor_con_productos(self, db_con_productos):
        """Calcular valor con productos en BD"""
        with patch('models.database.DB_PATH', db_con_productos):
            valor = DatabaseManager.calcular_valor_inventario()
            
            # Valor esperado:
            # Producto 1: 100 * 5000 = 500,000
            # Producto 2: 50 * 8000 * 1.19 = 476,000 (con IVA)
            # Producto 3: 5 * 3000 = 15,000
            # Total aproximado: 991,000
            
            assert valor > 0
            assert valor > 900000  # Aproximadamente
            assert valor < 1100000
    
    def test_calcular_valor_sin_productos(self, clean_db):
        """Calcular valor sin productos"""
        with patch('models.database.DB_PATH', clean_db):
            valor = DatabaseManager.calcular_valor_inventario()
            assert valor == 0.0
    
    def test_calcular_valor_incluye_iva(self, clean_db):
        """Verificar que incluye IVA en cálculo"""
        with patch('models.database.DB_PATH', clean_db):
            # Insertar producto con IVA
            datos = {
                'codigo_barras': 'TEST_IVA',
                'descripcion': 'PRODUCTO CON IVA',
                'cantidad': 10,
                'precio_compra': 1000.0,
                'impuesto': '19% IVA'
            }
            DatabaseManager.insertar_producto(datos)
            
            valor = DatabaseManager.calcular_valor_inventario()
            
            # Valor esperado: 10 * 1000 * 1.19 = 11,900
            assert valor == pytest.approx(11900.0, rel=0.01)


class TestObtenerTodosProductos:
    """Tests para obtener_todos_productos"""
    
    def test_obtener_productos_existentes(self, db_con_productos):
        """Obtener lista de todos los productos"""
        with patch('models.database.DB_PATH', db_con_productos):
            productos = DatabaseManager.obtener_todos_productos()
            
            assert len(productos) == 3
            assert isinstance(productos, list)
            assert isinstance(productos[0], tuple)
    
    def test_obtener_productos_vacio(self, clean_db):
        """Obtener productos cuando no hay ninguno"""
        with patch('models.database.DB_PATH', clean_db):
            productos = DatabaseManager.obtener_todos_productos()
            
            assert len(productos) == 0
            assert isinstance(productos, list)


# ============================================================
# TESTS DE INTEGRACIÓN
# ============================================================

class TestIntegracionDatabase:
    """Tests de integración del módulo database"""
    
    def test_ciclo_completo_producto(self, clean_db):
        """CRUD completo de un producto"""
        with patch('models.database.DB_PATH', clean_db):
            # CREATE
            datos = {
                'codigo_barras': 'CICLO001',
                'descripcion': 'PRODUCTO CICLO',
                'cantidad': 100,
                'precio_compra': 1000.0,
                'precio_venta': 1500.0
            }
            
            assert DatabaseManager.insertar_producto(datos) == True
            
            # READ
            producto = DatabaseManager.buscar_producto_por_codigo('CICLO001')
            assert producto is not None
            assert producto['cantidad'] == 100
            
            # UPDATE
            id_prod = producto['id_producto']
            assert DatabaseManager.actualizar_cantidad(id_prod, 150) == True
            assert DatabaseManager.actualizar_campo_producto(id_prod, 'precio_venta', 2000.0) == True
            
            producto_actualizado = DatabaseManager.buscar_producto_por_codigo('CICLO001')
            assert producto_actualizado['cantidad'] == 150
            assert producto_actualizado['precio_venta'] == 2000.0
            
            # DELETE
            assert DatabaseManager.eliminar_producto(id_prod) == True
            producto_eliminado = DatabaseManager.buscar_producto_por_codigo('CICLO001')
            assert producto_eliminado is None
    
    def test_multiples_operaciones_concurrentes(self, clean_db):
        """Múltiples operaciones en secuencia"""
        with patch('models.database.DB_PATH', clean_db):
            # Insertar varios productos
            for i in range(10):
                datos = {
                    'codigo_barras': f'MULTI{i:03d}',
                    'descripcion': f'PRODUCTO {i}',
                    'cantidad': i * 10,
                    'precio_compra': i * 1000.0
                }
                assert DatabaseManager.insertar_producto(datos) == True
            
            # Verificar todos se insertaron
            productos = DatabaseManager.obtener_todos_productos()
            assert len(productos) == 10
            
            # Buscar algunos
            resultados = DatabaseManager.buscar_productos_like('MULTI')
            assert len(resultados) == 10
