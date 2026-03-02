"""
Controlador de lógica de inventario
✅ CORREGIDO: Actualización desde Excel con mapeo correcto
✅ CORREGIDO: Soporte para archivos .xls y .xlsx
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
        ✅ CORREGIDO: Actualiza productos desde archivo Excel con mapeo correcto
        ✅ CORREGIDO: Soporte para archivos .xls (antiguos) y .xlsx (modernos)

        Mapeo Excel → Base de datos:
        - EAN → codigo_barras
        - Denominación → descripcion
        - Cantidad → cantidad
        - Venta Real → precio_compra
        - Impuesto → impuesto
        - Grupo → grupo
        - SubGrupo → subgrupo
        - Proveedor → proveedor
        - UND → unidad
        - % Boni → bonificacion

        Lógica:
        - Si EAN existe: actualizar solo descripcion y precio_compra
        - Si EAN NO existe: insertar con todos los campos

        Returns: (actualizados, insertados, errores)
        """
        try:
            # ✅ DETECTAR FORMATO Y LEER CON ENGINE CORRECTO
            import os
            extension = os.path.splitext(archivo_path)[1].lower()

            if extension == '.xls':
                # Archivo .xls antiguo - intentar convertir o leer con xlrd si está disponible
                try:
                    # Intentar con xlrd si está instalado
                    df = pd.read_excel(archivo_path, dtype=str, engine='xlrd')
                    logging.info("Archivo .xls leído con xlrd")
                except ImportError:
                    # xlrd no disponible - sugerir conversión
                    messagebox.showerror(
                        "Formato No Soportado",
                        "El archivo es formato .xls (Excel antiguo).\n\n"
                        "Por favor:\n"
                        "1. Abra el archivo en Excel\n"
                        "2. Guárdelo como .xlsx (Excel moderno)\n"
                        "3. Intente de nuevo\n\n"
                        "O instale xlrd:\n"
                        "pip install xlrd"
                    )
                    logging.error("Archivo .xls pero xlrd no está instalado")
                    return (0, 0, 0)
            elif extension == '.xlsx':
                # Archivo .xlsx moderno - usar openpyxl (ya instalado)
                df = pd.read_excel(archivo_path, dtype=str, engine='openpyxl')
                logging.info("Archivo .xlsx leído con openpyxl")
            else:
                messagebox.showerror(
                    "Formato Desconocido",
                    f"Formato de archivo no soportado: {extension}\n\n"
                    "Use archivos .xlsx o .xls"
                )
                return (0, 0, 0)

            logging.info(f"Columnas encontradas en Excel: {list(df.columns)}")

            # Normalizar nombres de columnas (quitar espacios, minúsculas)
            df.columns = df.columns.str.strip()

            # Verificar columnas obligatorias
            columnas_requeridas = ['EAN', 'Denominación', 'Venta Real']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                messagebox.showerror(
                    "Error",
                    f"Columnas faltantes en el Excel:\n{', '.join(columnas_faltantes)}\n\n"
                    f"Columnas requeridas: {', '.join(columnas_requeridas)}"
                )
                return (0, 0, 0)

            # Limpiar códigos de barras
            df['EAN'] = df['EAN'].apply(clean_codigo_barras)

            # Filtrar filas con EAN vacío
            df = df[df['EAN'].notna()]
            df = df[df['EAN'] != '']

            # Convertir precios y números
            df['Venta Real'] = df['Venta Real'].apply(parse_precio_text)

            # Convertir cantidad a entero
            if 'Cantidad' in df.columns:
                df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(int)

            # Convertir bonificación
            if '% Boni' in df.columns:
                df['% Boni'] = df['% Boni'].apply(parse_precio_text)

            # Filtrar filas con precio válido
            df = df[df['Venta Real'].notna()]
            df = df[df['Venta Real'] >= 0]

            # Eliminar duplicados (mantener el primero)
            df = df.drop_duplicates(subset=['EAN'], keep='first')

            logging.info(f"Filas válidas a procesar: {len(df)}")

            actualizados = 0
            insertados = 0
            errores = 0

            with get_db_connection() as conn:
                cursor = conn.cursor()

                for idx, fila in df.iterrows():
                    try:
                        # Extraer datos con mapeo correcto
                        ean = str(fila['EAN']).strip()
                        denominacion = str(fila.get('Denominación', '')).strip() if pd.notna(fila.get('Denominación')) else ''
                        venta_real = float(fila['Venta Real'])

                        # Campos opcionales
                        cantidad = int(fila.get('Cantidad', 0)) if 'Cantidad' in fila and pd.notna(fila.get('Cantidad')) else 0
                        proveedor = str(fila.get('Proveedor', '')).strip() if pd.notna(fila.get('Proveedor')) else ''
                        unidad = str(fila.get('UND', '')).strip() if pd.notna(fila.get('UND')) else ''
                        impuesto = str(fila.get('Impuesto', '')).strip() if pd.notna(fila.get('Impuesto')) else ''
                        bonificacion = float(fila.get('% Boni', 0)) if '% Boni' in fila and pd.notna(fila.get('% Boni')) else 0
                        grupo = str(fila.get('Grupo', '')).strip() if pd.notna(fila.get('Grupo')) else ''
                        subgrupo = str(fila.get('SubGrupo', '')).strip() if pd.notna(fila.get('SubGrupo')) else ''

                        # Validar EAN
                        if not ean or len(ean) < 8:
                            logging.warning(f"Fila {idx}: EAN inválido '{ean}', omitiendo")
                            errores += 1
                            continue

                        # Verificar si existe
                        cursor.execute(
                            "SELECT id_producto FROM productos WHERE codigo_barras = ?",
                            (ean,)
                        )
                        existe = cursor.fetchone()

                        if existe:
                            # ✅ SI EXISTE: Actualizar SOLO descripcion y precio_compra
                            cursor.execute("""
                                UPDATE productos 
                                SET descripcion = ?,
                                    precio_compra = ?
                                WHERE codigo_barras = ?
                            """, (denominacion, venta_real, ean))

                            actualizados += 1
                            logging.debug(f"Actualizado: {ean} - {denominacion}")

                        else:
                            # ✅ NO EXISTE: Insertar con todos los campos
                            cursor.execute("""
                                INSERT INTO productos 
                                (codigo_barras, descripcion, proveedor, unidad, cantidad,
                                 precio_compra, precio_venta, impuesto, bonificacion, 
                                 grupo, subgrupo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                ean,
                                denominacion,
                                proveedor,
                                unidad,
                                cantidad,
                                venta_real,
                                venta_real,  # precio_venta = precio_compra inicialmente
                                impuesto,
                                bonificacion,
                                grupo,
                                subgrupo
                            ))

                            insertados += 1
                            logging.debug(f"Insertado: {ean} - {denominacion}")

                    except Exception as e:
                        logging.error(f"Error en fila {idx} (EAN: {ean if 'ean' in locals() else 'N/A'}): {e}")
                        errores += 1
                        continue

                # Confirmar transacción
                conn.commit()

            # Mostrar resumen
            mensaje_resumen = (
                f"✅ Actualización completada\n\n"
                f"📊 Resumen:\n"
                f"  • Productos actualizados: {actualizados}\n"
                f"  • Productos insertados: {insertados}\n"
                f"  • Errores: {errores}\n"
                f"  • Total procesado: {actualizados + insertados}"
            )

            logging.info(f"Resumen actualización Excel: {actualizados} actualizados, {insertados} insertados, {errores} errores")

            messagebox.showinfo("Actualización Completada", mensaje_resumen)

            return (actualizados, insertados, errores)

        except FileNotFoundError:
            logging.error(f"Archivo no encontrado: {archivo_path}")
            messagebox.showerror("Error", f"Archivo no encontrado:\n{archivo_path}")
            return (0, 0, 0)

        except Exception as e:
            logging.error(f"Error al actualizar desde Excel: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo procesar el archivo:\n\n{str(e)}")
            return (0, 0, 0)

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