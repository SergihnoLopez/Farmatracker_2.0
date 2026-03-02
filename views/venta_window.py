"""
Ventana de Ventas - FarmaProStocker
✅ Edición de precio unitario con doble clic en columna "Precio Unit."
✅ Fraccionamiento de productos CJ con doble clic en columna "Cantidad"
   - Muestra opciones de fracción con precio proporcional
   - Cancelar restaura la unidad completa original
   - Descuenta fracción decimal del inventario
✅ Servicios rápidos: Inyectología, Toma de Tensión, Curaciones, Otros
   - Sin afectar inventario
   - Precio editable con doble clic
   - Utilidad 100% (sin impuestos ni cargos)
"""
from tkinter import (Toplevel, Frame, Label, Entry, Button, Listbox,
                     messagebox, END, W, BOTH, Toplevel as ToplevelAlias,
                     StringVar, Radiobutton)
from tkinter import ttk
import tkinter as tk
from pathlib import Path
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager
from controllers.ventas import VentasController
from views.kit_window import KitWindow

# ── Fuentes opcionales ────────────────────────────────────────────────────────
_FONT_REGULAR = Path(__file__).parent.parent / "resources" / "ArialNarrow.ttf"
_FONT_BOLD    = Path(__file__).parent.parent / "resources" / "ArialNarrowBold.ttf"


def _fuentes_disponibles():
    return _FONT_REGULAR.exists() and _FONT_BOLD.exists()


# ==============================================================================
# OPCIONES DE FRACCIONAMIENTO
# Formato: (label_mostrado, divisor, descripcion)
# El divisor indica cuántas fracciones tiene la caja/unidad mayor
# ==============================================================================
OPCIONES_FRACCION = [
    ("3 — Sobre×10  (caja de 30)",   30,  3),
    ("3 — Sobre×8   (caja de 24)",   24,  3),
    ("30 — Unidad   (caja×30)",      30, 30),
    ("10 — Sobre×10 (caja de 100)", 100, 10),
    ("100 — Unidad  (caja de 100)", 100, 100),
]

# ==============================================================================
# SERVICIOS — código especial SVC-*, sin descuento de inventario, impuesto=0
# ==============================================================================
SERVICIOS = [
    {"codigo": "SVC-INYEC",   "descripcion": "INYECTOLOGÍA",    "precio": 2000, "emoji": "💉"},
    {"codigo": "SVC-TENSION", "descripcion": "TOMA DE TENSIÓN", "precio": 1000, "emoji": "🩺"},
    {"codigo": "SVC-CURAC",   "descripcion": "CURACIONES",      "precio": 8000, "emoji": "🩹"},
    {"codigo": "SVC-OTROS",   "descripcion": "OTROS SERVICIOS", "precio": 5000, "emoji": "➕"},
]


