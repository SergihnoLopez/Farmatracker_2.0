"""
Ventana de registro de ventas
✅ NUEVO: Botón de impresión de factura tipo ticket
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, Listbox, END, W
from tkinter import messagebox
from tkinter import ttk, BOTH
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG, COMPANY_NAME, COMPANY_NIT, COMPANY_ADDRESS, COMPANY_PHONE, COMPANY_BRANCH
from controllers.ventas import VentasController
from models.database import DatabaseManager
from datetime import datetime
from fpdf import FPDF, XPos, YPos
import logging
import os


class VentaWindow:
    """Ventana para registrar ventas"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Registrar Venta")
        self.window.state("zoomed")

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz"""
        # Frame de entrada
        frame_entrada = Frame(self.window)
        frame_entrada.pack(pady=10)

        # Código de barras
        Label(frame_entrada, text="Código de Barras:", font=FONT_STYLE).grid(
            row=0, column=0, padx=5, pady=5, sticky=W
        )

        self.codigo_entry = Entry(frame_entrada, width=30, font=FONT_STYLE)
        self.codigo_entry.grid(row=0, column=1, padx=5, pady=5)
        self.codigo_entry.focus()

        # Autocompletado
        self.lista_sugerencias = Listbox(self.window, height=30, font=("Arial", 10))
        self.lista_sugerencias.place_forget()

        self.codigo_entry.bind("<KeyRelease>", self._buscar_sugerencias)
        self.lista_sugerencias.bind("<Double-1>", self._seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Return>", self._seleccionar_sugerencia)

        # Cantidad
        Label(frame_entrada, text="Cantidad:", font=FONT_STYLE).grid(
            row=1, column=0, padx=5, pady=5, sticky=W
        )

        self.cantidad_entry = Entry(frame_entrada, width=30, font=FONT_STYLE)
        self.cantidad_entry.grid(row=1, column=1, padx=5, pady=5)

        # Navegación con Enter
        self.codigo_entry.bind("<Return>", lambda e: self.cantidad_entry.focus())
        self.cantidad_entry.bind("<Return>", self._agregar_con_enter)

        # Botón agregar
        Button(
            frame_entrada,
            text="Agregar Producto",
            font=FONT_STYLE,
            bg=BTN_COLOR,
            fg=BTN_FG,
            command=self._agregar_producto
        ).grid(row=0, column=2, rowspan=2, padx=10, pady=5)

        # Tabla de productos
        self.tree = ttk.Treeview(
            self.window,
            columns=("codigo_barras", "descripcion", "cantidad", "precio_unitario", "subtotal", "impuesto"),
            show="headings"
        )

        self.tree.heading("codigo_barras", text="Código")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("precio_unitario", text="Precio Unit.")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.heading("impuesto", text="Impuesto")

        self.tree.pack(fill=BOTH, expand=True, pady=10)

        # Label total
        self.total_label = Label(
            self.window,
            text="Total: $0.00",
            font=("Titillium Web", 14, "bold"),
            fg="black"
        )
        self.total_label.pack(pady=5)

        # Frame de botones
        frame_botones = Frame(self.window)
        frame_botones.pack(pady=10)

        # Botón Eliminar Producto
        Button(
            frame_botones,
            text="Eliminar Producto",
            font=FONT_STYLE,
            bg="#f44336",
            fg="white",
            command=self._eliminar_producto,
            width=18
        ).pack(side="left", padx=5)

        # Botón Registrar Venta
        Button(
            frame_botones,
            text="Registrar Venta",
            font=FONT_STYLE,
            bg=BTN_COLOR,
            fg=BTN_FG,
            command=self._registrar_venta,
            width=18
        ).pack(side="left", padx=5)

        # ✅ NUEVO: Botón Imprimir Factura
        Button(
            frame_botones,
            text="🖨️ Imprimir Factura",
            font=FONT_STYLE,
            bg="#2196F3",
            fg="white",
            command=self._imprimir_factura,
            width=18
        ).pack(side="left", padx=5)

    def _buscar_sugerencias(self, event):
        """Busca productos mientras se escribe"""
        texto = self.codigo_entry.get().strip()

        if not texto:
            self.lista_sugerencias.place_forget()
            return

        resultados = DatabaseManager.buscar_productos_like(texto)

        if resultados:
            self.lista_sugerencias.delete(0, END)

            for cod, desc in resultados:
                self.lista_sugerencias.insert(END, f"{cod} - {desc}")

            # Posicionar lista
            x = self.codigo_entry.winfo_rootx() - self.window.winfo_rootx()
            y = (self.codigo_entry.winfo_rooty() - self.window.winfo_rooty() +
                 self.codigo_entry.winfo_height())

            self.lista_sugerencias.place(x=x, y=y, width=600)
            self.lista_sugerencias.lift()
        else:
            self.lista_sugerencias.place_forget()

    def _seleccionar_sugerencia(self, event):
        """Selecciona una sugerencia de la lista"""
        if self.lista_sugerencias.curselection():
            seleccion = self.lista_sugerencias.get(self.lista_sugerencias.curselection())
            codigo = seleccion.split(" - ")[0]

            self.codigo_entry.delete(0, END)
            self.codigo_entry.insert(0, codigo)
            self.lista_sugerencias.place_forget()
            self.cantidad_entry.focus()

    def _agregar_con_enter(self, event):
        """Agrega producto al presionar Enter"""
        self._agregar_producto()

    def _agregar_producto(self):
        """Agrega un producto a la venta"""
        if VentasController.agregar_producto_a_venta(
            self.tree,
            self.codigo_entry,
            self.cantidad_entry
        ):
            self._actualizar_total()

    def _actualizar_total(self):
        """Actualiza el total de la venta"""
        total = 0.0
        for item in self.tree.get_children():
            valores = self.tree.item(item, "values")
            total += float(valores[4])

        self.total_label.config(text=f"Total: ${total:,.0f}".replace(",", "."))

    def _eliminar_producto(self):
        """Elimina un producto de la lista"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return

        for item in selected:
            self.tree.delete(item)

        self._actualizar_total()

    def _registrar_venta(self):
        """Registra la venta"""
        if VentasController.registrar_venta(self.tree):
            messagebox.showinfo("Éxito", "Venta registrada correctamente")

            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)

            self._actualizar_total()
            self.codigo_entry.focus()

    def _imprimir_factura(self):
        """
        Genera e imprime la factura en formato PDF tipo ticket (72mm)
        ✅ NUEVO: Formato de impresión profesional
        """
        if not self.tree.get_children():
            messagebox.showwarning("Advertencia", "No hay productos para imprimir")
            return

        try:
            # Calcular altura dinámica del PDF
            altura = 130 + len(self.tree.get_children()) * 14
            ancho_total = 72   # ancho físico del papel (mm)
            ancho_texto = 68   # ancho útil para contenido

            pdf = FPDF("P", "mm", (ancho_total, altura))
            pdf.set_margins(left=2, top=2, right=2)
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=2)

            # ✅ Verificar si existen las fuentes Arial Narrow
            fuentes_disponibles = self._verificar_fuentes_arial_narrow()

            if fuentes_disponibles:
                # Registrar fuentes Arial Narrow
                pdf.add_font("ArialNarrow", "", "Arial Narrow Regular.ttf")
                pdf.add_font("ArialNarrow", "B", "Arial Narrow Regular.ttf")
                pdf.add_font("ArialNarrowBold", "", "Arial Narrow Bold.ttf")
                fuente_normal = "ArialNarrow"
                fuente_bold = "ArialNarrowBold"
            else:
                # Usar fuentes por defecto de FPDF
                logging.warning("Fuentes Arial Narrow no encontradas, usando fuentes por defecto")
                fuente_normal = "Arial"
                fuente_bold = "Arial"

            def upper(texto):
                return str(texto).upper()

            # Separador dinámico
            separador = "=" * int(ancho_texto * 1.2)

            # --- ENCABEZADO ---
            pdf.set_font(fuente_bold, "", 16)
            pdf.cell(ancho_texto, 7, upper(COMPANY_NAME), align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font(fuente_normal, "", 14)
            for linea in [
                f"NIT {COMPANY_NIT}",
                f"Sucursal: {COMPANY_BRANCH}",
                COMPANY_ADDRESS,
                f"Tel: {COMPANY_PHONE}",
                separador
            ]:
                pdf.cell(ancho_texto, 5, upper(linea), align="C",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.cell(ancho_texto, 5, upper(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(ancho_texto, 5, upper("Cajero: Principal"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(ancho_texto, 5, separador, align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Función auxiliar para formato de precios
            def formato_miles(v):
                try:
                    return f"${int(round(float(v))):,}".replace(",", ".")
                except:
                    return str(v)

            total = 0.0
            total_iva = 0.0

            pdf.set_font(fuente_normal, "", 14)
            pdf.cell(ancho_texto, 5, upper("Producto / Cant / Precio"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(ancho_texto, 4, separador,
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # --- PRODUCTOS ---
            for item in self.tree.get_children():
                valores = self.tree.item(item, "values")
                # Estructura: [codigo, descripcion, cantidad, precio_unitario, subtotal, impuesto]
                codigo = str(valores[0])
                descripcion = upper(str(valores[1]))
                cantidad = float(valores[2])
                precio_unitario = float(valores[3])
                subtotal = float(valores[4])
                impuesto_str = str(valores[5]).strip() if len(valores) > 5 else ""

                total += subtotal

                # Calcular IVA solo si el campo dice "19% IVA"
                if impuesto_str == "19% IVA":
                    precio_base = precio_unitario / 1.19
                    iva_unitario = precio_unitario - precio_base
                    iva_total_producto = iva_unitario * cantidad
                    total_iva += iva_total_producto

                # Código del producto
                pdf.set_font(fuente_normal, "B", 14)
                pdf.cell(ancho_texto, 5, f"CÓDIGO: {codigo}",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Descripción y cantidad
                pdf.set_font(fuente_normal, "", 14)
                linea_producto = f"{descripcion[:30]} X{int(cantidad)}"
                pdf.multi_cell(ancho_texto, 5, linea_producto.strip(), align="L")

                # Precio unitario
                linea_precio = f"   -> {formato_miles(precio_unitario)} C/U"
                pdf.cell(ancho_texto, 5, upper(linea_precio),
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Subtotal
                linea_subtotal = f"   SUBTOTAL: {formato_miles(subtotal)}"
                pdf.cell(ancho_texto, 5, upper(linea_subtotal),
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Espacio entre productos
                pdf.cell(ancho_texto, 3, "", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # --- IVA TOTAL ---
            pdf.cell(ancho_texto, 5, separador, align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font(fuente_normal, "B", 14)
            pdf.cell(ancho_texto, 6, upper(f"IVA TOTAL: {formato_miles(total_iva)}"),
                     align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # --- TOTAL GENERAL ---
            pdf.set_font(fuente_bold, "", 16)
            pdf.cell(ancho_texto, 7, upper(f"TOTAL: {formato_miles(total)}"),
                     align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font(fuente_normal, "", 14)
            pdf.cell(ancho_texto, 5, separador, align="C",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # --- PIE DE FACTURA ---
            for linea in [
                "Gracias por su compra",
                "Vuelva pronto",
                COMPANY_NAME,
                "Comprometidos con tu",
                "Bienestar y economía"
            ]:
                pdf.cell(ancho_texto, 5, upper(linea), align="C",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # --- GUARDAR ARCHIVO ---
            pdf.output("factura_ticket.pdf")

            messagebox.showinfo(
                "Factura Generada",
                "La factura se ha generado correctamente:\nfactura_ticket.pdf"
            )

            # Abrir el PDF automáticamente
            try:
                import platform
                if platform.system() == 'Windows':
                    os.startfile("factura_ticket.pdf")
                elif platform.system() == 'Darwin':  # macOS
                    os.system("open factura_ticket.pdf")
                else:  # Linux
                    os.system("xdg-open factura_ticket.pdf")
            except Exception as e:
                logging.warning(f"No se pudo abrir el PDF automáticamente: {e}")

        except Exception as e:
            logging.error(f"Error al generar factura: {e}")
            messagebox.showerror("Error", f"No se pudo generar la factura:\n{e}")

    def _verificar_fuentes_arial_narrow(self):
        """
        Verifica si existen las fuentes Arial Narrow en el directorio actual
        Returns: True si existen, False si no
        """
        fuentes_requeridas = [
            "Arial Narrow Regular.ttf",
            "Arial Narrow Bold.ttf"
        ]

        for fuente in fuentes_requeridas:
            if not os.path.exists(fuente):
                return False

        return True