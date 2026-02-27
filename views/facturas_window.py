"""
Ventana de Programación de Pago de Facturas - FarmaTrack
Droguería Irlandesa

✅ Mini-dashboard financiero (KPIs superiores)
✅ Tabla de facturas con colores por estado
✅ Filtros rápidos y por rango de fechas
✅ CRUD completo (agregar, editar fecha, marcar pagada, eliminar)
✅ Proyección de flujo de caja (7, 15, 30 días)
✅ Estadísticas por proveedor
✅ Campos: ID factura, proveedor, valor, fecha vencimiento, estado,
   método de pago, observaciones
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta

try:
    from ctk_design_system import Colors, Fonts, Dimensions
except ImportError:
    class Colors:
        PRIMARY = "#0f6cbd"; PRIMARY_HOVER = "#0c5aa6"
        SURFACE = "#ffffff"; BACKGROUND = "#f4f6f8"
        TEXT_PRIMARY = "#1a1a1a"; TEXT_SECONDARY = "#616161"
        SUCCESS = "#107c10"; ERROR = "#d13438"; WARNING = "#f7630c"
        BORDER = "#e3e6ea"
    class Fonts:
        FAMILY = "Segoe UI"
    class Dimensions:
        BUTTON_HEIGHT = 46; BUTTON_RADIUS = 8


def _fmt(v):
    """Formatea valor numérico como moneda colombiana."""
    try:
        return f"${int(round(float(v))):,}".replace(",", ".")
    except Exception:
        return str(v)


# ==============================================================================
# COLORES POR ESTADO
# ==============================================================================

TAG_COLORS = {
    "ok":      {"bg": "#e8f5e9", "fg": "#1b5e20"},   # 🟢 Verde  > 7 días
    "proxima": {"bg": "#fff8e1", "fg": "#e65100"},    # 🟡 Amarillo 4-7 días
    "urgente": {"bg": "#fff3e0", "fg": "#bf360c"},    # 🟠 Naranja ≤ 3 días
    "vencida": {"bg": "#ffebee", "fg": "#b71c1c"},    # 🔴 Rojo   vencida
    "pagada":  {"bg": "#e3f2fd", "fg": "#0d47a1"},    # 🔵 Azul   pagada
}

HDR_BG = "#003B8E"
FONT = ("Segoe UI", 12)
FONT_B = ("Segoe UI", 12, "bold")
FONT_H = ("Segoe UI", 15, "bold")
FONT_KPI_VAL = ("Segoe UI", 20, "bold")
FONT_KPI_TIT = ("Segoe UI", 10)


# ==============================================================================
# VENTANA PRINCIPAL
# ==============================================================================

class FacturasWindow:
    """Ventana de programación de pago de facturas"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("📋 Programación de Pago de Facturas – Droguería Irlandesa")
        self.window.state("zoomed")
        self.window.grab_set()
        self.window.configure(bg=Colors.BACKGROUND)

        self._filtro_actual = "todas"
        self._facturas = []

        # Inicializar tabla en BD
        from controllers.facturas import FacturasController
        FacturasController.inicializar_tabla()
        FacturasController.actualizar_estado_automatico()

        self._setup_ui()
        self._refrescar()

    # ══════════════════════════════════════════════════════════════════════════
    # INTERFAZ
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        # ── Cabecera ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self.window, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  Programación de Pago de Facturas",
                 font=("Segoe UI", 19, "bold"), bg=HDR_BG, fg="white"
                 ).pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="Droguería Irlandesa",
                 font=("Segoe UI", 13), bg=HDR_BG, fg="#a8c8f8"
                 ).pack(side="right", padx=20)

        # ── KPI Cards (mini-dashboard financiero) ─────────────────────────────
        self._setup_kpis()

        # ── Barra de filtros ──────────────────────────────────────────────────
        self._setup_filtros()

        # ── Cuerpo: tabla izquierda + panel derecho ───────────────────────────
        cuerpo = tk.Frame(self.window, bg=Colors.BACKGROUND)
        cuerpo.pack(fill="both", expand=True, padx=12, pady=(4, 0))

        self._setup_tabla(cuerpo)
        self._setup_panel_derecho(cuerpo)

        # ── Pie: botones de acción ────────────────────────────────────────────
        self._setup_pie()

    # ── KPIs ──────────────────────────────────────────────────────────────────

    def _setup_kpis(self):
        frame = tk.Frame(self.window, bg=Colors.BACKGROUND)
        frame.pack(fill="x", padx=12, pady=(10, 4))

        kpis = [
            ("total_pendiente", "💰 Total Pendiente",       Colors.WARNING),
            ("total_vencido",   "🔴 Total Vencido",         Colors.ERROR),
            ("total_semana",    "📅 Esta Semana",            Colors.PRIMARY),
            ("total_mes",       "📆 Próximos 30 Días",      "#6a1b9a"),
        ]

        self._kpi_labels = {}

        for i, (key, titulo, color) in enumerate(kpis):
            card = tk.Frame(frame, bg=Colors.SURFACE, relief="flat",
                            bd=1, highlightbackground=Colors.BORDER,
                            highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=4)

            tk.Label(card, text=titulo, font=FONT_KPI_TIT,
                     bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY
                     ).pack(anchor="w", padx=14, pady=(10, 0))

            lbl = tk.Label(card, text="$0", font=FONT_KPI_VAL,
                           bg=Colors.SURFACE, fg=color)
            lbl.pack(anchor="w", padx=14, pady=(0, 10))
            self._kpi_labels[key] = lbl

    # ── Filtros ───────────────────────────────────────────────────────────────

    def _setup_filtros(self):
        barra = tk.Frame(self.window, bg=Colors.SURFACE, relief="flat")
        barra.pack(fill="x", padx=12, pady=(4, 4))

        tk.Label(barra, text="Filtrar:", font=FONT_B,
                 bg=Colors.SURFACE).pack(side="left", padx=(10, 6))

        filtros = [
            ("Vence Hoy",    "hoy"),
            ("Esta Semana",  "semana"),
            ("Este Mes",     "mes"),
            ("Vencidas",     "vencidas"),
            ("Pendientes",   "pendientes"),
            ("Pagadas",      "pagadas"),
            ("Todas",        "todas"),
        ]

        self._btn_filtros = {}
        for label, key in filtros:
            btn = tk.Button(
                barra, text=label, font=FONT,
                bg=Colors.PRIMARY, fg="white",
                activebackground=Colors.PRIMARY_HOVER,
                relief="flat", padx=8, pady=3,
                command=lambda k=key: self._aplicar_filtro(k)
            )
            btn.pack(side="left", padx=2)
            self._btn_filtros[key] = btn

        # Separador
        tk.Label(barra, text="|", bg=Colors.SURFACE,
                 fg="#cccccc", font=("Segoe UI", 16)).pack(side="left", padx=6)

        # Rango personalizado
        tk.Label(barra, text="Desde:", font=FONT,
                 bg=Colors.SURFACE).pack(side="left", padx=(0, 3))
        self.entry_desde = tk.Entry(barra, width=11, font=FONT)
        self.entry_desde.pack(side="left")
        self.entry_desde.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(barra, text="Hasta:", font=FONT,
                 bg=Colors.SURFACE).pack(side="left", padx=(6, 3))
        self.entry_hasta = tk.Entry(barra, width=11, font=FONT)
        self.entry_hasta.pack(side="left")
        self.entry_hasta.insert(0, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))

        tk.Button(
            barra, text="🔍 Buscar", font=FONT_B,
            bg="#1976D2", fg="white", relief="flat", padx=8, pady=3,
            command=self._filtro_rango
        ).pack(side="left", padx=(6, 0))

    # ── Tabla de facturas ─────────────────────────────────────────────────────

    def _setup_tabla(self, parent):
        frame = tk.Frame(parent, bg=Colors.BACKGROUND)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Estilo
        style = ttk.Style()
        style.theme_use("default")
        style.configure("FC.Treeview.Heading",
                        background=HDR_BG, foreground="white",
                        font=("Segoe UI", 12, "bold"))
        style.map("FC.Treeview.Heading",
                  background=[("active", HDR_BG)])
        style.configure("FC.Treeview",
                        font=FONT, rowheight=30,
                        fieldbackground=Colors.SURFACE)
        style.map("FC.Treeview",
                  background=[("selected", Colors.PRIMARY)],
                  foreground=[("selected", "white")])

        cols = ("id_factura", "proveedor", "valor", "fecha_venc", "estado",
                "metodo", "observaciones")

        sb = ttk.Scrollbar(frame, orient="vertical")
        self.tree = ttk.Treeview(
            frame, columns=cols, show="headings",
            yscrollcommand=sb.set, style="FC.Treeview", height=22
        )
        sb.config(command=self.tree.yview)

        encabezados = {
            "id_factura":    ("ID Factura",     120, "w"),
            "proveedor":     ("Proveedor",      180, "w"),
            "valor":         ("Valor",          120, "e"),
            "fecha_venc":    ("Vencimiento",    110, "center"),
            "estado":        ("Estado",          90, "center"),
            "metodo":        ("Método Pago",    110, "center"),
            "observaciones": ("Observaciones",  200, "w"),
        }

        for col, (texto, ancho, anchor) in encabezados.items():
            self.tree.heading(col, text=texto,
                              command=lambda c=col: self._ordenar(c))
            self.tree.column(col, width=ancho, anchor=anchor)

        # Tags de color
        for tag, colors in TAG_COLORS.items():
            self.tree.tag_configure(tag, background=colors["bg"],
                                    foreground=colors["fg"])

        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # Bindings
        self.tree.bind("<Double-1>", self._doble_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar)

    # ── Panel derecho: Flujo de caja + Estadísticas proveedor ─────────────────

    def _setup_panel_derecho(self, parent):
        panel = tk.Frame(parent, bg=Colors.SURFACE, relief="flat",
                         bd=1, width=380)
        panel.pack(side="right", fill="y", padx=(0, 0))
        panel.pack_propagate(False)

        # ── Proyección de flujo de caja ───────────────────────────────────────
        tk.Label(panel, text="📊 Proyección Flujo de Caja",
                 font=FONT_H, bg=Colors.SURFACE,
                 fg=Colors.TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(12, 6))

        self._flujo_labels = {}
        for clave, texto, color in [
            ("7_dias",  "Próximos 7 días",  Colors.ERROR),
            ("15_dias", "Próximos 15 días", Colors.WARNING),
            ("30_dias", "Próximos 30 días", Colors.PRIMARY),
        ]:
            f = tk.Frame(panel, bg=Colors.SURFACE)
            f.pack(fill="x", padx=14, pady=2)
            tk.Label(f, text=texto, font=FONT,
                     bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY
                     ).pack(side="left")
            lbl = tk.Label(f, text="$0", font=FONT_B,
                           bg=Colors.SURFACE, fg=color)
            lbl.pack(side="right")
            self._flujo_labels[clave] = lbl

        tk.Frame(panel, height=1, bg=Colors.BORDER).pack(fill="x",
                                                          padx=14, pady=(10, 6))

        # ── Estadísticas por proveedor ────────────────────────────────────────
        tk.Label(panel, text="🏢 Top Proveedores (deuda activa)",
                 font=FONT_H, bg=Colors.SURFACE,
                 fg=Colors.TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(6, 4))

        cols_prov = ("Proveedor", "Deuda", "Facturas", "Promedio")
        style_p = ttk.Style()
        style_p.configure("PROV.Treeview",
                          font=("Segoe UI", 11), rowheight=26,
                          fieldbackground=Colors.SURFACE)
        style_p.configure("PROV.Treeview.Heading",
                          font=("Segoe UI", 11, "bold"),
                          background="#e3e6ea")

        wrap_prov = tk.Frame(panel, bg=Colors.SURFACE)
        wrap_prov.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.tree_prov = ttk.Treeview(
            wrap_prov, columns=cols_prov, show="headings",
            style="PROV.Treeview", height=6
        )
        sb_p = ttk.Scrollbar(wrap_prov, orient="vertical",
                              command=self.tree_prov.yview)
        self.tree_prov.configure(yscrollcommand=sb_p.set)

        anchos_prov = (130, 95, 65, 85)
        for col, w in zip(cols_prov, anchos_prov):
            self.tree_prov.heading(col, text=col)
            self.tree_prov.column(col, width=w,
                                  anchor="w" if col == "Proveedor" else "e")

        self.tree_prov.pack(side="left", fill="both", expand=True)
        sb_p.pack(side="right", fill="y")

        # ── Leyenda de colores ────────────────────────────────────────────────
        tk.Frame(panel, height=1, bg=Colors.BORDER).pack(fill="x",
                                                          padx=14, pady=(6, 4))
        tk.Label(panel, text="Leyenda:", font=FONT_B,
                 bg=Colors.SURFACE, fg=Colors.TEXT_PRIMARY
                 ).pack(anchor="w", padx=14, pady=(2, 2))

        leyenda_items = [
            ("🟢", "Más de 7 días", TAG_COLORS["ok"]["fg"]),
            ("🟡", "Vence en ≤ 3 días", TAG_COLORS["urgente"]["fg"]),
            ("🔴", "Vencida", TAG_COLORS["vencida"]["fg"]),
            ("🔵", "Pagada", TAG_COLORS["pagada"]["fg"]),
        ]
        for icono, texto, color in leyenda_items:
            f = tk.Frame(panel, bg=Colors.SURFACE)
            f.pack(fill="x", padx=18, pady=1)
            tk.Label(f, text=f"{icono}  {texto}", font=("Segoe UI", 11),
                     bg=Colors.SURFACE, fg=color).pack(side="left")

    # ── Pie con botones ───────────────────────────────────────────────────────

    def _setup_pie(self):
        pie = tk.Frame(self.window, bg=Colors.SURFACE, relief="flat")
        pie.pack(fill="x", side="bottom")

        # Contador
        self.lbl_contador = tk.Label(
            pie, text="0 facturas", font=FONT,
            bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY)
        self.lbl_contador.pack(side="left", padx=14, pady=8)

        btns = tk.Frame(pie, bg=Colors.SURFACE)
        btns.pack(side="right", padx=14, pady=8)

        botones = [
            ("➕ Agregar Factura",     "#107c10", self._agregar_factura),
            ("✅ Marcar Pagada",       "#0d47a1", self._marcar_pagada),
            ("🗑️ Eliminar Pagada",    "#b71c1c", self._eliminar_factura),
            ("🔄 Actualizar",          "#546e7a", self._refrescar),
        ]

        for texto, color, cmd in botones:
            tk.Button(
                btns, text=texto, font=FONT_B,
                bg=color, fg="white",
                activebackground=color, relief="flat",
                padx=12, pady=5, command=cmd
            ).pack(side="left", padx=4)

    # ══════════════════════════════════════════════════════════════════════════
    # DATOS
    # ══════════════════════════════════════════════════════════════════════════

    def _refrescar(self):
        """Refresca toda la vista: tabla, KPIs, flujo de caja, proveedores."""
        from controllers.facturas import FacturasController

        FacturasController.actualizar_estado_automatico()

        # Tabla
        self._facturas = FacturasController.obtener_todas(self._filtro_actual)
        self._poblar_tabla()

        # KPIs
        resumen = FacturasController.resumen_financiero()
        for key, lbl in self._kpi_labels.items():
            lbl.config(text=_fmt(resumen.get(key, 0)))

        # Flujo de caja
        flujo = FacturasController.proyeccion_flujo_caja()
        for key, lbl in self._flujo_labels.items():
            lbl.config(text=_fmt(flujo.get(key, 0)))

        # Proveedores
        self._poblar_proveedores()

        # Contador
        self.lbl_contador.config(text=f"{len(self._facturas)} factura(s)")

    def _poblar_tabla(self):
        """Llena el Treeview con las facturas actuales."""
        from controllers.facturas import FacturasController

        for item in self.tree.get_children():
            self.tree.delete(item)

        for f in self._facturas:
            clasificacion = FacturasController.clasificar_factura(
                f["fecha_vencimiento"], f["estado"]
            )

            # Formatear estado con emoji
            estado_display = {
                "pendiente": "⏳ Pendiente",
                "pagada":    "✅ Pagada",
                "vencida":   "❌ Vencida",
            }.get(f["estado"], f["estado"])

            self.tree.insert("", "end",
                iid=str(f["id"]),
                values=(
                    f["id_factura"],
                    f["proveedor"],
                    _fmt(f["valor"]),
                    f["fecha_vencimiento"],
                    estado_display,
                    f.get("metodo_pago", ""),
                    f.get("observaciones", "")[:50],
                ),
                tags=(clasificacion,)
            )

    def _poblar_proveedores(self):
        """Llena la tabla de estadísticas por proveedor."""
        from controllers.facturas import FacturasController

        for item in self.tree_prov.get_children():
            self.tree_prov.delete(item)

        stats = FacturasController.estadisticas_proveedores()
        for s in stats[:10]:  # Top 10
            self.tree_prov.insert("", "end", values=(
                s["proveedor"][:20],
                _fmt(s["deuda_activa"]),
                s["total_facturas"],
                _fmt(s["promedio_factura"]),
            ))

    # ══════════════════════════════════════════════════════════════════════════
    # FILTROS
    # ══════════════════════════════════════════════════════════════════════════

    def _aplicar_filtro(self, filtro: str):
        """Aplica un filtro rápido."""
        self._filtro_actual = filtro

        # Resaltar botón activo
        for key, btn in self._btn_filtros.items():
            if key == filtro:
                btn.config(bg="#0d47a1", relief="sunken")
            else:
                btn.config(bg=Colors.PRIMARY, relief="flat")

        from controllers.facturas import FacturasController
        self._facturas = FacturasController.obtener_todas(filtro)
        self._poblar_tabla()
        self.lbl_contador.config(text=f"{len(self._facturas)} factura(s)")

    def _filtro_rango(self):
        """Aplica filtro por rango de fechas."""
        desde = self.entry_desde.get().strip()
        hasta = self.entry_hasta.get().strip()

        if not desde or not hasta:
            messagebox.showwarning("Campos vacíos",
                                   "Ingresa ambas fechas para el rango.",
                                   parent=self.window)
            return

        from controllers.facturas import FacturasController
        self._filtro_actual = "rango"
        self._facturas = FacturasController.obtener_todas("rango", desde, hasta)
        self._poblar_tabla()
        self.lbl_contador.config(text=f"{len(self._facturas)} factura(s)")

        # Resetear botones
        for btn in self._btn_filtros.values():
            btn.config(bg=Colors.PRIMARY, relief="flat")

    # ══════════════════════════════════════════════════════════════════════════
    # ACCIONES CRUD
    # ══════════════════════════════════════════════════════════════════════════

    def _agregar_factura(self):
        """Abre ventana modal para agregar nueva factura."""
        dlg = tk.Toplevel(self.window)
        dlg.title("➕ Nueva Factura")
        dlg.geometry("520x580")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(bg=Colors.BACKGROUND)

        # Centrar
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - 260
        y = (dlg.winfo_screenheight() // 2) - 290
        dlg.geometry(f"520x580+{x}+{y}")

        # Cabecera
        hdr = tk.Frame(dlg, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="➕  Nueva Factura por Pagar",
                 font=("Segoe UI", 16, "bold"), bg=HDR_BG, fg="white"
                 ).pack(padx=16, pady=10)

        body = tk.Frame(dlg, bg=Colors.BACKGROUND)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        campos = [
            ("ID Factura:",           "id_factura",        "Ej: FAC-001234"),
            ("Proveedor:",            "proveedor",         "Nombre del proveedor"),
            ("Valor a Pagar ($):",    "valor",             "Ej: 1500000"),
            ("Fecha Vencimiento:",    "fecha_vencimiento", "YYYY-MM-DD"),
        ]

        entradas = {}
        for etiqueta, clave, placeholder in campos:
            tk.Label(body, text=etiqueta, font=FONT_B,
                     bg=Colors.BACKGROUND, fg=Colors.TEXT_PRIMARY
                     ).pack(anchor="w", pady=(8, 2))
            e = tk.Entry(body, font=("Segoe UI", 14), width=38)
            e.pack(fill="x", pady=(0, 2))
            e.insert(0, "")
            # Placeholder simulado
            e._placeholder = placeholder
            e.insert(0, placeholder)
            e.config(fg="#aaaaaa")
            e.bind("<FocusIn>", lambda ev, ent=e: self._clear_placeholder(ent))
            e.bind("<FocusOut>", lambda ev, ent=e: self._set_placeholder(ent))
            entradas[clave] = e

        # Método de pago
        tk.Label(body, text="Método de Pago:", font=FONT_B,
                 bg=Colors.BACKGROUND, fg=Colors.TEXT_PRIMARY
                 ).pack(anchor="w", pady=(8, 2))

        metodo_var = tk.StringVar(value="Transferencia")
        metodos_frame = tk.Frame(body, bg=Colors.BACKGROUND)
        metodos_frame.pack(fill="x", pady=(0, 2))

        for metodo in ["Transferencia", "Efectivo", "Cheque", "Débito automático"]:
            tk.Radiobutton(
                metodos_frame, text=metodo, variable=metodo_var,
                value=metodo, font=("Segoe UI", 11),
                bg=Colors.BACKGROUND, activebackground=Colors.BACKGROUND,
                selectcolor=Colors.SURFACE
            ).pack(side="left", padx=(0, 10))

        # Observaciones
        tk.Label(body, text="Observaciones:", font=FONT_B,
                 bg=Colors.BACKGROUND, fg=Colors.TEXT_PRIMARY
                 ).pack(anchor="w", pady=(8, 2))

        txt_obs = tk.Text(body, font=("Segoe UI", 12), height=3, width=38,
                          relief="solid", bd=1)
        txt_obs.pack(fill="x", pady=(0, 4))

        # Botón guardar
        def _guardar():
            datos = {}
            for clave, entry in entradas.items():
                val = entry.get().strip()
                if val == entry._placeholder:
                    val = ""
                datos[clave] = val

            # Validaciones
            if not datos["id_factura"]:
                messagebox.showerror("Error", "El ID de factura es obligatorio.",
                                     parent=dlg)
                return
            if not datos["proveedor"]:
                messagebox.showerror("Error", "El proveedor es obligatorio.",
                                     parent=dlg)
                return
            try:
                float(datos["valor"].replace(".", "").replace(",", ""))
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.",
                                     parent=dlg)
                return
            # Validar fecha
            try:
                datetime.strptime(datos["fecha_vencimiento"], "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Fecha inválida. Usa formato YYYY-MM-DD\nEj: 2026-03-15",
                    parent=dlg)
                return

            datos["valor"] = float(datos["valor"].replace(".", "").replace(",", ""))
            datos["metodo_pago"] = metodo_var.get()
            datos["observaciones"] = txt_obs.get("1.0", "end").strip()

            from controllers.facturas import FacturasController
            if FacturasController.agregar_factura(datos):
                dlg.destroy()
                self._refrescar()
                messagebox.showinfo("✅ Éxito", "Factura agregada correctamente.",
                                    parent=self.window)
            else:
                messagebox.showerror("Error", "No se pudo agregar la factura.",
                                     parent=dlg)

        tk.Button(
            body, text="💾  Guardar Factura", font=("Segoe UI", 14, "bold"),
            bg="#107c10", fg="white", activebackground="#0a5a0a",
            relief="flat", padx=16, pady=8, command=_guardar
        ).pack(fill="x", pady=(12, 0))

        # Foco
        entradas["id_factura"].focus()
        self._clear_placeholder(entradas["id_factura"])

    def _marcar_pagada(self):
        """Marca la factura seleccionada como pagada."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona una factura para marcar como pagada.",
                                   parent=self.window)
            return

        row_id = int(sel[0])

        # Verificar que no esté ya pagada
        factura = next((f for f in self._facturas if f["id"] == row_id), None)
        if factura and factura["estado"] == "pagada":
            messagebox.showinfo("Info", "Esta factura ya está marcada como pagada.",
                                parent=self.window)
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Marcar factura {factura['id_factura']} como PAGADA?\n\n"
            f"Proveedor: {factura['proveedor']}\n"
            f"Valor: {_fmt(factura['valor'])}",
            parent=self.window
        ):
            return

        from controllers.facturas import FacturasController
        if FacturasController.marcar_como_pagada(row_id):
            self._refrescar()
        else:
            messagebox.showerror("Error", "No se pudo actualizar la factura.",
                                 parent=self.window)

    def _eliminar_factura(self):
        """Elimina la factura seleccionada (solo pagadas)."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona una factura para eliminar.",
                                   parent=self.window)
            return

        row_id = int(sel[0])
        factura = next((f for f in self._facturas if f["id"] == row_id), None)

        if not factura:
            return

        if factura["estado"] != "pagada":
            messagebox.showwarning(
                "No permitido",
                "Solo se pueden eliminar facturas ya PAGADAS.\n\n"
                "Si desea eliminar una factura pendiente,\n"
                "primero márquela como pagada.",
                parent=self.window
            )
            return

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar factura {factura['id_factura']}?\n\n"
            f"Proveedor: {factura['proveedor']}\n"
            f"Valor: {_fmt(factura['valor'])}\n\n"
            "Esta acción no se puede deshacer.",
            parent=self.window
        ):
            return

        from controllers.facturas import FacturasController
        if FacturasController.eliminar_factura(row_id):
            self._refrescar()
            messagebox.showinfo("✅ Eliminada", "Factura eliminada correctamente.",
                                parent=self.window)
        else:
            messagebox.showerror("Error", "No se pudo eliminar la factura.",
                                 parent=self.window)

    # ══════════════════════════════════════════════════════════════════════════
    # EDICIÓN INLINE (doble clic)
    # ══════════════════════════════════════════════════════════════════════════

    def _doble_click(self, event):
        """Maneja doble clic: edición de fecha de vencimiento."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return

        # col = #1, #2, ... → index 0-based
        col_idx = int(col.replace("#", "")) - 1

        # Solo editar columna de fecha de vencimiento (índice 3)
        if col_idx != 3:
            return

        row_id = int(item)
        factura = next((f for f in self._facturas if f["id"] == row_id), None)
        if not factura or factura["estado"] == "pagada":
            return

        # Obtener posición de la celda
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return

        x, y, w, h = bbox

        # Crear Entry temporal sobre la celda
        entry = tk.Entry(self.tree, font=FONT, justify="center")
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, factura["fecha_vencimiento"])
        entry.select_range(0, "end")
        entry.focus()

        def _confirmar(event=None):
            nueva = entry.get().strip()
            entry.destroy()

            if nueva == factura["fecha_vencimiento"]:
                return

            # Validar formato
            try:
                datetime.strptime(nueva, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Formato inválido",
                    "Usa formato YYYY-MM-DD\nEjemplo: 2026-04-15",
                    parent=self.window
                )
                return

            from controllers.facturas import FacturasController
            if FacturasController.actualizar_fecha_vencimiento(row_id, nueva):
                self._refrescar()
            else:
                messagebox.showerror("Error",
                                     "No se pudo actualizar la fecha.",
                                     parent=self.window)

        def _cancelar(event=None):
            entry.destroy()

        entry.bind("<Return>", _confirmar)
        entry.bind("<Escape>", _cancelar)
        entry.bind("<FocusOut>", _confirmar)

    def _on_seleccionar(self, event=None):
        """Al seleccionar una factura, podría mostrar detalle (futuro)."""
        pass

    # ══════════════════════════════════════════════════════════════════════════
    # ORDENAMIENTO
    # ══════════════════════════════════════════════════════════════════════════

    _orden_cols = {}

    def _ordenar(self, col):
        """Ordena la tabla por columna."""
        datos = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        desc = self._orden_cols.get(col, False)
        self._orden_cols[col] = not desc

        # Intentar ordenar numéricamente
        try:
            datos.sort(
                key=lambda t: float(
                    t[0].replace("$", "").replace(".", "").replace(",", "")
                ) if t[0] else 0,
                reverse=desc
            )
        except ValueError:
            datos.sort(key=lambda t: str(t[0]).lower(), reverse=desc)

        for i, (_, k) in enumerate(datos):
            self.tree.move(k, "", i)

    # ══════════════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _clear_placeholder(entry):
        if entry.get() == entry._placeholder:
            entry.delete(0, "end")
            entry.config(fg="#1a1a1a")

    @staticmethod
    def _set_placeholder(entry):
        if not entry.get().strip():
            entry.insert(0, entry._placeholder)
            entry.config(fg="#aaaaaa")