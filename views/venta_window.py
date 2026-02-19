"""
Ventana de registro de ventas - FarmaTrack
✅ Arial Narrow cargada desde resources/ (Arial Narrow Regular.ttf / Bold.ttf)
✅ Sin warning de fuentes faltantes
✅ Fallback silencioso a Helvetica si los archivos no existen
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, Listbox, END, W
from tkinter import messagebox
from tkinter import ttk, BOTH
from config.settings import (
    FONT_STYLE, BTN_COLOR, BTN_FG,
    COMPANY_NAME, COMPANY_NIT, COMPANY_ADDRESS,
    COMPANY_PHONE, COMPANY_BRANCH,
    RESOURCES_DIR,
)
from controllers.ventas import VentasController
from models.database import DatabaseManager
from datetime import datetime
from fpdf import FPDF, XPos, YPos
import logging
import os
import platform


# ==============================================================================
# RUTAS DE FUENTES  (resources/ del proyecto)
# ==============================================================================

_FONT_REGULAR = RESOURCES_DIR / "Arial Narrow Regular.ttf"
_FONT_BOLD    = RESOURCES_DIR / "Arial Narrow Bold.ttf"


def _fuentes_disponibles() -> bool:
    """Retorna True si ambos archivos TTF existen en resources/."""
    return _FONT_REGULAR.exists() and _FONT_BOLD.exists()


# ==============================================================================
# VENTANA DE VENTAS
# ==============================================================================

class VentaWindow:
    """Ventana para registrar ventas"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.grab_set()
        self.window.title("Registrar Venta")
        self.window.state("zoomed")
        self.window.grab_set()
        self._setup_ui()


        # ──────────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        frame_entrada = Frame(self.window)
        frame_entrada.pack(pady=10)

        Label(frame_entrada, text="Código de Barras:", font=FONT_STYLE).grid(
            row=0, column=0, padx=5, pady=5, sticky=W
        )
        self.codigo_entry = Entry(frame_entrada, width=30, font=FONT_STYLE)
        self.codigo_entry.grid(row=0, column=1, padx=5, pady=5)
        self.codigo_entry.focus()

        self.lista_sugerencias = Listbox(self.window, height=30, font=("Arial", 10))
        self.lista_sugerencias.place_forget()
        self.codigo_entry.bind("<KeyRelease>", self._buscar_sugerencias)
        self.lista_sugerencias.bind("<Double-1>", self._seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Return>",   self._seleccionar_sugerencia)

        Label(frame_entrada, text="Cantidad:", font=FONT_STYLE).grid(
            row=1, column=0, padx=5, pady=5, sticky=W
        )
        self.cantidad_entry = Entry(frame_entrada, width=30, font=FONT_STYLE)
        self.cantidad_entry.grid(row=1, column=1, padx=5, pady=5)

        self.codigo_entry.bind("<Return>",  lambda e: self.cantidad_entry.focus())
        self.cantidad_entry.bind("<Return>", self._agregar_con_enter)

        Button(
            frame_entrada, text="Agregar Producto",
            font=FONT_STYLE, bg=BTN_COLOR, fg=BTN_FG,
            command=self._agregar_producto
        ).grid(row=0, column=2, rowspan=2, padx=10, pady=5)

        self.tree = ttk.Treeview(
            self.window,
            columns=("codigo_barras", "descripcion", "cantidad",
                     "precio_unitario", "subtotal", "impuesto"),
            show="headings",
        )
        self.tree.heading("codigo_barras",   text="Código")
        self.tree.heading("descripcion",     text="Descripción")
        self.tree.heading("cantidad",        text="Cantidad")
        self.tree.heading("precio_unitario", text="Precio Unit.")
        self.tree.heading("subtotal",        text="Subtotal")
        self.tree.heading("impuesto",        text="Impuesto")
        self.tree.pack(fill=BOTH, expand=True, pady=10)

        self.total_label = Label(
            self.window,
            text="Total: $0.00",
            font=("Titillium Web", 14, "bold"),
            fg="black",
        )
        self.total_label.pack(pady=5)

        frame_botones = Frame(self.window)
        frame_botones.pack(pady=10)

        Button(frame_botones, text="Eliminar Producto",
               font=FONT_STYLE, bg="#f44336", fg="white",
               command=self._eliminar_producto, width=18).pack(side="left", padx=5)

        Button(frame_botones, text="Registrar Venta",
               font=FONT_STYLE, bg=BTN_COLOR, fg=BTN_FG,
               command=self._registrar_venta, width=18).pack(side="left", padx=5)

        Button(frame_botones, text="🖨️ Imprimir Factura",
               font=FONT_STYLE, bg="#2196F3", fg="white",
               command=self._imprimir_factura, width=18).pack(side="left", padx=5)

    # ──────────────────────────────────────────────────────────────────────────
    # BÚSQUEDA Y SELECCIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _buscar_sugerencias(self, event):
        texto = self.codigo_entry.get().strip()
        if not texto:
            self.lista_sugerencias.place_forget()
            return

        resultados = DatabaseManager.buscar_productos_like(texto)
        if resultados:
            self.lista_sugerencias.delete(0, END)
            for cod, desc in resultados:
                self.lista_sugerencias.insert(END, f"{cod} - {desc}")

            x = self.codigo_entry.winfo_rootx() - self.window.winfo_rootx()
            y = (self.codigo_entry.winfo_rooty() - self.window.winfo_rooty()
                 + self.codigo_entry.winfo_height())
            self.lista_sugerencias.place(x=x, y=y, width=600)
            self.lista_sugerencias.lift()
        else:
            self.lista_sugerencias.place_forget()

    def _seleccionar_sugerencia(self, event):
        if self.lista_sugerencias.curselection():
            seleccion = self.lista_sugerencias.get(
                self.lista_sugerencias.curselection()
            )
            self.codigo_entry.delete(0, END)
            self.codigo_entry.insert(0, seleccion.split(" - ")[0])
            self.lista_sugerencias.place_forget()
            self.cantidad_entry.focus()

    def _agregar_con_enter(self, event):
        self._agregar_producto()

    def _agregar_producto(self):
        if VentasController.agregar_producto_a_venta(
            self.tree, self.codigo_entry, self.cantidad_entry
        ):
            self._actualizar_total()

    def _actualizar_total(self):
        total = sum(float(self.tree.item(i, "values")[4])
                    for i in self.tree.get_children())
        self.total_label.config(text=f"Total: ${total:,.0f}".replace(",", "."))

    def _eliminar_producto(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        for item in selected:
            self.tree.delete(item)
        self._actualizar_total()

    def _registrar_venta(self):
        if VentasController.registrar_venta(self.tree):
            messagebox.showinfo("Éxito", "Venta registrada correctamente")
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._actualizar_total()
            self.codigo_entry.focus()

    # ──────────────────────────────────────────────────────────────────────────
    # GENERACIÓN DE FACTURA
    # ──────────────────────────────────────────────────────────────────────────

    def _imprimir_factura(self):
        """
        Genera la factura PDF tipo ticket 72 mm.
        • Usa Arial Narrow desde resources/ si los TTF están disponibles.
        • Fallback silencioso a Helvetica si no se encuentran.
        • Sin warnings al usuario ni al log por fuentes faltantes.
        """
        if not self.tree.get_children():
            messagebox.showwarning("Advertencia", "No hay productos para imprimir")
            return

        try:
            altura      = 130 + len(self.tree.get_children()) * 14
            ancho_total = 72
            ancho_texto = 68

            pdf = FPDF("P", "mm", (ancho_total, altura))
            pdf.set_margins(left=2, top=2, right=2)
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=2)

            # ── Selección de fuente ──────────────────────────────────────────
            if _fuentes_disponibles():
                try:
                    pdf.add_font("AN",  "",  str(_FONT_REGULAR))
                    pdf.add_font("AN",  "B", str(_FONT_REGULAR))
                    pdf.add_font("ANB", "",  str(_FONT_BOLD))
                    fuente_n = "AN"
                    fuente_b = "ANB"
                    logging.debug("Fuentes Arial Narrow cargadas desde resources/")
                except Exception as exc:
                    logging.debug(f"Error cargando Arial Narrow: {exc}")
                    fuente_n = fuente_b = "Helvetica"
            else:
                # Fuentes no disponibles → Helvetica sin ningún warning
                fuente_n = fuente_b = "Helvetica"

            def upper(t):
                return str(t).upper()

            sep = "=" * int(ancho_texto * 1.2)

            # ── Encabezado ───────────────────────────────────────────────────
            pdf.set_font(fuente_b, "", 16)
            pdf.cell(ancho_texto, 7, upper(COMPANY_NAME), align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font(fuente_n, "", 14)
            for linea in [
                f"NIT {COMPANY_NIT}",
                f"Sucursal: {COMPANY_BRANCH}",
                COMPANY_ADDRESS,
                f"Tel: {COMPANY_PHONE}",
                sep,
            ]:
                pdf.cell(ancho_texto, 5, upper(linea), align="C",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.cell(
                ancho_texto, 5,
                upper(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"),
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.cell(ancho_texto, 5, upper("Cajero: Principal"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(ancho_texto, 5, sep, align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # ── Productos ────────────────────────────────────────────────────
            def fmt(v):
                try:
                    return f"${int(round(float(v))):,}".replace(",", ".")
                except Exception:
                    return str(v)

            total = total_iva = 0.0

            pdf.set_font(fuente_n, "", 14)
            pdf.cell(ancho_texto, 5, "PRODUCTO / CANT / PRECIO",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(ancho_texto, 4, sep,
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            for item in self.tree.get_children():
                v           = self.tree.item(item, "values")
                codigo      = str(v[0])
                descripcion = str(v[1]).upper()
                cantidad    = float(v[2])
                p_unit      = float(v[3])
                subtotal    = float(v[4])
                impuesto    = str(v[5]).strip() if len(v) > 5 else ""

                total += subtotal
                if impuesto == "19% IVA":
                    total_iva += (p_unit - p_unit / 1.19) * cantidad

                pdf.set_font(fuente_b, "", 14)
                pdf.cell(ancho_texto, 5, f"CODIGO: {codigo}",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font(fuente_n, "", 14)
                pdf.multi_cell(ancho_texto, 5,
                               f"{descripcion[:30]} X{int(cantidad)}".strip(),
                               align="L")
                pdf.cell(ancho_texto, 5, f"   -> {fmt(p_unit)} C/U",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(ancho_texto, 5, f"   SUBTOTAL: {fmt(subtotal)}",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(ancho_texto, 3, "",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # ── Totales ──────────────────────────────────────────────────────
            pdf.cell(ancho_texto, 5, sep, align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font(fuente_b, "", 14)
            pdf.cell(ancho_texto, 6, f"IVA TOTAL: {fmt(total_iva)}",
                     align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font(fuente_b, "", 16)
            pdf.cell(ancho_texto, 7, f"TOTAL: {fmt(total)}",
                     align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font(fuente_n, "", 14)
            pdf.cell(ancho_texto, 5, sep, align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # ── Pie ──────────────────────────────────────────────────────────
            for linea in [
                "Gracias por su compra",
                "Vuelva pronto",
                COMPANY_NAME,
                "Comprometidos con tu",
                "Bienestar y economia",
            ]:
                pdf.cell(ancho_texto, 5, upper(linea), align="C",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.output("factura_ticket.pdf")

            messagebox.showinfo(
                "Factura Generada",
                "La factura se ha generado correctamente:\nfactura_ticket.pdf",
            )

            # Abrir automáticamente
            try:
                if platform.system() == "Windows":
                    os.startfile("factura_ticket.pdf")
                elif platform.system() == "Darwin":
                    os.system("open factura_ticket.pdf")
                else:
                    os.system("xdg-open factura_ticket.pdf")
            except Exception as exc:
                logging.warning(f"No se pudo abrir el PDF: {exc}")

        except Exception as exc:
            logging.error(f"Error al generar factura: {exc}")
            messagebox.showerror("Error", f"No se pudo generar la factura:\n{exc}")