"""
Controlador de lógica de pedidos
"""
from tkinter import messagebox, filedialog
from models.database import DatabaseManager, get_db_connection
from datetime import datetime
from fpdf import FPDF
import pandas as pd
import logging


class PedidosController:
    """Maneja la lógica de negocio de pedidos"""

    @staticmethod
    def cargar_pedido_desde_txt(archivo_path: str) -> list:
        """
        Carga productos desde archivo TXT
        Returns: lista de productos
        """
        productos = []

        try:
            with open(archivo_path, "r", encoding="utf-8") as f:
                for linea in f:
                    partes = linea.strip().split("\t")
                    if len(partes) < 5:
                        continue

                    _, _, descripcion, cantidad, codigo_barras = partes

                    # Buscar precio
                    producto = DatabaseManager.buscar_producto_por_codigo(codigo_barras)
                    precio_compra = producto['precio_compra'] if producto else 0.0

                    productos.append({
                        'codigo': codigo_barras,
                        'descripcion': descripcion,
                        'cantidad': cantidad,
                        'precio_compra': precio_compra
                    })

            return productos

        except Exception as e:
            logging.error(f"Error al cargar TXT: {e}")
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
            return []

    @staticmethod
    def cargar_pedido_desde_excel(archivo_path: str) -> list:
        """
        Carga productos desde archivo Excel
        Returns: lista de productos
        """
        productos = []

        try:
            df = pd.read_excel(archivo_path)

            if "Cantidad" not in df.columns or "Código de Barras" not in df.columns:
                messagebox.showerror("Error", "El archivo debe contener 'Cantidad' y 'Código de Barras'")
                return []

            for _, fila in df.iterrows():
                codigo = str(fila["Código de Barras"]).strip()
                cantidad = int(fila["Cantidad"])

                # Buscar en BD
                producto = DatabaseManager.buscar_producto_por_codigo(codigo)

                if producto:
                    productos.append({
                        'codigo': codigo,
                        'descripcion': producto['descripcion'],
                        'cantidad': cantidad,
                        'precio_compra': producto['precio_compra']
                    })

            return productos

        except Exception as e:
            logging.error(f"Error al cargar Excel: {e}")
            messagebox.showerror("Error", f"No se pudo procesar el archivo:\n{e}")
            return []

    @staticmethod
    def exportar_pedido_pdf(productos: list, ruta_salida: str = None) -> bool:
        """Exporta pedido a PDF"""
        if not productos:
            messagebox.showwarning("Advertencia", "No hay productos en el pedido")
            return False

        if not ruta_salida:
            ruta_salida = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile="pedido.pdf"
            )
            if not ruta_salida:
                return False

        try:
            pdf = FPDF("P", "mm", "A4")
            pdf.add_page()

            # Encabezado
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "ORDEN DE PEDIDO", 0, 1, "C")

            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 6, "Droguería Irlandesa", 0, 1, "L")
            pdf.cell(0, 6, "NIT: 1019054697-5", 0, 1, "L")
            pdf.cell(0, 6, "Dirección: Calle 10F 80F 03", 0, 1, "L")
            pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, "L")
            pdf.ln(5)

            # Tabla
            pdf.set_font("Arial", "B", 10)
            pdf.cell(40, 8, "Código", 1, 0, "C")
            pdf.cell(100, 8, "Descripción", 1, 0, "C")
            pdf.cell(40, 8, "Cantidad", 1, 1, "C")

            pdf.set_font("Arial", "", 10)
            for prod in productos:
                pdf.cell(40, 8, str(prod['codigo']), 1, 0, "C")
                pdf.cell(100, 8, str(prod['descripcion'])[:50], 1, 0, "L")
                pdf.cell(40, 8, str(prod['cantidad']), 1, 1, "C")

            pdf.ln(15)

            # Pie
            pdf.set_font("Arial", "I", 11)
            pdf.cell(0, 8, "Autorizado por Sergio D Lopez", 0, 1, "R")

            pdf.set_font("Arial", "I", 9)
            año = datetime.now().year
            pdf.cell(0, 8, f"Digitalizado mediante FarmaTrack © {año}", 0, 1, "C")

            pdf.output(ruta_salida)

            messagebox.showinfo("Éxito", f"Pedido exportado:\n{ruta_salida}")
            return True

        except Exception as e:
            logging.error(f"Error al exportar PDF: {e}")
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
            return False

    @staticmethod
    def exportar_pedido_excel(productos: list, codigo_drogueria: str = "35389") -> bool:
        """Exporta pedido a Excel formato Copidrogas"""
        if not productos:
            messagebox.showwarning("Advertencia", "No hay productos en el pedido")
            return False

        try:
            ruta_salida = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialfile="pedido_copidrogas.xlsx"
            )

            if not ruta_salida:
                return False

            datos = []
            for prod in productos:
                datos.append({
                    "Código Droguería": codigo_drogueria,
                    "Sucursal": 0,
                    "Descripción": prod['descripcion'],
                    "Cantidad": prod['cantidad'],
                    "Código de Barras": prod['codigo']
                })

            df = pd.DataFrame(datos)
            df.to_excel(ruta_salida, index=False)

            messagebox.showinfo("Éxito", f"Pedido exportado:\n{ruta_salida}")
            return True

        except Exception as e:
            logging.error(f"Error al exportar Excel: {e}")
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
            return False

    @staticmethod
    def exportar_pedido_txt(productos: list, codigo_drogueria: str = "35389") -> bool:
        """Exporta pedido a TXT"""
        if not productos:
            messagebox.showwarning("Advertencia", "No hay productos en el pedido")
            return False

        try:
            ruta_salida = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt")],
                initialfile="pedido_copidrogas.txt"
            )

            if not ruta_salida:
                return False

            with open(ruta_salida, "w", encoding="utf-8") as archivo:
                for prod in productos:
                    linea = f"{codigo_drogueria}\t0\t{prod['descripcion']}\t{prod['cantidad']}\t{prod['codigo']}\n"
                    archivo.write(linea)

            messagebox.showinfo("Éxito", f"Pedido exportado:\n{ruta_salida}")
            return True

        except Exception as e:
            logging.error(f"Error al exportar TXT: {e}")
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
            return False
