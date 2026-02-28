"""
Controlador de lógica de ventas
✅ MEJORADO: Validación de stock bloqueante + Registro completo de ventas
✅ NUEVO: Soporte para cantidades decimales (fraccionamiento de productos CJ)
"""
from tkinter import messagebox
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_codigo_barras
from datetime import datetime
import json
import logging


def _parse_cantidad(valor_str) -> float | None:
    """
    Convierte el valor de cantidad a float.
    Acepta enteros (3) y decimales (0.1, 0.333...) para fracciones de CJ.
    Retorna None si el valor es inválido.
    """
    try:
        v = float(str(valor_str).strip())
        if v <= 0:
            return None
        return v
    except (ValueError, TypeError):
        return None


class VentasController:
    """Maneja la lógica de negocio de ventas"""

    @staticmethod
    def agregar_producto_a_venta(tree, codigo_entry, cantidad_entry):
        """
        Agrega un producto al treeview de venta.
        ✅ MEJORADO: Validación de stock bloqueante.
        ✅ NUEVO: Cantidad acepta decimales para fraccionamiento CJ.
        """
        codigo = codigo_entry.get().strip()
        cantidad_str = cantidad_entry.get().strip() or "1"

        # Validaciones
        if not validate_codigo_barras(codigo):
            messagebox.showerror("Error", "Código de barras inválido")
            return False

        cantidad = _parse_cantidad(cantidad_str)
        if cantidad is None:
            messagebox.showerror("Error", "Cantidad inválida")
            return False

        # Buscar producto
        producto = DatabaseManager.buscar_producto_por_codigo(codigo)

        if not producto:
            messagebox.showerror("Error", f"Producto no encontrado: {codigo}")
            return False

        # ✅ VALIDACIÓN DE STOCK BLOQUEANTE
        stock_disponible = float(producto['cantidad'])

        if stock_disponible < cantidad:
            messagebox.showerror(
                "Stock Insuficiente",
                f"❌ NO HAY STOCK SUFICIENTE\n\n"
                f"Producto: {producto['descripcion']}\n"
                f"Stock disponible: {stock_disponible} unidades\n"
                f"Cantidad solicitada: {cantidad} unidades\n\n"
                f"Diferencia: Faltan {cantidad - stock_disponible:.3f} unidades\n\n"
                "La venta NO puede continuar."
            )
            return False

        # Calcular subtotal
        precio_unitario = float(producto['precio_venta'])
        subtotal = precio_unitario * cantidad

        # Agregar al treeview
        # Mostrar cantidad: si es entero exacto, sin decimales; si es fracción, con decimales
        cantidad_display = int(cantidad) if cantidad == int(cantidad) else round(cantidad, 6)

        tree.insert("", "end", values=(
            producto['codigo_barras'],
            producto['descripcion'],
            cantidad_display,
            precio_unitario,
            subtotal,
            producto.get('impuesto', ''),
            ''  # kit_data vacío para productos normales
        ))

        # Limpiar campos
        codigo_entry.delete(0, 'end')
        cantidad_entry.delete(0, 'end')

        return True

    @staticmethod
    def registrar_venta(tree):
        """
        Registra la venta y actualiza inventario.
        ✅ MEJORADO: Registra en tabla ventas + validaciones adicionales.
        ✅ NUEVO: Soporta cantidades decimales para fracciones de CJ.
        ✅ SERVICIOS: Códigos SVC-* no afectan inventario (sin stock check).
        ✅ KITS: Los componentes se validan y descuentan aquí (no en kit_window).
        """
        items = tree.get_children()

        if not items:
            messagebox.showwarning("Advertencia", "No hay productos en la venta")
            return False

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # ── Fase 1: Leer y validar todos los items del treeview ──────
                total = 0.0
                productos_venta = []

                for item in items:
                    valores = tree.item(item, "values")
                    codigo  = valores[0]
                    es_kit  = str(codigo) == "KIT"
                    es_svc  = str(codigo).startswith("SVC-")

                    if es_kit:
                        # ── Validar stock de cada componente del kit ─────────
                        kit_data_str = valores[6] if len(valores) > 6 else ""
                        if not kit_data_str:
                            messagebox.showerror(
                                "Error de Kit",
                                "El kit no tiene datos de componentes.\n"
                                "Elimine el kit y vuelva a armarlo."
                            )
                            return False

                        try:
                            componentes = json.loads(kit_data_str)
                        except Exception:
                            messagebox.showerror(
                                "Error de Kit",
                                "Los datos del kit están corruptos.\n"
                                "Elimine el kit y vuelva a armarlo."
                            )
                            return False

                        for comp in componentes:
                            cod_comp  = comp["codigo"]
                            desc_comp = comp.get("descripcion", cod_comp)
                            req       = float(comp["descuento_cajas"])
                            cursor.execute(
                                "SELECT cantidad FROM productos WHERE codigo_barras = ?",
                                (cod_comp,)
                            )
                            row = cursor.fetchone()
                            stock_actual = float(row[0]) if row else 0.0
                            if not row or stock_actual < req:
                                messagebox.showerror(
                                    "Stock Insuficiente — Componente de Kit",
                                    f"❌ No hay stock suficiente para armar el kit.\n\n"
                                    f"Componente: {desc_comp}\n"
                                    f"Stock disponible: {stock_actual:.4f}\n"
                                    f"Cantidad requerida: {req:.6f}\n\n"
                                    "La venta ha sido CANCELADA."
                                )
                                return False

                        subtotal   = float(valores[4])
                        total     += subtotal
                        # Costo base = suma de costo_prop de cada componente
                        # Esto permite al reporte calcular la utilidad real del kit
                        costo_base = sum(float(c.get('costo_prop', 0)) for c in componentes)
                        utilidad   = subtotal - costo_base
                        pct_util   = (utilidad / subtotal * 100) if subtotal > 0 else 0.0
                        productos_venta.append({
                            'codigo':          'KIT',
                            'descripcion':     valores[1],
                            'cantidad':        1,
                            'precio_unitario': float(valores[3]),
                            'precio_compra':   round(costo_base, 2),
                            'costo_base':      round(costo_base, 2),
                            'subtotal':        subtotal,
                            'utilidad':        round(utilidad, 2),
                            'utilidad_pct':    round(pct_util, 2),
                            'impuesto':        'KIT',
                            'es_kit':          True,
                            'componentes':     componentes,
                        })

                    elif es_svc:
                        subtotal = float(valores[4])
                        total   += subtotal
                        productos_venta.append({
                            'codigo':          codigo,
                            'descripcion':     valores[1],
                            'cantidad':        _parse_cantidad(valores[2]) or 1,
                            'precio_unitario': float(valores[3]),
                            'subtotal':        subtotal,
                            'impuesto':        valores[5] if len(valores) > 5 else '',
                            'es_kit':          False,
                        })

                    else:
                        # ── Producto normal ───────────────────────────────────
                        cantidad_vendida = _parse_cantidad(valores[2])
                        if cantidad_vendida is None:
                            messagebox.showerror(
                                "Error de datos",
                                f"Cantidad inválida para el producto {codigo}"
                            )
                            return False

                        cursor.execute(
                            "SELECT cantidad FROM productos WHERE codigo_barras = ?",
                            (codigo,)
                        )
                        row = cursor.fetchone()
                        if not row or float(row[0]) < cantidad_vendida:
                            stock_actual = float(row[0]) if row else 0
                            messagebox.showerror(
                                "Error de Stock",
                                f"❌ Stock insuficiente para {codigo}\n\n"
                                f"Stock actual: {stock_actual:.3f}\n"
                                f"Cantidad requerida: {cantidad_vendida:.3f}\n\n"
                                "La venta ha sido CANCELADA."
                            )
                            return False

                        subtotal = float(valores[4])
                        total   += subtotal
                        productos_venta.append({
                            'codigo':          codigo,
                            'descripcion':     valores[1],
                            'cantidad':        cantidad_vendida,
                            'precio_unitario': float(valores[3]),
                            'subtotal':        subtotal,
                            'impuesto':        valores[5] if len(valores) > 5 else '',
                            'es_kit':          False,
                        })

                # ── Fase 2: Registrar venta en tabla ventas ──────────────────
                productos_json = json.dumps(productos_venta, ensure_ascii=False)
                fecha_actual   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute("""
                    INSERT INTO ventas (fecha, total, productos, cajero)
                    VALUES (?, ?, ?, 'Principal')
                """, (fecha_actual, total, productos_json))

                venta_id = cursor.lastrowid
                logging.info(f"Venta registrada - ID: {venta_id}, Total: ${total:,.2f}")

                # ── Fase 3: Descontar inventario ─────────────────────────────
                productos_actualizados = 0

                for producto in productos_venta:
                    if producto.get('es_kit'):
                        # Descontar cada componente del kit
                        for comp in producto.get('componentes', []):
                            cod_comp = comp["codigo"]
                            req      = float(comp["descuento_cajas"])
                            cursor.execute("""
                                UPDATE productos
                                SET cantidad = ROUND(cantidad - ?, 8)
                                WHERE codigo_barras = ? AND cantidad >= ?
                            """, (req, cod_comp, req))
                            if cursor.rowcount == 0:
                                raise Exception(
                                    f"Error al descontar componente de kit: "
                                    f"{comp.get('descripcion', cod_comp)} — "
                                    f"posible venta concurrente"
                                )
                            productos_actualizados += 1
                            logging.info(
                                f"Componente de kit descontado: "
                                f"{cod_comp} -{req:.6f}"
                            )

                    elif not str(producto['codigo']).startswith("SVC-"):
                        # Producto normal
                        cursor.execute("""
                            UPDATE productos 
                            SET cantidad = cantidad - ? 
                            WHERE codigo_barras = ? AND cantidad >= ?
                        """, (
                            producto['cantidad'],
                            producto['codigo'],
                            producto['cantidad']
                        ))
                        if cursor.rowcount == 0:
                            raise Exception(
                                f"Error al actualizar stock de {producto['codigo']} — "
                                f"posible venta concurrente"
                            )
                        productos_actualizados += 1
                    else:
                        logging.info(
                            f"Servicio registrado (sin stock): {producto['codigo']}"
                        )

                logging.info(
                    f"Venta completada - ID: {venta_id}, "
                    f"Movimientos de inventario: {productos_actualizados}, "
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
    def obtener_historial_ventas(limite: int = 50):
        """Obtiene el historial de ventas"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id_venta, fecha, total, productos, cajero
                    FROM ventas
                    ORDER BY id_venta DESC
                    LIMIT ?
                """, (limite,))

                rows = cursor.fetchall()
                ventas = []
                for row in rows:
                    try:
                        productos = json.loads(row['productos']) if row['productos'] else []
                    except Exception:
                        productos = []

                    ventas.append({
                        'id':          row['id_venta'],
                        'fecha':       row['fecha'],
                        'total':       float(row['total']),
                        'productos':   productos,
                        'cajero':      row['cajero'],
                        'n_productos': len(productos)
                    })

                return ventas

        except Exception as e:
            logging.error(f"Error al obtener historial: {e}")
            return []

    @staticmethod
    def obtener_venta_por_id(id_venta: int):
        """Obtiene una venta específica por ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM ventas WHERE id_venta = ?",
                    (id_venta,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                try:
                    productos = json.loads(row['productos']) if row['productos'] else []
                except Exception:
                    productos = []

                return {
                    'id':        row['id_venta'],
                    'fecha':     row['fecha'],
                    'total':     float(row['total']),
                    'productos': productos,
                    'cajero':    row['cajero']
                }

        except Exception as e:
            logging.error(f"Error al obtener venta {id_venta}: {e}")
            return None