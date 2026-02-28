"""
Generador de facturas en PDF - FarmaTrack
Basado en la implementación probada de interfaz_inicio.py
"""
import os
import logging
from datetime import datetime
from fpdf import FPDF, XPos, YPos
from config.settings import (
    COMPANY_NAME, COMPANY_NIT, COMPANY_ADDRESS,
    COMPANY_PHONE, COMPANY_BRANCH
)
from utils.formatters import format_precio_miles


# Directorio raíz del proyecto (donde están los .ttf)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RESOURCES_DIR = os.path.join(_BASE_DIR, "resources")


class FacturaGenerator:
    """Genera facturas en formato PDF térmico (ticket 72 mm)"""

    def __init__(self, productos_venta: list, fecha: str = None):
        """
        productos_venta : lista de productos a imprimir.
        fecha           : fecha/hora del registro con formato
                          'YYYY-MM-DD HH:MM:SS'.
                          Si es None usa datetime.now() (comportamiento original).
        """
        self.productos   = productos_venta
        self.ancho_papel = 72
        self.ancho_texto = 68
        if fecha:
            try:
                dt = datetime.strptime(str(fecha), "%Y-%m-%d %H:%M:%S")
                self._fecha_str = dt.strftime("%d/%m/%Y %H:%M:%S")
            except ValueError:
                self._fecha_str = str(fecha)
        else:
            self._fecha_str = None

    def generar(self, output_path: str = "factura_flexible.pdf") -> bool:
        """Genera el PDF de la factura."""
        try:
            altura = 130 + len(self.productos) * 14

            pdf = FPDF("P", "mm", (self.ancho_papel, altura))
            pdf.set_margins(left=2, top=2, right=2)
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=2)

            # === Registrar fuentes desde resources/ ===
            # Cambiamos temporalmente el directorio de trabajo al de resources
            # para que fpdf encuentre los .ttf igual que en interfaz_inicio.py
            _cwd_original = os.getcwd()
            try:
                os.chdir(_RESOURCES_DIR)
                pdf.add_font("ArialNarrow",     "", "Arial Narrow Regular.ttf")
                pdf.add_font("ArialNarrow",     "B", "Arial Narrow Regular.ttf")
                pdf.add_font("ArialNarrowBold", "", "Arial Narrow Regular.ttf")
            except Exception as fe:
                logging.warning(f"Fuente Arial Narrow no cargada: {fe}")
            finally:
                os.chdir(_cwd_original)

            self._generar_encabezado(pdf)
            total, total_iva = self._generar_productos(pdf)
            self._generar_totales(pdf, total, total_iva)
            self._generar_pie(pdf)

            pdf.output(output_path)
            return True

        except Exception as e:
            logging.error(f"Error al generar factura: {e}")
            return False

    def _upper(self, texto):
        return str(texto).upper()

    def _fmt(self, v):
        try:
            return f"${int(round(float(v))):,}".replace(",", ".")
        except Exception:
            return str(v)

    def _generar_encabezado(self, pdf: FPDF):
        separador = "=" * int(self.ancho_texto * 1.2)

        pdf.set_font("ArialNarrowBold", "", 16)
        pdf.cell(self.ancho_texto, 7, self._upper(COMPANY_NAME), align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("ArialNarrow", "", 14)
        for linea in [
            f"NIT {COMPANY_NIT}",
            f"Sucursal: {COMPANY_BRANCH}",
            COMPANY_ADDRESS,
            f"Tel: {COMPANY_PHONE}",
            separador,
        ]:
            pdf.cell(self.ancho_texto, 5, self._upper(linea), align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.cell(self.ancho_texto, 5,
                 self._upper(f"Fecha: {self._fecha_str or datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 5, self._upper("Cajero: Principal"),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 5, separador, align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _generar_productos(self, pdf: FPDF):
        separador = "=" * int(self.ancho_texto * 1.2)
        total     = 0.0
        total_iva = 0.0

        pdf.set_font("ArialNarrow", "", 14)
        pdf.cell(self.ancho_texto, 5, self._upper("Producto / Cant / Precio"),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 4, separador,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        for item in self.productos:
            # Acepta tanto lista/tupla como dict
            if isinstance(item, dict):
                codigo          = str(item.get("codigo", ""))
                descripcion     = self._upper(str(item.get("descripcion", "")))
                cantidad        = float(item.get("cantidad", 0))
                precio_unitario = float(item.get("precio_unitario", 0))
                subtotal        = float(item.get("subtotal", 0))
                impuesto_str    = str(item.get("impuesto", "")).strip()
            else:
                codigo          = str(item[0])
                descripcion     = self._upper(str(item[1]))
                cantidad        = float(item[2])
                precio_unitario = float(item[3])
                subtotal        = float(item[4])
                impuesto_str    = str(item[5]).strip() if len(item) > 5 else ""

            total += subtotal

            # IVA: soporta "19%  IVA" (2 espacios) y "19% IVA" (1 espacio)
            if impuesto_str in ("19%  IVA", "19% IVA"):
                # El subtotal ya incluye IVA; la fracción correcta es 19/119
                total_iva += subtotal * (19 / 119)

            pdf.set_font("ArialNarrow", "B", 14)
            pdf.cell(self.ancho_texto, 5, f"CÓDIGO: {codigo}",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("ArialNarrow", "", 14)
            linea_prod = f"{descripcion[:30]} X{int(cantidad)}"
            pdf.multi_cell(self.ancho_texto, 5, linea_prod.strip(), align="L")

            pdf.cell(self.ancho_texto, 5,
                     self._upper(f"   -> {self._fmt(precio_unitario)} C/U"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(self.ancho_texto, 5,
                     self._upper(f"   SUBTOTAL: {self._fmt(subtotal)}"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(self.ancho_texto, 3, "",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        return total, total_iva

    def _generar_totales(self, pdf: FPDF, total: float, total_iva: float):
        separador = "=" * int(self.ancho_texto * 1.2)

        pdf.cell(self.ancho_texto, 5, separador, align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("ArialNarrow", "B", 14)

        subtotal_sin_iva = total - total_iva
        pdf.cell(self.ancho_texto, 6,
                 self._upper(f"SUBTOTAL: {self._fmt(subtotal_sin_iva)}"),
                 align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(self.ancho_texto, 6,
                 self._upper(f"IVA (19%): {self._fmt(total_iva)}"),
                 align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("ArialNarrowBold", "", 16)
        pdf.cell(self.ancho_texto, 7,
                 self._upper(f"TOTAL: {self._fmt(total)}"),
                 align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("ArialNarrow", "", 14)
        pdf.cell(self.ancho_texto, 5, separador, align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _generar_pie(self, pdf: FPDF):
        for linea in [
            "Gracias por su compra",
            "Vuelva pronto",
            COMPANY_NAME,
            "Comprometidos con tu",
            "Bienestar y economía",
        ]:
            pdf.cell(self.ancho_texto, 5, self._upper(linea), align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)