# ==============================================================================
# MÉTODOS DE PAGO
# ==============================================================================
METODOS_PAGO = [
    ("Efectivo",         "Efectivo"),
    ("Nequi",            "Nequi"),
    ("QR Bancolombia",   "QR Bancolombia"),
    ("Daviplata",        "Daviplata"),
    ("Tarjeta Deb/Créd", "Tarjeta Deb/Créd"),
]
_PAGO_COLOR = {
    "Efectivo":         "#2e7d32",
    "Nequi":            "#6a0dad",
    "QR Bancolombia":   "#e65100",
    "Daviplata":        "#c62828",
    "Tarjeta Deb/Créd": "#1565C0",
}

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
        self.metodo_pago_var = StringVar(master=self.window, value="Efectivo")
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

        # ── Tipo de venta: Unidad / Fracción ────────────────────────────────
        Label(frame_entrada, text="Tipo de venta:", font=FONT_STYLE).grid(
            row=1, column=0, padx=5, pady=5, sticky=W
        )

        frame_tipo_venta = Frame(frame_entrada)
        frame_tipo_venta.grid(row=1, column=1, padx=5, pady=5, sticky=W)

        self.tipo_venta_var = StringVar(master=self.window, value="unidad")

        Radiobutton(
            frame_tipo_venta, text="Unidad",
            variable=self.tipo_venta_var, value="unidad",
            font=FONT_STYLE, cursor="hand2",
            command=self._toggle_tipo_venta
        ).pack(side="left", padx=(0, 12))

        Radiobutton(
            frame_tipo_venta, text="Fracción",
            variable=self.tipo_venta_var, value="fraccion",
            font=FONT_STYLE, cursor="hand2",
            command=self._toggle_tipo_venta
        ).pack(side="left")

        # ── Campo cantidad (modo Unidad) ─────────────────────────────────────
        self.lbl_cantidad = Label(frame_entrada, text="Cantidad:", font=FONT_STYLE)
        self.lbl_cantidad.grid(row=2, column=0, padx=5, pady=5, sticky=W)
        self.cantidad_entry = Entry(frame_entrada, width=30, font=FONT_STYLE)
        self.cantidad_entry.grid(row=2, column=1, padx=5, pady=5)

        # ── Campos fracción (modo Fracción) — ocultos por defecto ────────────
        self.lbl_cant_caja = Label(frame_entrada, text="Cantidad en caja:", font=FONT_STYLE)
        self.entry_cant_caja = Entry(frame_entrada, width=30, font=FONT_STYLE)

        self.lbl_unidades_fraccion = Label(frame_entrada, text="Unidades:", font=FONT_STYLE)
        self.entry_unidades_fraccion = Entry(frame_entrada, width=30, font=FONT_STYLE)

        self.lbl_resultado_fraccion = Label(
            frame_entrada, text="",
            font=("Titillium Web", 10, "bold"), fg="#003B8E"
        )

        # Calcular automáticamente al escribir en los campos de fracción
        self.entry_cant_caja.bind("<KeyRelease>", self._calcular_fraccion)
        self.entry_cant_caja.bind("<Return>", lambda e: self.entry_unidades_fraccion.focus())
        self.entry_unidades_fraccion.bind("<KeyRelease>", self._calcular_fraccion)
        self.entry_unidades_fraccion.bind("<Return>", self._agregar_con_enter)

        self.codigo_entry.bind("<Return>",  lambda e: self._focus_cantidad())
        self.cantidad_entry.bind("<Return>", self._agregar_con_enter)

        Button(
            frame_entrada, text="Agregar Producto",
            font=FONT_STYLE, bg=BTN_COLOR, fg=BTN_FG,
            command=self._agregar_producto
        ).grid(row=0, column=2, rowspan=5, padx=10, pady=5)

        # ── Treeview de venta ─────────────────────────────────────────────────
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

        # Anchos de columna
        self.tree.column("codigo_barras",   width=130)
        self.tree.column("descripcion",     width=350)
        self.tree.column("cantidad",        width=90,  anchor="center")
        self.tree.column("precio_unitario", width=130, anchor="e")
        self.tree.column("subtotal",        width=130, anchor="e")
        self.tree.column("impuesto",        width=100, anchor="center")

        self.tree.pack(fill=BOTH, expand=True, pady=10)

        # Doble clic: col Precio Unit. → editar precio | col Cantidad → fraccionar si CJ
        self.tree.bind("<Double-1>", self._on_double_click_tree)

        # ── Botones de Servicios Rápidos ──────────────────────────────────────
        frame_servicios_outer = Frame(self.window)
        frame_servicios_outer.pack(pady=(2, 0))

        Label(
            frame_servicios_outer,
            text="💊 Servicios  (doble clic en la fila para editar precio):",
            font=("Titillium Web", 10, "bold"),
            fg="#555555"
        ).pack(anchor="w", padx=10)

        frame_servicios = Frame(frame_servicios_outer)
        frame_servicios.pack(pady=4)

        # Colores por servicio
        _colores = ["#7B1FA2", "#00796B", "#E65100", "#1565C0"]
        self._servicios_precios = {}   # codigo → precio vigente (editable en runtime)

        for i, svc in enumerate(SERVICIOS):
            precio_inicial = svc["precio"]
            self._servicios_precios[svc["codigo"]] = precio_inicial

            btn = Button(
                frame_servicios,
                text=f"{svc['emoji']}  {svc['descripcion']}\n${precio_inicial:,.0f}".replace(",", "."),
                font=("Titillium Web", 11, "bold"),
                bg=_colores[i % len(_colores)],
                fg="white",
                width=18,
                height=2,
                relief="raised",
                cursor="hand2",
                command=lambda s=svc: self._agregar_servicio(s["codigo"])
            )
            btn.pack(side="left", padx=6)
            # Guardar referencia para actualizar etiqueta cuando cambie precio
            svc["_btn_ref"] = btn

        self.total_label = Label(
            self.window,
            text="Total: $0.00",
            font=("Titillium Web", 14, "bold"),
            fg="black",
        )
        self.total_label.pack(pady=5)

        # ── Selector de método de pago ────────────────────────────────
        frame_pago = Frame(self.window, bd=1, relief="groove",
                           padx=10, pady=5, bg="#f0f4f8")
        frame_pago.pack(pady=(2, 4))

        Label(frame_pago, text="💳  Método de Pago:",
              font=("Titillium Web", 10, "bold"),
              bg="#f0f4f8", fg="#003B8E").pack(side="left", padx=(0, 10))

        for label, valor in METODOS_PAGO:
            Radiobutton(
                frame_pago,
                text=label,
                variable=self.metodo_pago_var,
                value=valor,
                font=("Titillium Web", 10, "bold"),
                bg="#f0f4f8",
                fg=_PAGO_COLOR.get(valor, "#333"),
                selectcolor="#ffffff",
                activebackground="#f0f4f8",
                cursor="hand2",
            ).pack(side="left", padx=7)

        frame_botones = Frame(self.window)
        frame_botones.pack(pady=10)

        Button(frame_botones, text="Eliminar Producto",
               font=FONT_STYLE, bg="#f44336", fg="white",
               command=self._eliminar_producto, width=18).pack(side="left", padx=5)

        Button(frame_botones, text="🧪 Armar Kit",
               font=FONT_STYLE, bg="#7B1FA2", fg="white",
               command=self._abrir_armar_kit, width=16).pack(side="left", padx=5)

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
            for item in resultados:
                cod  = item[0]
                desc = item[1]
                # buscar_productos_like retorna (codigo, descripcion, cantidad)
                # Se respetan decimales: 48.0 → "48"  |  0.15 → "0.15"
                try:
                    stock_val = float(item[2]) if len(item) > 2 and item[2] is not None else 0.0
                    stock_str = str(int(stock_val)) if stock_val == int(stock_val) else str(stock_val)
                except (ValueError, TypeError):
                    stock_str = "0"
                self.lista_sugerencias.insert(END, f"{cod} - {desc} (Stock: {stock_str})")

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
            self._focus_cantidad()

    def _toggle_tipo_venta(self):
        """Muestra u oculta los campos de fracción según el tipo de venta."""
        if self.tipo_venta_var.get() == "fraccion":
            # Ocultar campo cantidad simple y su label
            self.lbl_cantidad.grid_remove()
            self.cantidad_entry.grid_remove()
            # Mostrar campos de fracción
            self.lbl_cant_caja.grid(row=2, column=0, padx=5, pady=5, sticky=W)
            self.entry_cant_caja.grid(row=2, column=1, padx=5, pady=5)
            self.lbl_unidades_fraccion.grid(row=3, column=0, padx=5, pady=5, sticky=W)
            self.entry_unidades_fraccion.grid(row=3, column=1, padx=5, pady=5)
            self.lbl_resultado_fraccion.grid(row=4, column=1, padx=5, pady=(0, 5), sticky=W)
            self.entry_cant_caja.focus()
        else:
            # Ocultar campos de fracción
            self.lbl_cant_caja.grid_remove()
            self.entry_cant_caja.grid_remove()
            self.lbl_unidades_fraccion.grid_remove()
            self.entry_unidades_fraccion.grid_remove()
            self.lbl_resultado_fraccion.grid_remove()
            # Mostrar campo cantidad simple y su label
            self.lbl_cantidad.grid(row=2, column=0, padx=5, pady=5, sticky=W)
            self.cantidad_entry.grid(row=2, column=1, padx=5, pady=5)
            self.cantidad_entry.focus()

    def _calcular_fraccion(self, event=None):
        """Calcula Cantidad = Unidades / Cantidad en caja y actualiza el label."""
        try:
            cant_caja = float(self.entry_cant_caja.get().strip())
            unidades = float(self.entry_unidades_fraccion.get().strip())
            if cant_caja <= 0:
                self.lbl_resultado_fraccion.config(
                    text="⚠ Cantidad en caja debe ser mayor a 0", fg="#d13438"
                )
                return
            resultado = unidades / cant_caja
            self.lbl_resultado_fraccion.config(
                text=f"→ Cantidad a descontar: {resultado:.6f}",
                fg="#003B8E"
            )
        except (ValueError, ZeroDivisionError):
            self.lbl_resultado_fraccion.config(text="", fg="#003B8E")

    def _focus_cantidad(self):
        """Da foco al campo correcto según el tipo de venta."""
        if self.tipo_venta_var.get() == "fraccion":
            self.entry_cant_caja.focus()
        else:
            self.cantidad_entry.focus()

    def _agregar_con_enter(self, event):
        self._agregar_producto()

    def _agregar_producto(self):
        # Si es fracción, calcular y poner resultado en cantidad_entry
        if self.tipo_venta_var.get() == "fraccion":
            try:
                cant_caja = float(self.entry_cant_caja.get().strip())
                unidades = float(self.entry_unidades_fraccion.get().strip())
                if cant_caja <= 0:
                    messagebox.showerror("Error", "Cantidad en caja debe ser mayor a 0")
                    return
                if unidades <= 0:
                    messagebox.showerror("Error", "Unidades debe ser mayor a 0")
                    return
                cantidad_final = unidades / cant_caja
                self.cantidad_entry.delete(0, 'end')
                self.cantidad_entry.insert(0, str(round(cantidad_final, 6)))
            except ValueError:
                messagebox.showerror("Error", "Ingrese valores numéricos válidos en los campos de fracción")
                return

        if VentasController.agregar_producto_a_venta(
            self.tree, self.codigo_entry, self.cantidad_entry
        ):
            self._actualizar_total()
            # Limpiar campos de fracción
            self.entry_cant_caja.delete(0, 'end')
            self.entry_unidades_fraccion.delete(0, 'end')
            self.lbl_resultado_fraccion.config(text="")
            self.codigo_entry.focus()

    def _actualizar_total(self):
        total = sum(float(self.tree.item(i, "values")[4])
                    for i in self.tree.get_children())
        self.total_label.config(text=f"Total: ${total:,.0f}".replace(",", "."))

    # ──────────────────────────────────────────────────────────────────────────
    # SERVICIOS RÁPIDOS
    # ──────────────────────────────────────────────────────────────────────────

    def _agregar_servicio(self, codigo_svc: str):
        """
        Agrega un servicio a la venta. Sin afectar inventario.
        Impuesto = 0%, utilidad = 100%.
        """
        svc = next((s for s in SERVICIOS if s["codigo"] == codigo_svc), None)
        if not svc:
            return

        precio = self._servicios_precios.get(codigo_svc, svc["precio"])
        subtotal = precio * 1  # cantidad siempre 1 por fila (se puede editar)

        self.tree.insert("", END, values=(
            codigo_svc,
            svc["descripcion"],
            1,
            precio,
            subtotal,
            "0%"
        ))
        self._actualizar_total()
        self.codigo_entry.focus()

    # ──────────────────────────────────────────────────────────────────────────
    # ✅ EDICIÓN DE PRECIO CON DOBLE CLIC
    # ──────────────────────────────────────────────────────────────────────────

    def _on_double_click_tree(self, event):
        """
        Doble clic en el treeview:
          #3 (Cantidad)     → si und=CJ abre diálogo de fraccionamiento,
                              si es servicio SVC- edita cantidad sin stock,
                              si no, abre editor de cantidad normal.
          #4 (Precio Unit.) → abre editor de precio (productos y servicios).
        """
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row:
            return

        valores = list(self.tree.item(row, "values"))
        codigo = valores[0]
        es_servicio = str(codigo).startswith("SVC-")

        if col == "#3":
            if es_servicio:
                self._editar_cantidad_servicio(row)
            else:
                producto = DatabaseManager.buscar_producto_por_codigo(codigo)
                unidad = str(producto.get("unidad", "")).strip().upper() if producto else ""
                if unidad == "CJ":
                    self._mostrar_dialogo_fraccion(row, valores, producto)
                else:
                    self._editar_cantidad(row)
            return

        if col == "#4":
            if es_servicio:
                self._editar_precio_servicio(row, codigo)
            else:
                self._editar_precio_unitario(row)

    def _editar_precio_unitario(self, item_id):
        """Muestra un Entry flotante sobre la celda de precio para editarlo."""
        # Obtener bbox de la celda (#4)
        bbox = self.tree.bbox(item_id, "#4")
        if not bbox:
            return
        x, y, w, h = bbox

        valores = list(self.tree.item(item_id, "values"))
        precio_actual = str(valores[3])

        editor = Entry(self.tree, font=FONT_STYLE, justify="right")
        editor.place(x=x, y=y, width=w, height=h)
        editor.insert(0, precio_actual)
        editor.select_range(0, END)
        editor.focus_set()

        def confirmar(event=None):
            nuevo_precio_str = editor.get().strip().replace(".", "").replace(",", "")
            try:
                nuevo_precio = float(nuevo_precio_str)
                if nuevo_precio < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Precio inválido. Ingrese un número positivo.")
                editor.destroy()
                return

            # Recalcular subtotal
            try:
                cantidad = float(valores[2])
            except (ValueError, IndexError):
                cantidad = 1.0

            nuevo_subtotal = nuevo_precio * cantidad
            valores[3] = nuevo_precio
            valores[4] = nuevo_subtotal
            self.tree.item(item_id, values=tuple(valores))
            self._actualizar_total()
            editor.destroy()

        def cancelar(event=None):
            editor.destroy()

        editor.bind("<Return>",   confirmar)
        editor.bind("<Tab>",      confirmar)
        editor.bind("<Escape>",   cancelar)
        editor.bind("<FocusOut>", cancelar)

    def _editar_precio_servicio(self, item_id, codigo_svc: str):
        """
        Edita el precio de un servicio en la fila seleccionada.
        Actualiza también el precio por defecto del botón para esa sesión.
        """
        bbox = self.tree.bbox(item_id, "#4")
        if not bbox:
            return
        x, y, w, h = bbox

        valores = list(self.tree.item(item_id, "values"))
        precio_actual = str(valores[3])

        editor = Entry(self.tree, font=FONT_STYLE, justify="right")
        editor.place(x=x, y=y, width=w, height=h)
        editor.insert(0, precio_actual)
        editor.select_range(0, END)
        editor.focus_set()

        def confirmar(event=None):
            nuevo_str = editor.get().strip().replace(".", "").replace(",", "")
            try:
                nuevo_precio = float(nuevo_str)
                if nuevo_precio < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Precio inválido. Ingrese un número positivo.")
                editor.destroy()
                return

            try:
                cantidad = float(valores[2])
            except (ValueError, IndexError):
                cantidad = 1.0

            nuevo_subtotal = nuevo_precio * cantidad
            valores[3] = nuevo_precio
            valores[4] = nuevo_subtotal
            self.tree.item(item_id, values=tuple(valores))

            # Actualizar precio vigente en memoria y etiqueta del botón
            self._servicios_precios[codigo_svc] = nuevo_precio
            svc = next((s for s in SERVICIOS if s["codigo"] == codigo_svc), None)
            if svc and svc.get("_btn_ref"):
                svc["_btn_ref"].config(
                    text=f"{svc['emoji']}  {svc['descripcion']}\n${nuevo_precio:,.0f}".replace(",", ".")
                )

            self._actualizar_total()
            editor.destroy()

        editor.bind("<Return>",   confirmar)
        editor.bind("<Tab>",      confirmar)
        editor.bind("<Escape>",   lambda e: editor.destroy())
        editor.bind("<FocusOut>", lambda e: editor.destroy())

    def _editar_cantidad_servicio(self, item_id):
        """
        Edita la cantidad de un servicio (sin verificación de stock).
        """
        bbox = self.tree.bbox(item_id, "#3")
        if not bbox:
            return
        x, y, w, h = bbox

        valores = list(self.tree.item(item_id, "values"))

        editor = Entry(self.tree, font=FONT_STYLE, justify="center")
        editor.place(x=x, y=y, width=w, height=h)
        editor.insert(0, str(valores[2]))
        editor.select_range(0, END)
        editor.focus_set()

        def confirmar(event=None):
            try:
                nueva_cant = float(editor.get().strip().replace(",", "."))
                if nueva_cant <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Cantidad inválida.")
                editor.focus_set()
                return

            precio_unitario = float(valores[3])
            nuevo_subtotal = precio_unitario * nueva_cant
            cant_display = int(nueva_cant) if nueva_cant == int(nueva_cant) else round(nueva_cant, 2)
            valores[2] = cant_display
            valores[4] = nuevo_subtotal
            self.tree.item(item_id, values=tuple(valores))
            self._actualizar_total()
            editor.destroy()

        editor.bind("<Return>", confirmar)
        editor.bind("<Escape>", lambda e: editor.destroy())
        editor.bind("<FocusOut>", lambda e: editor.destroy())

    # ──────────────────────────────────────────────────────────────────────────
    # FRACCIONAMIENTO Y EDICIÓN DE CANTIDAD
    # ──────────────────────────────────────────────────────────────────────────

    def _editar_cantidad(self, item_id):
        """
        Muestra un Entry flotante sobre la celda de cantidad para editarla.
        ✅ FRACCIÓN: acepta decimales como 0.2, 1.5, 0.333
        """
        bbox = self.tree.bbox(item_id, "#3")
        if not bbox:
            return
        x, y, w, h = bbox

        valores = list(self.tree.item(item_id, "values"))
        cantidad_actual = str(valores[2])
        codigo = valores[0]

        editor = Entry(self.tree, font=FONT_STYLE, justify="center")
        editor.place(x=x, y=y, width=w, height=h)
        editor.insert(0, cantidad_actual)
        editor.select_range(0, END)
        editor.focus_set()

        def confirmar(event=None):
            texto_val = editor.get().strip().replace(",", ".")
            try:
                nueva_cant = float(texto_val)
                if nueva_cant <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Cantidad inválida.\nEjemplos válidos: 1, 2, 0.5, 0.2, 1.333"
                )
                editor.focus_set()
                return

            # Verificar stock disponible
            producto = DatabaseManager.buscar_producto_por_codigo(codigo)
            if producto:
                stock = float(producto["cantidad"])
                if nueva_cant > stock:
                    messagebox.showerror(
                        "Stock Insuficiente",
                        f"Stock disponible: {stock}\nCantidad solicitada: {nueva_cant}"
                    )
                    editor.focus_set()
                    return

            # Actualizar cantidad y recalcular subtotal
            precio_unitario = float(valores[3])
            nuevo_subtotal = precio_unitario * nueva_cant
            cant_display = int(nueva_cant) if nueva_cant == int(nueva_cant) else round(nueva_cant, 6)
            valores[2] = cant_display
            valores[4] = nuevo_subtotal
            self.tree.item(item_id, values=valores)
            self._actualizar_total()
            editor.destroy()

        editor.bind("<Return>", confirmar)
        editor.bind("<Escape>", lambda e: editor.destroy())
        editor.bind("<FocusOut>", lambda e: editor.destroy())


    def _mostrar_dialogo_fraccion(self, item_id, valores_actuales, producto_bd):
        """
        Ventana emergente para seleccionar la fracción a vender.
        Cancelar restaura cantidad=1 y precio original de la caja.
        """
        # Guardar valores originales de la caja para poder restaurarlos con Cancelar
        precio_caja_original  = float(producto_bd["precio_venta"])
        cant_original         = 1  # una caja completa
        subtotal_original     = precio_caja_original * cant_original
        precio_caja = float(valores_actuales[3])   # precio actual en el tree (puede haber sido editado)
        desc = valores_actuales[1]

        dialogo = Toplevel(self.window)
        dialogo.title("Fraccionar Producto")
        dialogo.geometry("480x400")
        dialogo.resizable(False, False)
        dialogo.transient(self.window)
        dialogo.grab_set()

        # Encabezado
        Label(
            dialogo,
            text="📦 Fraccionamiento de Caja",
            font=("Titillium Web", 15, "bold"),
            fg="#003B8E"
        ).pack(pady=(15, 5))

        Label(
            dialogo,
            text=desc,
            font=("Titillium Web", 11),
            fg="#555555",
            wraplength=440
        ).pack(pady=(0, 5))

        Label(
            dialogo,
            text=f"Precio caja: ${precio_caja:,.0f}".replace(",", "."),
            font=("Titillium Web", 11, "bold"),
            fg="#222222"
        ).pack(pady=(0, 10))

        # Marco con opciones
        frame_opciones = Frame(dialogo, bd=1, relief="solid", padx=10, pady=10)
        frame_opciones.pack(fill="x", padx=20)

        Label(
            frame_opciones,
            text="Seleccione cómo desea vender:",
            font=("Titillium Web", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        seleccion_var = tk.IntVar(value=-1)

        # Botones de opción con precio calculado
        for idx, (label, total_unidades, cant_fraccion) in enumerate(OPCIONES_FRACCION):
            precio_fraccion = precio_caja / total_unidades * cant_fraccion
            texto_btn = (
                f"  {label}\n"
                f"  → Descuenta {cant_fraccion}/{total_unidades} de caja  |  "
                f"Precio: ${precio_fraccion:,.0f}".replace(",", ".")
            )
            rb = tk.Radiobutton(
                frame_opciones,
                text=texto_btn,
                variable=seleccion_var,
                value=idx,
                font=("Arial", 10),
                justify="left",
                anchor="w"
            )
            rb.pack(fill="x", pady=2)

        # Botones Aceptar / Cancelar
        frame_btns = Frame(dialogo)
        frame_btns.pack(pady=15)

        def confirmar_fraccion():
            idx = seleccion_var.get()
            if idx < 0:
                messagebox.showwarning(
                    "Aviso", "Seleccione una opción de fraccionamiento.", parent=dialogo
                )
                return

            label, total_unidades, cant_fraccion = OPCIONES_FRACCION[idx]

            # Fracción del inventario que se descuenta (ej: 3/30 = 0.1)
            fraccion_inventario = cant_fraccion / total_unidades

            # Precio proporcional a la fracción
            precio_fraccion = precio_caja / total_unidades * cant_fraccion

            # Actualizar fila en treeview:
            # cantidad queda como la fracción decimal,
            # precio_unitario pasa a ser el de la fracción,
            # subtotal = fraccion * precio_fraccion (pero cantidad ya refleja eso)
            subtotal_nuevo = precio_fraccion  # 1 "unidad fraccionada"

            nuevos_valores = list(valores_actuales)
            nuevos_valores[2] = round(fraccion_inventario, 6)  # cantidad a descontar
            nuevos_valores[3] = round(precio_fraccion, 2)       # precio fraccion
            nuevos_valores[4] = round(subtotal_nuevo, 2)        # subtotal

            self.tree.item(item_id, values=tuple(nuevos_valores))
            self._actualizar_total()
            dialogo.destroy()
            self.codigo_entry.focus()

        Button(
            frame_btns,
            text="✅ Confirmar",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            width=14,
            command=confirmar_fraccion
        ).pack(side="left", padx=8)

        def cancelar_fraccion():
            # Restaurar fila a la unidad completa original
            restaurados = list(valores_actuales)
            restaurados[2] = cant_original
            restaurados[3] = round(precio_caja_original, 2)
            restaurados[4] = round(subtotal_original, 2)
            self.tree.item(item_id, values=tuple(restaurados))
            self._actualizar_total()
            dialogo.destroy()

        Button(
            frame_btns,
            text="Cancelar",
            font=FONT_STYLE,
            bg="#f44336",
            fg="white",
            width=12,
            command=cancelar_fraccion
        ).pack(side="left", padx=8)

    # ──────────────────────────────────────────────────────────────────────────
    # ACCIONES PRINCIPALES
    # ──────────────────────────────────────────────────────────────────────────

    def _abrir_armar_kit(self):
        """Abre el formulario para armar un kit compuesto."""
        KitWindow(self)

    def _eliminar_producto(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        for item in selected:
            self.tree.delete(item)
        self._actualizar_total()

    def _registrar_venta(self):
        metodo = self.metodo_pago_var.get()
        if VentasController.registrar_venta(self.tree, metodo_pago=metodo):
            messagebox.showinfo("Éxito", "Venta registrada correctamente")
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._actualizar_total()
            self.metodo_pago_var.set("Efectivo")  # resetear a predeterminado
            self.codigo_entry.focus()

    # ──────────────────────────────────────────────────────────────────────────
    # GENERACIÓN DE FACTURA
    # ──────────────────────────────────────────────────────────────────────────

    def _imprimir_factura(self):
        """Genera la factura PDF tipo ticket 72 mm con FacturaGenerator."""
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "No hay productos en la venta")
            return

        # FacturaGenerator espera lista de listas:
        # [codigo, descripcion, cantidad, precio_unitario, subtotal, impuesto]
        productos = []
        for item in items:
            v = self.tree.item(item, "values")
            productos.append([
                v[0],
                v[1],
                v[2],
                v[3],
                v[4],
                v[5] if len(v) > 5 else "",
            ])

        try:
            import os
            from utils.pdf_generator import FacturaGenerator
            ruta = "factura_flexible.pdf"
            metodo = self.metodo_pago_var.get()
            gen = FacturaGenerator(productos, metodo_pago=metodo)
            if gen.generar(ruta):
                if os.name == "nt":
                    os.startfile(ruta)
                else:
                    os.system(f"xdg-open '{ruta}'")
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF.\nRevisa logs/farmatrack.log para detalles.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la factura:\n{e}")