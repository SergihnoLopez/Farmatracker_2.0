"""
Ventana de registro de ventas
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, Listbox, END, W
from tkinter import messagebox
from tkinter import ttk, BOTH
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from controllers.ventas import VentasController
from models.database import DatabaseManager
from utils.pdf_generator import FacturaGenerator
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

        # Botones de acción
        Button(
            self.window,
            text="Eliminar Producto",
            font=FONT_STYLE,
            bg="#f44336",
            fg="white",
            command=self._eliminar_producto
        ).pack(pady=5)

        Button(
            self.window,
            text="Registrar Venta",
            font=FONT_STYLE,
            bg=BTN_COLOR,
            fg=BTN_FG,
            command=self._registrar_venta
        ).pack(pady=10)

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

    def _agregar_producto(self):
        """Agrega producto a la venta"""
        if not self.cantidad_entry.get().strip():
            self.cantidad_entry.insert(0, "1")

        if VentasController.agregar_producto_a_venta(
                self.tree,
                self.codigo_entry,
                self.cantidad_entry
        ):
            self._actualizar_total()

    def _agregar_con_enter(self, event):
        """Agrega producto y resetea foco"""
        self._agregar_producto()
        self.codigo_entry.focus()

    def _actualizar_total(self):
        """Actualiza el total de la venta"""
        total = 0.0
        for item in self.tree.get_children():
            subtotal = float(self.tree.item(item, "values")[4])
            total += subtotal

        self.total_label.config(text=f"Total: ${total:,.2f}".replace(",", "."))

    def _eliminar_producto(self):
        """Elimina producto seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return

        for item in seleccion:
            self.tree.delete(item)

        self._actualizar_total()

    def _registrar_venta(self):
        """Registra la venta completa"""
        if VentasController.registrar_venta(self.tree):
            self._actualizar_total()

            # Generar factura
            productos = []
            for item in self.tree.get_children():
                productos.append(self.tree.item(item, "values"))

            if productos:
                factura = FacturaGenerator(productos)
                if factura.generar():
                    self._imprimir_factura()
                    messagebox.showinfo("Éxito", "Venta registrada y factura generada")

            # Limpiar
            self.tree.delete(*self.tree.get_children())

    def _imprimir_factura(self):
        """Envía factura a impresora"""
        try:
            archivo_pdf = "factura_flexible.pdf"
            if os.path.exists(archivo_pdf):
                if os.name == "nt":
                    os.startfile(archivo_pdf, "print")
                else:
                    os.system(f"lp '{archivo_pdf}'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir: {e}")
