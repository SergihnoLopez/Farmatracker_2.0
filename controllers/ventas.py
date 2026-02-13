"""
Controlador de lógica de ventas
"""
from tkinter import messagebox
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_cantidad, validate_codigo_barras
import logging


class VentasController:
    """Maneja la lógica de negocio de ventas"""

    @staticmethod
    def agregar_producto_a_venta(tree, codigo_entry, cantidad_entry):
        """Agrega un producto al treeview de venta"""
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

        # Verificar stock
        if producto['cantidad'] < cantidad:
            messagebox.showwarning(
                "Stock insuficiente",
                f"Solo hay {producto['cantidad']} unidades disponibles"
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
        """Registra la venta y actualiza inventario"""
        items = tree.get_children()

        if not items:
            messagebox.showwarning("Advertencia", "No hay productos en la venta")
            return False

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                for item in items:
                    valores = tree.item(item, "values")
                    codigo = valores[0]
                    cantidad_vendida = int(valores[2])

                    # Actualizar stock
                    cursor.execute("""
                        UPDATE productos 
                        SET cantidad = cantidad - ? 
                        WHERE codigo_barras = ? AND cantidad >= ?
                    """, (cantidad_vendida, codigo, cantidad_vendida))

                    if cursor.rowcount == 0:
                        raise Exception(f"Stock insuficiente para {codigo}")

                # Limpiar treeview
                tree.delete(*items)

                return True

        except Exception as e:
            logging.error(f"Error al registrar venta: {e}")
            messagebox.showerror("Error", f"No se pudo registrar la venta:\n{e}")
            return False