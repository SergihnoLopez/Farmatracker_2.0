"""
Controlador de lógica de ventas
✅ MEJORADO: Validación de stock bloqueante + Registro completo de ventas
"""
from tkinter import messagebox
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_cantidad, validate_codigo_barras
from datetime import datetime
import json
import logging


class VentasController:
    """Maneja la lógica de negocio de ventas"""

    @staticmethod
    def agregar_producto_a_venta(tree, codigo_entry, cantidad_entry):
        """
        Agrega un producto al treeview de venta
        ✅ MEJORADO: Validación de stock bloqueante
        """
        codigo = codigo_entry.get().strip()
        cantidad_str = cantidad_entry.get().strip() or "1"

        # Validaciones
        if not validate_codigo_barras(codigo):
            messagebox.showerror("Error", "Código de barras inválido")
            return False

        cantidad = validate_cantidad(cantidad_str)
        if cantidad is None:
            messagebox.showerror("Error", "Cantidad inválida")
            return False

        # Buscar producto
        producto = DatabaseManager.buscar_producto_por_codigo(codigo)

        if not producto:
            messagebox.showerror("Error", f"Producto no encontrado: {codigo}")
            return False

        # ✅ VALIDACIÓN DE STOCK BLOQUEANTE
        stock_disponible = producto['cantidad']

        if stock_disponible < cantidad:
            messagebox.showerror(
                "Stock Insuficiente",
                f"❌ NO HAY STOCK SUFICIENTE\n\n"
                f"Producto: {producto['descripcion']}\n"
                f"Stock disponible: {stock_disponible} unidades\n"
                f"Cantidad solicitada: {cantidad} unidades\n\n"
                f"Diferencia: Faltan {cantidad - stock_disponible} unidades\n\n"
                "La venta NO puede continuar."
            )
            return False

        # Advertencia si queda poco stock después de la venta
        stock_restante = stock_disponible - cantidad
        if stock_restante > 0 and stock_restante <= 5:
            messagebox.showwarning(
                "⚠️ Stock Bajo",
                f"Después de esta venta quedarán solo {stock_restante} unidades.\n\n"
                f"Considera hacer un pedido pronto."
            )

        # Calcular subtotal
        precio_unitario = float(producto['precio_venta'])
        subtotal = precio_unitario * cantidad

        # Agregar al treeview
        tree.insert("", "end", values=(
            producto['codigo_barras'],
            producto['descripcion'],
            cantidad,
            precio_unitario,
            subtotal,
            producto.get('impuesto', '')
        ))

        # Limpiar campos
        codigo_entry.delete(0, 'end')
        cantidad_entry.delete(0, 'end')

        return True

    @staticmethod
    def registrar_venta(tree):
        """
        Registra la venta y actualiza inventario
        ✅ MEJORADO: Registra en tabla ventas + validaciones adicionales
        """
        items = tree.get_children()

        if not items:
            messagebox.showwarning("Advertencia", "No hay productos en la venta")
            return False

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Calcular total y preparar detalles de venta
                total = 0.0
                productos_venta = []

                # ✅ VALIDACIÓN PREVIA: Verificar stock de todos los productos
                for item in items:
                    valores = tree.item(item, "values")
                    codigo = valores[0]
                    cantidad_vendida = int(valores[2])

                    # Verificar stock actual antes de proceder
                    cursor.execute(
                        "SELECT cantidad FROM productos WHERE codigo_barras = ?",
                        (codigo,)
                    )
                    row = cursor.fetchone()

                    if not row or row[0] < cantidad_vendida:
                        stock_actual = row[0] if row else 0
                        messagebox.showerror(
                            "Error de Stock",
                            f"❌ Stock insuficiente para {codigo}\n\n"
                            f"Stock actual: {stock_actual}\n"
                            f"Cantidad requerida: {cantidad_vendida}\n\n"
                            "La venta ha sido CANCELADA."
                        )
                        return False

                    # Acumular total y detalles
                    subtotal = float(valores[4])
                    total += subtotal

                    productos_venta.append({
                        'codigo': codigo,
                        'descripcion': valores[1],
                        'cantidad': cantidad_vendida,
                        'precio_unitario': float(valores[3]),
                        'subtotal': subtotal,
                        'impuesto': valores[5] if len(valores) > 5 else ''
                    })

                # ✅ REGISTRAR VENTA EN TABLA VENTAS
                productos_json = json.dumps(productos_venta, ensure_ascii=False)
                fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute("""
                    INSERT INTO ventas (fecha, total, productos, cajero)
                    VALUES (?, ?, ?, 'Principal')
                """, (fecha_actual, total, productos_json))

                venta_id = cursor.lastrowid
                logging.info(f"Venta registrada - ID: {venta_id}, Total: ${total:,.2f}")

                # ✅ ACTUALIZAR INVENTARIO
                productos_actualizados = 0
                for producto in productos_venta:
                    cursor.execute("""
                        UPDATE productos 
                        SET cantidad = cantidad - ? 
                        WHERE codigo_barras = ? AND cantidad >= ?
                    """, (producto['cantidad'], producto['codigo'], producto['cantidad']))

                    if cursor.rowcount == 0:
                        raise Exception(
                            f"Error al actualizar stock de {producto['codigo']} - "
                            f"Posible venta concurrente"
                        )

                    productos_actualizados += 1

                logging.info(
                    f"Venta completada - ID: {venta_id}, "
                    f"Productos: {productos_actualizados}, "
                    f"Total: ${total:,.2f}"
                )

                return True

        except Exception as e:
            logging.error(f"Error al registrar venta: {e}", exc_info=True)
            messagebox.showerror(
                "Error al Registrar Venta",
                f"No se pudo completar la venta:\n\n{str(e)}\n\n"
                "La transacción ha sido revertida.\n"
                "El inventario NO fue modificado."
            )
            return False

    @staticmethod
    def obtener_historial_ventas(limite: int = 100):
        """
        ✅ NUEVO: Obtiene el historial de ventas registradas

        Args:
            limite: Número máximo de ventas a retornar

        Returns:
            Lista de ventas con sus detalles
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id_venta, fecha, total, productos, cajero
                    FROM ventas
                    ORDER BY fecha DESC
                    LIMIT ?
                """, (limite,))

                ventas = []
                for row in cursor.fetchall():
                    venta = {
                        'id': row[0],
                        'fecha': row[1],
                        'total': row[2],
                        'productos': json.loads(row[3]) if row[3] else [],
                        'cajero': row[4]
                    }
                    ventas.append(venta)

                return ventas

        except Exception as e:
            logging.error(f"Error al obtener historial de ventas: {e}")
            return []

    @staticmethod
    def obtener_venta_por_id(venta_id: int):
        """
        ✅ NUEVO: Obtiene detalles de una venta específica

        Args:
            venta_id: ID de la venta

        Returns:
            Diccionario con detalles de la venta o None
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id_venta, fecha, total, productos, cajero
                    FROM ventas
                    WHERE id_venta = ?
                """, (venta_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'fecha': row[1],
                        'total': row[2],
                        'productos': json.loads(row[3]) if row[3] else [],
                        'cajero': row[4]
                    }
                return None

        except Exception as e:
            logging.error(f"Error al obtener venta {venta_id}: {e}")
            return None

    @staticmethod
    def calcular_total_ventas_periodo(fecha_inicio: str, fecha_fin: str):
        """
        ✅ NUEVO: Calcula el total de ventas en un período

        Args:
            fecha_inicio: Fecha inicio en formato 'YYYY-MM-DD'
            fecha_fin: Fecha fin en formato 'YYYY-MM-DD'

        Returns:
            Diccionario con total, cantidad de ventas, etc.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as num_ventas,
                        SUM(total) as total_ventas,
                        AVG(total) as promedio_venta
                    FROM ventas
                    WHERE fecha BETWEEN ? AND ?
                """, (fecha_inicio + ' 00:00:00', fecha_fin + ' 23:59:59'))

                row = cursor.fetchone()

                return {
                    'num_ventas': row[0] or 0,
                    'total_ventas': row[1] or 0.0,
                    'promedio_venta': row[2] or 0.0,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                }

        except Exception as e:
            logging.error(f"Error al calcular totales del período: {e}")
            return {
                'num_ventas': 0,
                'total_ventas': 0.0,
                'promedio_venta': 0.0,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
