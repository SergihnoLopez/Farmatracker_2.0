"""
Ventana de liquidador de precios - FarmaTrack
✅ Label con nombre del producto seleccionado entre el buscador y la tabla
"""
from tkinter import Toplevel, Frame, Label, Entry, Listbox, END
from tkinter import ttk
from config.settings import FONT_STYLE
from models.database import DatabaseManager
from utils.formatters import format_precio_display


class LiquidadorWindow:
    """Ventana para calcular precios de venta sugeridos"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Liquidador de Precios")
        self.window.state("zoomed")
        self.window.grab_set()

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz"""
        self.window.grid_columnconfigure(0, weight=1)

        # ── Label búsqueda ────────────────────────────────────────────────────
        Label(
            self.window,
            text="Buscar producto:",
            font=FONT_STYLE,
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=50, pady=(20, 5))

        # ── Entry búsqueda ────────────────────────────────────────────────────
        self.entry_busqueda = Entry(self.window, font=FONT_STYLE)
        self.entry_busqueda.grid(row=1, column=0, sticky="ew", padx=50, pady=(0, 10))
        self.entry_busqueda.focus()

        # ── Listbox de sugerencias (flotante) ─────────────────────────────────
        self.lista_sugerencias = Listbox(self.window, height=6, font=("Arial", 12))
        self.lista_sugerencias.place_forget()

        self.entry_busqueda.bind("<KeyRelease>", self._buscar_sugerencias)
        self.lista_sugerencias.bind("<Double-1>", self._seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Return>",   self._seleccionar_sugerencia)

        # ── Label nombre del producto seleccionado ────────────────────────────
        #    Aparece entre el buscador y la tabla de precios
        self.lbl_producto = Label(
            self.window,
            text="",                     # vacío hasta que se seleccione un producto
            font=("Segoe UI", 18, "bold"),
            fg="#0f6cbd",                # Colors.PRIMARY
            anchor="w",
            wraplength=900,
        )
        self.lbl_producto.grid(row=2, column=0, sticky="ew", padx=50, pady=(4, 2))

        # Subtítulo con código y precio de compra
        self.lbl_detalle = Label(
            self.window,
            text="",
            font=("Segoe UI", 13),
            fg="#616161",
            anchor="w",
        )
        self.lbl_detalle.grid(row=3, column=0, sticky="ew", padx=50, pady=(0, 12))

        # ── Label nombre grande (destacado) ──────────────────────────────────
        self.lbl_nombre_grande = Label(
            self.window,
            text="",
            font=("Segoe UI", 36, "bold"),
            fg="#0f6cbd",
            anchor="center",
            wraplength=1100,
            justify="center",
        )
        self.lbl_nombre_grande.grid(row=4, column=0, sticky="ew", padx=50, pady=(0, 16))

        # ── Frame resultados (tabla de precios) ───────────────────────────────
        frame_resultados = Frame(self.window)
        frame_resultados.grid(row=5, column=0, sticky="nsew", padx=50, pady=(0, 20))

        self.window.grid_rowconfigure(5, weight=1)

        # Estilo grande para la tabla
        estilo = ttk.Style()
        estilo.configure("Big.Treeview",
                         font=("Helvetica", 22, "bold"), rowheight=48)
        estilo.configure("Big.Treeview.Heading",
                         font=("Helvetica", 24, "bold"))

        self.tree = ttk.Treeview(
            frame_resultados,
            columns=("margen", "precio"),
            show="headings",
            height=8,
            style="Big.Treeview",
        )

        self.tree.heading("margen", text="Margen (%)")
        self.tree.heading("precio", text="Precio sugerido")
        self.tree.column("margen", width=200, anchor="center")
        self.tree.column("precio", width=300, anchor="e")

        self.tree.pack(expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    def _buscar_sugerencias(self, event):
        texto = self.entry_busqueda.get().strip()

        if not texto:
            self.lista_sugerencias.place_forget()
            return

        resultados = DatabaseManager.buscar_productos_like(texto, limit=30)

        if resultados:
            self.lista_sugerencias.delete(0, END)

            for cod, desc in resultados:
                producto = DatabaseManager.buscar_producto_por_codigo(cod)
                precio = producto['precio_compra'] if producto else 0
                self.lista_sugerencias.insert(
                    END,
                    f"{cod} - {desc} - {format_precio_display(precio)}"
                )

            x = self.entry_busqueda.winfo_rootx() - self.window.winfo_rootx()
            y = (self.entry_busqueda.winfo_rooty() - self.window.winfo_rooty()
                 + self.entry_busqueda.winfo_height() + 10)

            self.lista_sugerencias.place(
                x=x, y=y,
                width=self.entry_busqueda.winfo_width()
            )
        else:
            self.lista_sugerencias.place_forget()

    def _seleccionar_sugerencia(self, event):
        if not self.lista_sugerencias.curselection():
            return

        seleccion = self.lista_sugerencias.get(
            self.lista_sugerencias.curselection()
        )
        partes = seleccion.split(" - ")

        codigo        = partes[0].strip()
        descripcion   = partes[1].strip() if len(partes) > 1 else codigo
        precio_str    = partes[-1].replace("$", "").replace(".", "")
        precio_compra = float(precio_str) if precio_str.isdigit() else 0.0

        # Consultar precio real desde la BD para evitar errores de formato
        producto = DatabaseManager.buscar_producto_por_codigo(codigo)
        if producto:
            precio_compra = float(producto['precio_compra'])
            descripcion   = producto['descripcion']

        self.entry_busqueda.delete(0, END)
        self.entry_busqueda.insert(0, codigo)
        self.lista_sugerencias.place_forget()

        # ── Actualizar labels del producto seleccionado ───────────────────────
        self.lbl_producto.config(text=descripcion)
        self.lbl_nombre_grande.config(text=descripcion)
        self.lbl_detalle.config(
            text=f"Código: {codigo}   |   "
                 f"Precio de compra: {format_precio_display(precio_compra)}"
        )

        self._mostrar_precios(precio_compra)

    def _mostrar_precios(self, precio_compra: float):
        """Calcula y muestra precios sugeridos con diferentes márgenes."""
        self.tree.delete(*self.tree.get_children())

        margenes = [10, 15, 20, 30, 40, 50]

        for m in margenes:
            precio_sugerido = precio_compra / (1 - m / 100)
            self.tree.insert("", "end", values=(
                f"{m}%",
                format_precio_display(precio_sugerido),
            ))