"""
Ventana de liquidador de precios - FarmaTrack
✅ grab_set() implementado
✅ Listbox de sugerencias correctamente posicionado y visible
✅ Clic simple selecciona sugerencia
✅ Enter busca coincidencia exacta por EAN
✅ Nombre del producto se muestra tras selección
✅ División de precio de compra con recálculo automático
"""
from tkinter import (Toplevel, Frame, Label, Entry, Listbox, END, Scrollbar,
                     VERTICAL, RIGHT, LEFT, Y, BOTH, StringVar, W, messagebox)
from tkinter import ttk
from config.settings import FONT_STYLE
from models.database import DatabaseManager, get_db_connection
from utils.formatters import format_precio_display, format_precio_miles
import logging


class LiquidadorWindow:
    """Ventana para calcular precios de venta sugeridos"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Liquidador de Precios")
        self.window.state("zoomed")
        self.window.grab_set()

        self._sugerencias_data = []     # lista de dicts con datos de cada sugerencia
        self._precio_compra_base = 0.0  # precio original sin dividir
        self._producto_seleccionado = None  # dict completo del producto actual
        self._editing_widget = None     # widget Entry temporal para edición inline
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

        # ── Sección de información del inventario ────────────────────────────
        self._setup_inventario_section()

    # ──────────────────────────────────────────────────────────────────────────
    # SECCIÓN INVENTARIO (Treeview editable)
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_inventario_section(self):
        """Crea el LabelFrame con el Treeview de información del inventario."""
        self.frame_inventario = ttk.LabelFrame(
            self.window,
            text="📦 Información del Inventario",
        )
        self.frame_inventario.grid(row=7, column=0, sticky="ew", padx=50, pady=(10, 20))
        self.frame_inventario.grid_columnconfigure(0, weight=1)

        # Columnas del Treeview
        columnas_inv = ("ID", "Código", "Descripción", "Cantidad",
                        "Precio Compra", "Precio Venta", "Impuesto", "Vencimiento")

        self.tree_inventario = ttk.Treeview(
            self.frame_inventario,
            columns=columnas_inv,
            show="headings",
            height=3,
        )

        # Configurar encabezados y anchos
        anchos = {
            "ID": 50, "Código": 120, "Descripción": 280, "Cantidad": 80,
            "Precio Compra": 110, "Precio Venta": 110, "Impuesto": 100, "Vencimiento": 110,
        }
        for col in columnas_inv:
            self.tree_inventario.heading(col, text=col, anchor="center")
            anchor = "w" if col == "Descripción" else "center"
            self.tree_inventario.column(col, width=anchos[col], anchor=anchor, minwidth=40)

        # Scrollbar
        sb_inv = Scrollbar(self.frame_inventario, orient=VERTICAL,
                           command=self.tree_inventario.yview)
        self.tree_inventario.configure(yscrollcommand=sb_inv.set)

        self.tree_inventario.pack(side=LEFT, fill=BOTH, expand=True, padx=(8, 0), pady=8)
        sb_inv.pack(side=RIGHT, fill=Y, padx=(0, 8), pady=8)

        # Doble clic para editar celdas
        self.tree_inventario.bind("<Double-1>", self._on_inventario_doble_clic)

        # Columnas editables (mapeo display → campo BD)
        self._columnas_editables = {
            "Cantidad":      "cantidad",
            "Precio Compra": "precio_compra",
            "Precio Venta":  "precio_venta",
            "Impuesto":      "impuesto",
            "Vencimiento":   "fecha_vencimiento",
        }

    def _cargar_inventario_producto(self, codigo: str):
        """Carga los datos del producto en el Treeview de inventario."""
        # Limpiar treeview
        for item in self.tree_inventario.get_children():
            self.tree_inventario.delete(item)

        producto = DatabaseManager.buscar_producto_por_codigo(codigo)
        if not producto:
            return

        self._producto_seleccionado = dict(producto)

        self.tree_inventario.insert("", "end", iid="prod_0", values=(
            producto.get("id_producto", ""),
            producto.get("codigo_barras", ""),
            producto.get("descripcion", ""),
            producto.get("cantidad", 0),
            format_precio_miles(producto.get("precio_compra", 0)),
            format_precio_miles(producto.get("precio_venta", 0)),
            producto.get("impuesto", ""),
            producto.get("fecha_vencimiento", ""),
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # EDICIÓN INLINE EN TREEVIEW DE INVENTARIO
    # ──────────────────────────────────────────────────────────────────────────

    def _on_inventario_doble_clic(self, event):
        """Inicia edición inline al hacer doble clic en una celda editable."""
        # Destruir editor previo si existe
        self._cancelar_edicion()

        region = self.tree_inventario.identify_region(event.x, event.y)
        if region != "cell":
            return

        item_id = self.tree_inventario.identify_row(event.y)
        column_id = self.tree_inventario.identify_column(event.x)

        if not item_id or not column_id:
            return

        # column_id es "#1", "#2", etc.
        col_index = int(column_id.replace("#", "")) - 1
        columnas = self.tree_inventario["columns"]

        if col_index >= len(columnas):
            return

        col_name = columnas[col_index]

        # Verificar si la columna es editable
        if col_name not in self._columnas_editables:
            return

        # Obtener bounding box de la celda
        bbox = self.tree_inventario.bbox(item_id, column_id)
        if not bbox:
            return

        x, y, w, h = bbox
        valor_actual = self.tree_inventario.set(item_id, col_name)

        # Para precios, limpiar el formato ($1.234) para editar el número puro
        if col_name in ("Precio Compra", "Precio Venta"):
            valor_limpio = valor_actual.replace("$", "").replace(".", "").strip()
            valor_actual = valor_limpio
        elif col_name == "Cantidad":
            # Mostrar número limpio
            valor_actual = valor_actual.strip()

        # Crear Entry superpuesto
        entry_edit = Entry(
            self.tree_inventario,
            font=("Segoe UI", 11),
            justify="center",
        )
        entry_edit.place(x=x, y=y, width=w, height=h)
        entry_edit.insert(0, valor_actual)
        entry_edit.select_range(0, END)
        entry_edit.focus_set()

        # Guardar referencia y contexto
        self._editing_widget = entry_edit
        self._editing_item = item_id
        self._editing_col = col_name

        # Bindings
        entry_edit.bind("<Return>", self._confirmar_edicion)
        entry_edit.bind("<Escape>", lambda e: self._cancelar_edicion())
        entry_edit.bind("<FocusOut>", lambda e: self._cancelar_edicion())

    def _confirmar_edicion(self, event=None):
        """Confirma la edición, actualiza Treeview y guarda en BD."""
        if not self._editing_widget:
            return

        nuevo_valor = self._editing_widget.get().strip()
        item_id = self._editing_item
        col_name = self._editing_col
        campo_bd = self._columnas_editables.get(col_name)

        # Destruir el widget de edición
        self._editing_widget.destroy()
        self._editing_widget = None

        if not campo_bd or not self._producto_seleccionado:
            return

        id_producto = self._producto_seleccionado.get("id_producto")
        if not id_producto:
            return

        # Validar según tipo de campo
        valor_bd = None
        valor_display = nuevo_valor

        try:
            if campo_bd in ("cantidad",):
                # Acepta decimales
                valor_bd = float(nuevo_valor)
                if valor_bd < 0:
                    raise ValueError("Cantidad negativa")
                # Mostrar como entero si no tiene decimales
                valor_display = str(int(valor_bd)) if valor_bd == int(valor_bd) else str(valor_bd)

            elif campo_bd in ("precio_compra", "precio_venta"):
                valor_bd = float(nuevo_valor)
                if valor_bd < 0:
                    raise ValueError("Precio negativo")
                valor_display = format_precio_miles(valor_bd)

            elif campo_bd == "impuesto":
                valor_bd = nuevo_valor
                valor_display = nuevo_valor

            elif campo_bd == "fecha_vencimiento":
                # Validar formato si no está vacío
                if nuevo_valor:
                    from datetime import datetime
                    datetime.strptime(nuevo_valor, "%Y-%m-%d")
                valor_bd = nuevo_valor
                valor_display = nuevo_valor

        except ValueError as ve:
            messagebox.showwarning(
                "Valor inválido",
                f"El valor ingresado no es válido para '{col_name}'.\n\n{ve}",
                parent=self.window,
            )
            return

        # Guardar en base de datos
        ok = DatabaseManager.actualizar_campo_producto(id_producto, campo_bd, valor_bd)

        if ok:
            # Actualizar Treeview
            self.tree_inventario.set(item_id, col_name, valor_display)

            # Actualizar dict local
            self._producto_seleccionado[campo_bd] = valor_bd

            # Si cambió precio_compra, refrescar precios del liquidador
            if campo_bd == "precio_compra":
                self._precio_compra_base = valor_bd
                self.lbl_detalle.config(
                    text=f"Código: {self._producto_seleccionado.get('codigo_barras', '')}   |   "
                         f"Precio de compra: {format_precio_display(valor_bd)}"
                )
                self.var_division.set("1")
                self.lbl_precio_dividido.config(text="")
                self._mostrar_precios(valor_bd)

            logging.info(f"Producto {id_producto}: {campo_bd} → {valor_bd}")
        else:
            messagebox.showerror(
                "Error",
                f"No se pudo guardar el cambio en '{col_name}'.",
                parent=self.window,
            )

    def _cancelar_edicion(self, event=None):
        """Cancela la edición inline destruyendo el Entry."""
        if self._editing_widget:
            try:
                self._editing_widget.destroy()
            except Exception:
                pass
            self._editing_widget = None


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

        # Cargar info de inventario en el Treeview
        self._cargar_inventario_producto(codigo)

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