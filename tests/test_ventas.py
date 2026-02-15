"""
Tests unitarios para controllers/ventas.py
"""
import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from controllers.ventas import VentasController


class TestAgregarProductoAVenta:
    """Tests para agregar_producto_a_venta"""
    
    def test_agregar_producto_valido(self, mock_tree, mock_entry, db_con_productos):
        """Agregar producto válido con stock suficiente"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Setup
            codigo_entry = mock_entry
            codigo_entry.set_value('7501234567890')
            
            cantidad_entry = MagicMock()
            cantidad_entry.get.return_value = '10'
            cantidad_entry.delete = MagicMock()
            
            # Ejecutar
            resultado = VentasController.agregar_producto_a_venta(
                mock_tree,
                codigo_entry,
                cantidad_entry
            )
            
            assert resultado == True
            assert len(mock_tree.get_children()) == 1
            
            # Verificar valores insertados
            item = mock_tree.item(mock_tree.get_children()[0])
            valores = item['values']
            assert valores[0] == '7501234567890'  # Código
            assert valores[2] == 10  # Cantidad
            assert valores[3] == 5000.0  # Precio unitario
            assert valores[4] == 50000.0  # Subtotal
    
    def test_agregar_producto_cantidad_default(self, mock_tree, mock_entry, db_con_productos):
        """Agregar producto sin especificar cantidad (default 1)"""
        with patch('models.database.DB_PATH', db_con_productos):
            codigo_entry = mock_entry
            codigo_entry.set_value('7501234567890')
            
            cantidad_entry = MagicMock()
            cantidad_entry.get.return_value = ''  # Vacío
            
            resultado = VentasController.agregar_producto_a_venta(
                mock_tree,
                codigo_entry,
                cantidad_entry
            )
            
            assert resultado == True
            item = mock_tree.item(mock_tree.get_children()[0])
            assert item['values'][2] == 1  # Cantidad default
    
    def test_agregar_producto_stock_insuficiente(self, mock_tree, mock_entry, db_con_productos):
        """Agregar producto con stock insuficiente"""
        with patch('models.database.DB_PATH', db_con_productos):
            with patch('tkinter.messagebox.showerror') as mock_error:
                codigo_entry = mock_entry
                codigo_entry.set_value('7501234567892')  # Producto con stock bajo (5)
                
                cantidad_entry = MagicMock()
                cantidad_entry.get.return_value = '10'  # Solicitar más del disponible
                
                resultado = VentasController.agregar_producto_a_venta(
                    mock_tree,
                    codigo_entry,
                    cantidad_entry
                )
                
                assert resultado == False
                assert len(mock_tree.get_children()) == 0
                mock_error.assert_called_once()
    
    def test_agregar_producto_no_existe(self, mock_tree, mock_entry, clean_db):
        """Agregar producto que no existe en BD"""
        with patch('models.database.DB_PATH', clean_db):
            with patch('tkinter.messagebox.showerror') as mock_error:
                codigo_entry = mock_entry
                codigo_entry.set_value('9999999999999')
                
                cantidad_entry = MagicMock()
                cantidad_entry.get.return_value = '1'
                
                resultado = VentasController.agregar_producto_a_venta(
                    mock_tree,
                    codigo_entry,
                    cantidad_entry
                )
                
                assert resultado == False
                mock_error.assert_called_once()
    
    def test_agregar_producto_codigo_invalido(self, mock_tree, mock_entry, clean_db):
        """Agregar producto con código inválido"""
        with patch('models.database.DB_PATH', clean_db):
            with patch('tkinter.messagebox.showerror') as mock_error:
                codigo_entry = mock_entry
                codigo_entry.set_value('CODIGO CON ESPACIOS')
                
                cantidad_entry = MagicMock()
                cantidad_entry.get.return_value = '1'
                
                resultado = VentasController.agregar_producto_a_venta(
                    mock_tree,
                    codigo_entry,
                    cantidad_entry
                )
                
                assert resultado == False
                mock_error.assert_called_once()
    
    def test_agregar_producto_cantidad_invalida(self, mock_tree, mock_entry, db_con_productos):
        """Agregar producto con cantidad inválida"""
        with patch('models.database.DB_PATH', db_con_productos):
            with patch('tkinter.messagebox.showerror') as mock_error:
                codigo_entry = mock_entry
                codigo_entry.set_value('7501234567890')
                
                cantidad_entry = MagicMock()
                cantidad_entry.get.return_value = 'ABC'  # No numérico
                
                resultado = VentasController.agregar_producto_a_venta(
                    mock_tree,
                    codigo_entry,
                    cantidad_entry
                )
                
                assert resultado == False
                mock_error.assert_called_once()
    
    def test_agregar_producto_advertencia_stock_bajo(self, mock_tree, mock_entry, db_con_productos):
        """Advertencia cuando queda poco stock después de la venta"""
        with patch('models.database.DB_PATH', db_con_productos):
            with patch('tkinter.messagebox.showwarning') as mock_warning:
                codigo_entry = mock_entry
                codigo_entry.set_value('7501234567892')  # Stock: 5
                
                cantidad_entry = MagicMock()
                cantidad_entry.get.return_value = '3'  # Quedarán 2
                
                resultado = VentasController.agregar_producto_a_venta(
                    mock_tree,
                    codigo_entry,
                    cantidad_entry
                )
                
                assert resultado == True
                mock_warning.assert_called_once()  # Debe mostrar advertencia


class TestRegistrarVenta:
    """Tests para registrar_venta"""
    
    def test_registrar_venta_exitosa(self, mock_tree, db_con_productos):
        """Registrar venta con productos válidos"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Agregar productos al tree
            mock_tree.insert("", "end", values=(
                '7501234567890',
                'ACETAMINOFEN 500MG',
                10,
                5000.0,
                50000.0,
                ''
            ))
            
            resultado = VentasController.registrar_venta(mock_tree)
            
            assert resultado == True
            
            # Verificar que se actualizó el inventario
            from models.database import DatabaseManager
            producto = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            assert producto['cantidad'] == 90  # 100 - 10
    
    def test_registrar_venta_multiple_productos(self, mock_tree, db_con_productos):
        """Registrar venta con múltiples productos"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Agregar varios productos
            mock_tree.insert("", "end", values=(
                '7501234567890', 'ACETAMINOFEN', 5, 5000.0, 25000.0, ''
            ))
            mock_tree.insert("", "end", values=(
                '7501234567891', 'IBUPROFENO', 3, 8000.0, 24000.0, '19% IVA'
            ))
            
            resultado = VentasController.registrar_venta(mock_tree)
            
            assert resultado == True
            
            # Verificar inventario actualizado
            from models.database import DatabaseManager
            prod1 = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            prod2 = DatabaseManager.buscar_producto_por_codigo('7501234567891')
            
            assert prod1['cantidad'] == 95  # 100 - 5
            assert prod2['cantidad'] == 47  # 50 - 3
    
    def test_registrar_venta_sin_productos(self, mock_tree, clean_db):
        """Intentar registrar venta sin productos"""
        with patch('models.database.DB_PATH', clean_db):
            with patch('tkinter.messagebox.showwarning') as mock_warning:
                resultado = VentasController.registrar_venta(mock_tree)
                
                assert resultado == False
                mock_warning.assert_called_once()
    
    def test_registrar_venta_guarda_en_tabla_ventas(self, mock_tree, db_con_productos):
        """Verificar que se guarda en tabla ventas"""
        with patch('models.database.DB_PATH', db_con_productos):
            mock_tree.insert("", "end", values=(
                '7501234567890', 'ACETAMINOFEN', 5, 5000.0, 25000.0, ''
            ))
            
            resultado = VentasController.registrar_venta(mock_tree)
            
            assert resultado == True
            
            # Verificar en tabla ventas
            from models.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ventas")
                ventas = cursor.fetchall()
                
                assert len(ventas) == 1
                assert ventas[0]['total'] == 25000.0
                
                # Verificar productos JSON
                productos = json.loads(ventas[0]['productos'])
                assert len(productos) == 1
                assert productos[0]['codigo'] == '7501234567890'
    
    def test_registrar_venta_stock_insuficiente_durante_registro(self, mock_tree, db_con_productos):
        """Venta falla si stock insuficiente durante registro (race condition)"""
        with patch('models.database.DB_PATH', db_con_productos):
            with patch('tkinter.messagebox.showerror') as mock_error:
                # Agregar producto solicitando todo el stock
                mock_tree.insert("", "end", values=(
                    '7501234567892',  # Stock: 5
                    'LORATADINA',
                    10,  # Más del disponible
                    3000.0,
                    30000.0,
                    ''
                ))
                
                resultado = VentasController.registrar_venta(mock_tree)
                
                assert resultado == False
                mock_error.assert_called_once()


class TestObtenerHistorialVentas:
    """Tests para obtener_historial_ventas"""
    
    def test_obtener_historial_con_ventas(self, mock_tree, db_con_productos):
        """Obtener historial con ventas registradas"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Registrar una venta primero
            mock_tree.insert("", "end", values=(
                '7501234567890', 'ACETAMINOFEN', 5, 5000.0, 25000.0, ''
            ))
            VentasController.registrar_venta(mock_tree)
            
            # Obtener historial
            ventas = VentasController.obtener_historial_ventas(limite=10)
            
            assert len(ventas) == 1
            assert ventas[0]['total'] == 25000.0
            assert len(ventas[0]['productos']) == 1
    
    def test_obtener_historial_sin_ventas(self, clean_db):
        """Obtener historial sin ventas"""
        with patch('models.database.DB_PATH', clean_db):
            ventas = VentasController.obtener_historial_ventas()
            
            assert len(ventas) == 0
            assert isinstance(ventas, list)
    
    def test_obtener_historial_respeta_limite(self, mock_tree, db_con_productos):
        """Historial respeta el límite especificado"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Registrar múltiples ventas
            for i in range(5):
                mock_tree._items = []  # Limpiar tree
                mock_tree.insert("", "end", values=(
                    '7501234567890', 'ACETAMINOFEN', 1, 5000.0, 5000.0, ''
                ))
                VentasController.registrar_venta(mock_tree)
            
            # Obtener con límite
            ventas = VentasController.obtener_historial_ventas(limite=3)
            
            assert len(ventas) == 3


class TestObtenerVentaPorId:
    """Tests para obtener_venta_por_id"""
    
    def test_obtener_venta_existente(self, mock_tree, db_con_productos):
        """Obtener venta por ID existente"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Registrar venta
            mock_tree.insert("", "end", values=(
                '7501234567890', 'ACETAMINOFEN', 5, 5000.0, 25000.0, ''
            ))
            VentasController.registrar_venta(mock_tree)
            
            # Obtener por ID
            venta = VentasController.obtener_venta_por_id(1)
            
            assert venta is not None
            assert venta['id'] == 1
            assert venta['total'] == 25000.0
    
    def test_obtener_venta_inexistente(self, clean_db):
        """Obtener venta por ID inexistente"""
        with patch('models.database.DB_PATH', clean_db):
            venta = VentasController.obtener_venta_por_id(99999)
            
            assert venta is None


