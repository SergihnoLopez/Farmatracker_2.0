"""
Generador de facturas en PDF
"""
from datetime import datetime
from fpdf import FPDF, XPos, YPos
from config.settings import (
    COMPANY_NAME, COMPANY_NIT, COMPANY_ADDRESS,
    COMPANY_PHONE, COMPANY_BRANCH
)
from utils.formatters import format_precio_miles
import logging


class FacturaGenerator:
    """Genera facturas en formato PDF térmico"""

    def __init__(self, productos_venta: list):
        self.productos = productos_venta
        self.ancho_papel = 72  # mm
        self.ancho_texto = 68  # mm

    def generar(self, output_path: str = "factura_flexible.pdf") -> bool:
        """Genera el PDF de la factura"""
        try:
            altura = 130 + len(self.productos) * 14

            pdf = FPDF("P", "mm", (self.ancho_papel, altura))
            pdf.set_margins(left=2, top=2, right=2)
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=2)

            # Registrar fuentes
            try:
                pdf.add_font("ArialNarrow", "", "Arial Narrow Regular.ttf")
                pdf.add_font("ArialNarrow", "B", "Arial Narrow Regular.ttf")
                pdf.add_font("ArialNarrowBold", "", "Arial Narrow Bold.ttf")
            except:
                logging.warning("Fuentes personalizadas no encontradas, usando Arial estándar")

            self._generar_encabezado(pdf)
            total, total_iva = self._generar_productos(pdf)
            self._generar_totales(pdf, total, total_iva)
            self._generar_pie(pdf)

            pdf.output(output_path)
            return True

        except Exception as e:
            logging.error(f"Error al generar factura: {e}")
            return False

    def _generar_encabezado(self, pdf: FPDF):
        """Genera el encabezado de la factura"""
        separador = "=" * int(self.ancho_texto * 1.2)

        pdf.set_font("ArialNarrowBold", "", 16)
        pdf.cell(self.ancho_texto, 7, COMPANY_NAME.upper(), align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("ArialNarrow", "", 14)
        lineas = [
            f"NIT {COMPANY_NIT}",
            f"Sucursal: {COMPANY_BRANCH}",
            COMPANY_ADDRESS,
            f"Tel: {COMPANY_PHONE}",
            separador
        ]

        for linea in lineas:
            pdf.cell(self.ancho_texto, 5, linea.upper(), align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.cell(self.ancho_texto, 5,
                 f"FECHA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}".upper(),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 5, "CAJERO: PRINCIPAL",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 5, separador, align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _generar_productos(self, pdf: FPDF) -> tuple:
        """Genera la lista de productos y retorna (total, total_iva)"""
        total = 0.0
        total_iva = 0.0

        pdf.set_font("ArialNarrow", "", 14)
        pdf.cell(self.ancho_texto, 5, "PRODUCTO / CANT / PRECIO",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 4, "=" * int(self.ancho_texto * 1.2),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        for item in self.productos:
            # Estructura: [codigo, descripcion, cantidad, precio_unitario, subtotal, impuesto]
            codigo = str(item[0])
            descripcion = str(item[1]).upper()
            cantidad = float(item[2])
            precio_unitario = float(item[3])
            subtotal = float(item[4])
            impuesto_str = str(item[5]).strip() if len(item) > 5 else ""

            total += subtotal

            # Calcular IVA
            if impuesto_str == "19% IVA":
                precio_base = precio_unitario / 1.19
                iva_unitario = precio_unitario - precio_base
                total_iva += iva_unitario * cantidad

            # Código
            pdf.set_font("ArialNarrow", "B", 14)
            pdf.cell(self.ancho_texto, 5, f"CÓDIGO: {codigo}",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Descripción y cantidad
            pdf.set_font("ArialNarrow", "", 14)
            linea_producto = f"{descripcion[:30]} X{int(cantidad)}"
            pdf.multi_cell(self.ancho_texto, 5, linea_producto.strip(), align="L")

            # Precio unitario
            pdf.cell(self.ancho_texto, 5,
                     f"   -> {format_precio_miles(precio_unitario)} C/U",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Subtotal
            pdf.cell(self.ancho_texto, 5,
                     f"   SUBTOTAL: {format_precio_miles(subtotal)}",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Espacio
            pdf.cell(self.ancho_texto, 3, "", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        return total, total_iva

    def _generar_totales(self, pdf: FPDF, total: float, total_iva: float):
        """Genera la sección de totales"""
        separador = "=" * int(self.ancho_texto * 1.2)

        pdf.cell(self.ancho_texto, 5, separador, align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("ArialNarrow", "B", 14)
        pdf.cell(self.ancho_texto, 6,
                 f"IVA TOTAL: {format_precio_miles(total_iva)}",
                 align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("ArialNarrowBold", "", 16)
        pdf.cell(self.ancho_texto, 7,
                 f"TOTAL: {format_precio_miles(total)}",
                 align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("ArialNarrow", "", 14)
        pdf.cell(self.ancho_texto, 5, separador, align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _generar_pie(self, pdf: FPDF):
        """Genera el pie de página"""
        lineas = [
            "Gracias por su compra",
            "Vuelva pronto",
            COMPANY_NAME,
            "Comprometidos con tu",
            "Bienestar y economía"
        ]

        for linea in lineas:
            pdf.cell(self.ancho_texto, 5, linea.upper(), align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)