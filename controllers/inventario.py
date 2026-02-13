"""
Controlador de lógica de inventario
"""
from tkinter import messagebox
from models.database import DatabaseManager, get_db_connection
from utils.validators import (
    validate_codigo_barras,
    validate_cantidad,
    validate_precio,
    validate_fecha
)
from utils.formatters import parse_precio_text, clean_codigo_barras
import pandas as pd
import logging


class InventarioController:
    """Maneja la lógica de negocio del inventario"""

    @staticmethod
    def agregar_producto(datos: dict) -> bool:
        """Agrega un nuevo producto al inventario"""
        # Validaciones
        if not validate_codigo_barras(datos.get('codigo_barras', '')):
            messagebox.showerror("Error", "Código de barras inválido")
            return False

        if not datos.get('descripcion', '').strip():
            messagebox.showerror("Error", "La descripción es obligatoria")
            return False

        cantidad = validate_cantidad(str(datos.get('cantidad', '0')))
        if cantidad is None:
            messagebox.showerror("Error", "Cantidad inválida")
            return False

        precio_compra = validate_precio(str(datos.get('precio_compra', '0')))
        if precio_compra is None:
            messagebox.showerror("Error", "Precio de compra inválido")
            return False

        precio_venta = validate_precio(str(datos.get('precio_venta', '0')))
        if precio_venta is None:
            messagebox.showerror("Error", "Precio de venta inválido")
            return False

        if not validate_fecha(datos.get('fecha_vencimiento', '')):
            messagebox.showerror("Error", "Fecha de vencimiento inválida (formato: YYYY-MM-DD)")
            return False

        # Preparar datos validados
        datos_validados = {
            'codigo_barras': datos['codigo_barras'],
            'descripcion': datos['descripcion'],
            'proveedor': datos.get('proveedor', ''),
            'unidad': datos.get('unidad', ''),
            'cantidad': cantidad,
            'precio_compra': precio_compra,
            'precio_venta': precio_venta,
            'impuesto': datos.get('impuesto', ''),
            'bonificacion': validate_precio(str(datos.get('bonificacion', '0'))) or 0,
            'grupo': datos.get('grupo', ''),
            'subgrupo': datos.get('subgrupo', ''),
            'fecha_vencimiento': datos.get('fecha_vencimiento', '')
        }

        # Insertar en BD
        if DatabaseManager.insertar_producto(datos_validados):
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
            return True
        else:
            messagebox.showerror("Error", "No se pudo agregar el producto")
            return False

    @staticmethod
    def actualizar_producto_desde_excel(archivo_path: str) -> tuple:
        """
        Actualiza precios desde archivo Excel
        Returns: (actualizados, insertados)
        """
        try:
            df = pd.read_excel(archivo_path, dtype=str)

            # Normalizar nombres de columnas
            cols_norm = {c.lower().strip(): c for c in df.columns}

            def get_col(candidatos):
                for cand in candidatos:
                    key = cand.lower().strip()
                    if key in cols_norm:
                        return cols_norm[key]
                for key, orig in cols_norm.items():
                    for cand in candidatos:
                        if cand.lower().strip() in key:
                            return orig
                return None

            # Buscar columnas necesarias
            ean_col = get_col(["ean", "codigo de barras", "codigo_barras"])
            venta_col = get_col(["venta real", "ventareal", "precio compra", "precio_compra"])
            boni_col = get_col(["% boni", "bonificacion", "boni"])
            desc_col = get_col(["denominación", "descripcion"])
            prov_col = get_col(["proveedor"])
            und_col = get_col(["und", "unidad"])

            if not ean_col or not venta_col:
                messagebox.showerror("Error", "No se encontraron las columnas 'EAN' y 'Precio'")
                return (0, 0)

            # Limpiar códigos de barras
            df[ean_col] = df[ean_col].apply(clean_codigo_barras)

            # Convertir precios
            df[venta_col] = df[venta_col].apply(parse_precio_text)
            if boni_col:
                df[boni_col] = df[boni_col].apply(parse_precio_text)

            # Filtrar precios válidos
            df = df[df[venta_col].notna()]
            df = df[df[venta_col] >= 0]
            df = df.drop_duplicates(subset=[ean_col], keep="first")

            actualizados = 0
            insertados = 0

            with get_db_connection() as conn:
                cursor = conn.cursor()

                for _, fila in df.iterrows():
                    ean = str(fila[ean_col])
                    precio = float(fila[venta_col])
                    bonificacion = float(fila[boni_col]) if boni_col and pd.notna(fila[boni_col]) else 0
                    descripcion = str(fila[desc_col]) if desc_col and pd.notna(fila[desc_col]) else ""
                    proveedor = str(fila[prov_col]) if prov_col and pd.notna(fila[prov_col]) else ""
                    unidad = str(fila[und_col]) if und_col and pd.notna(fila[und_col]) else ""

                    # Verificar si existe
                    cursor.execute("SELECT id_producto FROM productos WHERE codigo_barras = ?", (ean,))
                    existe = cursor.fetchone()

                    if existe:
                        cursor.execute(
                            "UPDATE productos SET precio_compra = ?, bonificacion = ? WHERE codigo_barras = ?",
                            (precio, bonificacion, ean)
                        )
                        actualizados += 1
                    else:
                        cursor.execute("""
                            INSERT INTO productos 
                            (codigo_barras, descripcion, proveedor, unidad, cantidad, precio_compra, precio_venta, bonificacion)
                            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                        """, (ean, descripcion, proveedor, unidad, precio, precio, bonificacion))
                        insertados += 1

            return (actualizados, insertados)

        except Exception as e:
            logging.error(f"Error al actualizar desde Excel: {e}")
            messagebox.showerror("Error", f"No se pudo procesar el archivo:\n{e}")
            return (0, 0)

    @staticmethod
    def buscar_y_reemplazar_precios(texto_busqueda: str, nuevo_precio_compra: str, nuevo_precio_venta: str) -> int:
        """
        Busca productos y actualiza sus precios
        Returns: número de productos actualizados
        """
        if not texto_busqueda.strip():
            messagebox.showerror("Error", "Debe ingresar un texto de búsqueda")
            return 0

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Buscar coincidencias
                cursor.execute("""
                    SELECT id_producto, descripcion, precio_compra, precio_venta
                    FROM productos
                    WHERE LOWER(descripcion) LIKE ?
                """, (f"%{texto_busqueda.lower()}%",))

                resultados = cursor.fetchall()

                if not resultados:
                    messagebox.showinfo("Sin resultados", "No se encontraron productos")
                    return 0

                # Confirmar
                confirmar = messagebox.askyesno(
                    "Confirmar",
                    f"Se encontraron {len(resultados)} productos.\n¿Actualizar precios?"
                )

                if not confirmar:
                    return 0

                actualizados = 0

                for row in resultados:
                    id_prod = row[0]
                    precio_c = row[2]
                    precio_v = row[3]

                    # Actualizar solo si se proporcionó nuevo valor
                    if nuevo_precio_compra.strip():
                        precio_c = validate_precio(nuevo_precio_compra) or precio_c

                    if nuevo_precio_venta.strip():
                        precio_v = validate_precio(nuevo_precio_venta) or precio_v

                    cursor.execute("""
                        UPDATE productos
                        SET precio_compra = ?, precio_venta = ?
                        WHERE id_producto = ?
                    """, (precio_c, precio_v, id_prod))

                    actualizados += 1

                return actualizados

        except Exception as e:
            logging.error(f"Error en búsqueda y reemplazo: {e}")
            messagebox.showerror("Error", f"Error al actualizar precios: {e}")
            return 0