class TestCalcularTotalVentasPeriodo:
    """Tests para calcular_total_ventas_periodo"""
    
    def test_calcular_periodo_con_ventas(self, mock_tree, db_con_productos):
        """Calcular totales de un período con ventas"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Registrar ventas
            for i in range(3):
                mock_tree._items = []
                mock_tree.insert("", "end", values=(
                    '7501234567890', 'ACETAMINOFEN', 1, 5000.0, 5000.0, ''
                ))
                VentasController.registrar_venta(mock_tree)
            
            # Calcular totales
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            totales = VentasController.calcular_total_ventas_periodo(
                fecha_hoy,
                fecha_hoy
            )
            
            assert totales['num_ventas'] == 3
            assert totales['total_ventas'] == 15000.0
            assert totales['promedio_venta'] == 5000.0
    
    def test_calcular_periodo_sin_ventas(self, clean_db):
        """Calcular totales de período sin ventas"""
        with patch('models.database.DB_PATH', clean_db):
            totales = VentasController.calcular_total_ventas_periodo(
                '2026-01-01',
                '2026-01-31'
            )
            
            assert totales['num_ventas'] == 0
            assert totales['total_ventas'] == 0.0
            assert totales['promedio_venta'] == 0.0


# ============================================================
# TESTS DE INTEGRACIÓN
# ============================================================

class TestIntegracionVentas:
    """Tests de integración del módulo de ventas"""
    
    def test_flujo_completo_venta(self, mock_tree, db_con_productos):
        """Flujo completo: agregar productos y registrar venta"""
        with patch('models.database.DB_PATH', db_con_productos):
            # Setup
            codigo_entry1 = MagicMock()
            codigo_entry1.get.return_value = '7501234567890'
            codigo_entry1.delete = MagicMock()
            
            cantidad_entry1 = MagicMock()
            cantidad_entry1.get.return_value = '5'
            cantidad_entry1.delete = MagicMock()
            
            # Agregar primer producto
            resultado1 = VentasController.agregar_producto_a_venta(
                mock_tree,
                codigo_entry1,
                cantidad_entry1
            )
            assert resultado1 == True
            
            # Agregar segundo producto
            codigo_entry2 = MagicMock()
            codigo_entry2.get.return_value = '7501234567891'
            codigo_entry2.delete = MagicMock()
            
            cantidad_entry2 = MagicMock()
            cantidad_entry2.get.return_value = '3'
            cantidad_entry2.delete = MagicMock()
            
            resultado2 = VentasController.agregar_producto_a_venta(
                mock_tree,
                codigo_entry2,
                cantidad_entry2
            )
            assert resultado2 == True
            
            # Verificar que hay 2 productos en el tree
            assert len(mock_tree.get_children()) == 2
            
            # Registrar venta
            resultado_venta = VentasController.registrar_venta(mock_tree)
            assert resultado_venta == True
            
            # Verificar inventario actualizado
            from models.database import DatabaseManager
            prod1 = DatabaseManager.buscar_producto_por_codigo('7501234567890')
            prod2 = DatabaseManager.buscar_producto_por_codigo('7501234567891')
            
            assert prod1['cantidad'] == 95  # 100 - 5
            assert prod2['cantidad'] == 47  # 50 - 3
            
            # Verificar venta registrada
            ventas = VentasController.obtener_historial_ventas()
            assert len(ventas) == 1
            assert len(ventas[0]['productos']) == 2
