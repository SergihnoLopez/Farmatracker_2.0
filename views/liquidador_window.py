"""
Ventana de liquidador de precios - FarmaTrack
✅ grab_set() implementado
✅ Listbox de sugerencias correctamente posicionado y visible
✅ Clic simple selecciona sugerencia
✅ Enter busca coincidencia exacta por EAN
✅ Nombre del producto se muestra tras selección
✅ División de precio de compra con recálculo automático
"""
from tkinter import Toplevel, Frame, Label, Entry, Listbox, END, Scrollbar, VERTICAL, RIGHT, Y, StringVar
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

        self._sugerencias_data = []     # lista de dicts con datos de cada sugerencia
        self._precio_compra_base = 0.0  # precio original sin dividir
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        """Configura la interfaz"""
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(6, weight=1)

        # ── Label búsqueda ────────────────────────────────────────────────────
        Label(
            self.window,
            text="Buscar producto (EAN, código o nombre):",
            font=FONT_STYLE,
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=50, pady=(20, 4))

        # ── Frame que contiene Entry + Listbox superpuesta ────────────────────
        # Usamos un Frame contenedor para que la Listbox flote correctamente
        self.frame_busqueda = Frame(self.window)
        self.frame_busqueda.grid(row=1, column=0, sticky="ew", padx=50, pady=(0, 0))
        self.frame_busqueda.grid_columnconfigure(0, weight=1)

        self.entry_busqueda = Entry(self.frame_busqueda, font=FONT_STYLE)
        self.entry_busqueda.grid(row=0, column=0, sticky="ew")
        self.entry_busqueda.focus()

        # ── Listbox de sugerencias ────────────────────────────────────────────
        # Se coloca en el frame principal (window) con place() relativo a la ventana
        self.frame_lista = Frame(self.window, relief="solid", bd=1)
        self.lista_sugerencias = Listbox(
            self.frame_lista,
            font=("Segoe UI", 12),
            height=8,
            activestyle="dotbox",
            selectbackground="#0f6cbd",
            selectforeground="white",
        )
        scrollbar = Scrollbar(self.frame_lista, orient=VERTICAL, command=self.lista_sugerencias.yview)
        self.lista_sugerencias.configure(yscrollcommand=scrollbar.set)

        self.lista_sugerencias.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Ocultar inicialmente
        self.frame_lista.place_forget()

        # ── Bindings ──────────────────────────────────────────────────────────
        self.entry_busqueda.bind("<KeyRelease>", self._buscar_sugerencias)
        self.entry_busqueda.bind("<Return>",     self._buscar_exacto_enter)
        self.entry_busqueda.bind("<Down>",       lambda e: self.lista_sugerencias.focus_set())
        self.lista_sugerencias.bind("<ButtonRelease-1>", self._seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Return>",          self._seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Double-1>",        self._seleccionar_sugerencia)

        # Clic fuera cierra lista
        self.window.bind("<Button-1>", self._cerrar_lista_si_fuera, add="+")

        # ── Label nombre del producto seleccionado ────────────────────────────
        self.lbl_producto = Label(
            self.window,
            text="",
            font=("Segoe UI", 18, "bold"),
            fg="#0f6cbd",
            anchor="w",
            wraplength=900,
        )
        self.lbl_producto.grid(row=2, column=0, sticky="ew", padx=50, pady=(14, 2))

        # ── Subtítulo con código y precio de compra ───────────────────────────
        self.lbl_detalle = Label(
            self.window,
            text="",
            font=("Segoe UI", 13),
            fg="#616161",
            anchor="w",
        )
        self.lbl_detalle.grid(row=3, column=0, sticky="ew", padx=50, pady=(0, 4))

        # ── Label nombre grande (destacado) ───────────────────────────────────
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

        # ── Sección de división del producto ─────────────────────────────────
        frame_division = Frame(self.window, bg="#f0f6ff", bd=1, relief="groove")
        frame_division.grid(row=5, column=0, sticky="ew", padx=50, pady=(0, 10))
        frame_division.grid_columnconfigure(3, weight=1)

        Label(
            frame_division,
            text="✂  Dividir producto en:",
            font=("Segoe UI", 13, "bold"),
            bg="#f0f6ff",
            fg="#0f6cbd",
        ).grid(row=0, column=0, padx=(14, 6), pady=10, sticky="w")

        self.var_division = StringVar(value="1")
        self.entry_division = Entry(
            frame_division,
            textvariable=self.var_division,
            font=("Segoe UI", 14, "bold"),
            width=6,
            justify="center",
        )
        self.entry_division.grid(row=0, column=1, padx=4, pady=10)

        Label(
            frame_division,
            text="unidades",
            font=("Segoe UI", 13),
            bg="#f0f6ff",
            fg="#444",
        ).grid(row=0, column=2, padx=(2, 14), pady=10, sticky="w")

        self.lbl_precio_dividido = Label(
            frame_division,
            text="",
            font=("Segoe UI", 13),
            bg="#f0f6ff",
            fg="#616161",
            anchor="w",
        )
        self.lbl_precio_dividido.grid(row=0, column=3, padx=(10, 14), pady=10, sticky="w")

        # Recalcular al presionar Enter o al salir del campo
        self.entry_division.bind("<Return>", self._on_division_change)
        self.entry_division.bind("<FocusOut>", self._on_division_change)

        # ── Frame resultados (tabla de precios) ───────────────────────────────
        frame_resultados = Frame(self.window)
        frame_resultados.grid(row=6, column=0, sticky="nsew", padx=50, pady=(0, 20))
        frame_resultados.grid_columnconfigure(0, weight=1)
        frame_resultados.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(6, weight=1)

        _FONT_TABLA      = ("Helvetica", 42, "bold")
        _FONT_ENCABEZADO = ("Helvetica", 28, "bold")
        _BG_HDR  = "#003B8E"
        _BG_ALT  = "#f0f6ff"
        _BG_NORM = "#ffffff"

        # Encabezados
        Label(frame_resultados, text="Margen (%)",
              font=_FONT_ENCABEZADO, bg=_BG_HDR, fg="white",
              anchor="center", pady=10
        ).grid(row=0, column=0, sticky="ew", padx=(0, 1))
        Label(frame_resultados, text="Precio sugerido",
              font=_FONT_ENCABEZADO, bg=_BG_HDR, fg="white",
              anchor="center", pady=10
        ).grid(row=0, column=1, sticky="ew")

        # Filas de resultados — referencias para actualizar en _mostrar_precios
        self._filas_margen = []
        self._filas_precio = []
        for i, m in enumerate([10, 15, 20, 30, 40, 50]):
            bg = _BG_ALT if i % 2 == 0 else _BG_NORM
            lbl_m = Label(frame_resultados, text=f"{m}%",
                          font=_FONT_TABLA, bg=bg, fg="#003B8E",
                          anchor="center", pady=8)
            lbl_m.grid(row=i + 1, column=0, sticky="ew", padx=(0, 1), pady=1)
            lbl_p = Label(frame_resultados, text="—",
                          font=_FONT_TABLA, bg=bg, fg="#1a1a1a",
                          anchor="e", padx=30, pady=8)
            lbl_p.grid(row=i + 1, column=1, sticky="ew", pady=1)
            self._filas_margen.append(lbl_m)
            self._filas_precio.append(lbl_p)

        self.tree = None  # reemplazado por Labels directos


    # ──────────────────────────────────────────────────────────────────────────
    # BÚSQUEDA Y SUGERENCIAS
    # ──────────────────────────────────────────────────────────────────────────

    def _buscar_sugerencias(self, event):
        """Muestra sugerencias mientras el usuario escribe."""
        # Ignorar teclas de navegación
        if event.keysym in ("Return", "Up", "Down", "Escape", "Tab"):
            if event.keysym == "Escape":
                self._ocultar_lista()
            return

        texto = self.entry_busqueda.get().strip()

        if len(texto) < 1:
            self._ocultar_lista()
            return

        resultados = DatabaseManager.buscar_productos_like(texto, limit=30)

        if not resultados:
            self._ocultar_lista()
            return

        self.lista_sugerencias.delete(0, END)
        self._sugerencias_data.clear()

        for cod, desc in resultados:
            producto = DatabaseManager.buscar_producto_por_codigo(cod)
            precio = producto['precio_compra'] if producto else 0
            self.lista_sugerencias.insert(
                END,
                f"{cod}  —  {desc}  —  {format_precio_display(precio)}"
            )
            self._sugerencias_data.append({
                'codigo': cod,
                'descripcion': desc,
                'precio_compra': float(precio) if producto else 0.0,
            })

        # ── Posicionar el frame_lista debajo del entry ────────────────────────
        self.window.update_idletasks()

        # Coordenadas relativas a self.window
        ex = self.entry_busqueda.winfo_rootx() - self.window.winfo_rootx()
        ey = self.entry_busqueda.winfo_rooty() - self.window.winfo_rooty()
        ew = self.entry_busqueda.winfo_width()
        eh = self.entry_busqueda.winfo_height()

        # Ancho mínimo 600, máximo el del entry
        lista_w = max(ew, 600)

        self.frame_lista.place(x=ex, y=ey + eh + 2, width=lista_w)
        self.frame_lista.lift()   # traer al frente

    def _ocultar_lista(self):
        self.frame_lista.place_forget()

    def _cerrar_lista_si_fuera(self, event):
        """Cierra la lista si se hace clic fuera de ella."""
        widget = event.widget
        if widget not in (self.lista_sugerencias, self.entry_busqueda, self.frame_lista):
            self._ocultar_lista()

    # ──────────────────────────────────────────────────────────────────────────
    # SELECCIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _seleccionar_sugerencia(self, event):
        """Selecciona la sugerencia con clic simple o Enter."""
        sel = self.lista_sugerencias.curselection()
        if not sel:
            return

        idx = sel[0]
        if idx >= len(self._sugerencias_data):
            return

        datos = self._sugerencias_data[idx]
        self._aplicar_producto(
            datos['codigo'],
            datos['descripcion'],
            datos['precio_compra']
        )

    def _buscar_exacto_enter(self, event):
        """Al presionar Enter en el Entry, busca coincidencia exacta por EAN."""
        texto = self.entry_busqueda.get().strip()
        if not texto:
            return

        # 1) Buscar coincidencia exacta por código de barras / EAN
        producto = DatabaseManager.buscar_producto_por_codigo(texto)

        if producto:
            self._aplicar_producto(
                producto['codigo_barras'],
                producto['descripcion'],
                float(producto['precio_compra'])
            )
            return

        # 2) Si no hay exacta, intentar con la primera sugerencia visible
        if self._sugerencias_data:
            datos = self._sugerencias_data[0]
            self._aplicar_producto(
                datos['codigo'],
                datos['descripcion'],
                datos['precio_compra']
            )

    def _aplicar_producto(self, codigo: str, descripcion: str, precio_compra: float):
        """Actualiza la UI con el producto seleccionado."""
        # Consultar siempre datos frescos desde la BD
        producto = DatabaseManager.buscar_producto_por_codigo(codigo)
        if producto:
            precio_compra = float(producto['precio_compra'])
            descripcion = producto['descripcion']

        # Guardar precio base original
        self._precio_compra_base = precio_compra

        # Actualizar entry
        self.entry_busqueda.delete(0, END)
        self.entry_busqueda.insert(0, codigo)
        self._ocultar_lista()

        # Resetear divisor a 1
        self.var_division.set("1")
        self.lbl_precio_dividido.config(text="")

        # Actualizar labels
        self.lbl_producto.config(text=descripcion)
        self.lbl_nombre_grande.config(text=descripcion)
        self.lbl_detalle.config(
            text=f"Código: {codigo}   |   Precio de compra: {format_precio_display(precio_compra)}"
        )

        self._mostrar_precios(precio_compra)

    # ──────────────────────────────────────────────────────────────────────────
    # DIVISIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _on_division_change(self, event=None):
        """Se ejecuta cada vez que cambia el valor del Entry de división."""
        if self._precio_compra_base <= 0:
            return

        texto = self.entry_division.get().strip()

        # Validar que sea número entero positivo
        try:
            divisor = int(texto)
            if divisor < 1:
                raise ValueError
        except ValueError:
            self.lbl_precio_dividido.config(text="⚠ Ingrese un número entero mayor a 0", fg="#c0392b")
            return

        precio_dividido = self._precio_compra_base / divisor

        if divisor == 1:
            self.lbl_precio_dividido.config(text="", fg="#616161")
            # ✅ Restaurar lbl_detalle al precio base original
            self.lbl_detalle.config(
                text=f"Código: {self.entry_busqueda.get().strip()}   |   "
                     f"Precio de compra: {format_precio_display(self._precio_compra_base)}"
            )
        else:
            self.lbl_precio_dividido.config(
                text=f"→  Precio unitario: {format_precio_display(precio_dividido)}  "
                     f"({format_precio_display(self._precio_compra_base)} ÷ {divisor})",
                fg="#0f6cbd",
            )
            # ✅ Actualizar lbl_detalle con el precio dividido
            self.lbl_detalle.config(
                text=f"Código: {self.entry_busqueda.get().strip()}   |   "
                     f"Precio de compra: {format_precio_display(self._precio_compra_base)}   |   "
                     f"Precio unitario (÷{divisor}): {format_precio_display(precio_dividido)}"
            )

        self._mostrar_precios(precio_dividido)

    # ──────────────────────────────────────────────────────────────────────────
    # CÁLCULO DE PRECIOS
    # ──────────────────────────────────────────────────────────────────────────

    def _mostrar_precios(self, precio_compra: float):
        """Calcula y muestra precios sugeridos con diferentes márgenes."""
        margenes = [10, 15, 20, 30, 40, 50]
        for i, m in enumerate(margenes):
            precio_sugerido = precio_compra / (1 - m / 100)
            self._filas_precio[i].config(text=format_precio_display(precio_sugerido))