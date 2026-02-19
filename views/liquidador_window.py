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

        # ── Listbox de sugerencias (ventana flotante independiente) ───────────
        self._popup = None  # ventana flotante para sugerencias
        self.lista_sugerencias = None

        self.entry_busqueda.bind("<KeyRelease>", self._buscar_sugerencias)
        self.entry_busqueda.bind("<FocusOut>", lambda e: self.window.after(150, self._cerrar_popup))

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
    def _cerrar_popup(self):
        """Cierra la ventana flotante de sugerencias"""
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None
            self.lista_sugerencias = None

    def _buscar_sugerencias(self, event):
        texto = self.entry_busqueda.get().strip()

        if not texto:
            self._cerrar_popup()
            return

        resultados = DatabaseManager.buscar_productos_like(texto, limit=30)

        if resultados:
            # Calcular posición absoluta del entry en la pantalla
            self.entry_busqueda.update_idletasks()
            ex = self.entry_busqueda.winfo_rootx()
            ey = self.entry_busqueda.winfo_rooty() + self.entry_busqueda.winfo_height()
            ew = self.entry_busqueda.winfo_width()

            # Crear o reutilizar ventana flotante
            if self._popup is None:
                from tkinter import Toplevel, Listbox, Scrollbar, BOTH, RIGHT, Y
                self._popup = Toplevel(self.window)
                self._popup.wm_overrideredirect(True)  # sin bordes
                self._popup.attributes("-topmost", True)

                frame = __import__('tkinter').Frame(self._popup, bd=1, relief="solid")
                frame.pack(fill=BOTH, expand=True)

                sb = Scrollbar(frame, orient="vertical")
                self.lista_sugerencias = Listbox(
                    frame,
                    height=8,
                    font=("Arial", 13),
                    yscrollcommand=sb.set,
                    activestyle="dotbox",
                    selectbackground="#0f6cbd",
                    selectforeground="white"
                )
                sb.config(command=self.lista_sugerencias.yview)
                sb.pack(side=RIGHT, fill=Y)
                self.lista_sugerencias.pack(fill=BOTH, expand=True)

                self.lista_sugerencias.bind("<Double-1>", self._seleccionar_sugerencia)
                self.lista_sugerencias.bind("<Return>",   self._seleccionar_sugerencia)

            self._popup.geometry(f"{ew}x{min(len(resultados), 8) * 24 + 8}+{ex}+{ey}")

            self.lista_sugerencias.delete(0, END)
            for cod, desc in resultados:
                producto = DatabaseManager.buscar_producto_por_codigo(cod)
                precio = producto['precio_compra'] if producto else 0
                self.lista_sugerencias.insert(
                    END,
                    f"{cod} - {desc} - {format_precio_display(precio)}"
                )
        else:
            self._cerrar_popup()

    def _seleccionar_sugerencia(self, event):
        if not self.lista_sugerencias or not self.lista_sugerencias.curselection():
            return

        seleccion = self.lista_sugerencias.get(
            self.lista_sugerencias.curselection()
        )
        self._cerrar_popup()
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