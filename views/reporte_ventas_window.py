"""
Ventana de Reporte de Ventas - FarmaTrack
Droguería Irlandesa

Funcionalidades:
  - Filtro por rango de fechas (Hoy / Esta semana / Este mes / Personalizado)
  - Tabla de historial de ventas (ID, Fecha, Total, Cajero, N° Productos)
  - Panel de resumen: Total recaudado, N° ventas, Promedio por venta
  - Detalle de venta al seleccionar una fila (productos vendidos)
  - Exportar reporte PDF con resumen + detalle completo
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import logging
import os

try:
    import customtkinter as ctk
    from ctk_design_system import Colors, Fonts, Dimensions
    CTK_OK = True
except ImportError:
    CTK_OK = False
    class Colors:
        PRIMARY = "#0f6cbd"; PRIMARY_HOVER = "#0c5aa6"
        SURFACE = "#ffffff"; BACKGROUND = "#f4f6f8"
        TEXT_PRIMARY = "#1a1a1a"; TEXT_SECONDARY = "#616161"
        SUCCESS = "#107c10"; ERROR = "#d13438"
    class Fonts:
        FAMILY = "Segoe UI"
    class Dimensions:
        BUTTON_HEIGHT = 46; BUTTON_RADIUS = 8

from controllers.ventas import VentasController
from config.settings import COMPANY_NAME, COMPANY_NIT, COMPANY_BRANCH

try:
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white, black
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(valor) -> str:
    """Formatea número como pesos colombianos."""
    try:
        return f"${int(round(float(valor))):,}".replace(",", ".")
    except Exception:
        return str(valor)


def _fmt_fecha(fecha_str: str) -> str:
    """Convierte 'YYYY-MM-DD HH:MM:SS' → 'DD/MM/YYYY HH:MM'."""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return fecha_str


# ─────────────────────────────────────────────────────────────────────────────
# VENTANA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class ReporteVentasWindow:
    """Ventana de reporte y análisis de ventas"""

    # Colores internos
    _HDR_BG  = "#003B8E"
    _ROW_ALT = "#f0f6ff"
    _FONT    = ("Segoe UI", 13)
    _FONT_B  = ("Segoe UI", 13, "bold")
    _FONT_H  = ("Segoe UI", 15, "bold")

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.grab_set()
        self.window.title("📊 Reporte de Ventas – Droguería Irlandesa")
        self.window.state("zoomed")
        self.window.grab_set()
        self.window.configure(bg=Colors.BACKGROUND)

        # Estado
        self._ventas_actuales = []      # lista de dicts del controller
        self._venta_seleccionada = None

        self._setup_ui()
        self._aplicar_filtro_rapido("hoy")   # cargar al abrir

    # ─────────────────────────────────────────────────────────────────────────
    # INTERFAZ
    # ─────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # ── Cabecera ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self.window, bg=self._HDR_BG)
        hdr.pack(fill="x")

        tk.Label(hdr, text="📊  Reporte de Ventas",
                 font=("Segoe UI", 19, "bold"),
                 bg=self._HDR_BG, fg="white").pack(side="left", padx=20, pady=12)

        tk.Label(hdr, text=COMPANY_NAME,
                 font=("Segoe UI", 13),
                 bg=self._HDR_BG, fg="#a8c8f8").pack(side="right", padx=20)

        # ── Barra de filtros ─────────────────────────────────────────────────
        self._setup_filtros()

        # ── Cuerpo dividido: izquierda tabla | derecha detalle ───────────────
        cuerpo = tk.Frame(self.window, bg=Colors.BACKGROUND)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=(6, 0))

        self._setup_tabla(cuerpo)
        self._setup_panel_detalle(cuerpo)

        # ── Pie con resumen y botones ─────────────────────────────────────────
        self._setup_pie()

    # ── Filtros ───────────────────────────────────────────────────────────────

    def _setup_filtros(self):
        barra = tk.Frame(self.window, bg=Colors.SURFACE,
                         relief="flat", bd=0)
        barra.pack(fill="x", padx=14, pady=(8, 4))

        tk.Label(barra, text="Período:", font=self._FONT_B,
                 bg=Colors.SURFACE).pack(side="left", padx=(8, 4))

        # Botones rápidos
        periodos = [
            ("Hoy",        "hoy"),
            ("Esta semana","semana"),
            ("Este mes",   "mes"),
            ("Este año",   "anio"),
        ]
        self._btn_periodo = {}
        for label, key in periodos:
            btn = tk.Button(
                barra, text=label, font=self._FONT,
                bg=Colors.PRIMARY, fg="white",
                activebackground=Colors.PRIMARY_HOVER,
                relief="flat", padx=10, pady=4,
                command=lambda k=key: self._aplicar_filtro_rapido(k)
            )
            btn.pack(side="left", padx=3)
            self._btn_periodo[key] = btn

        # Separador visual
        tk.Label(barra, text="|", bg=Colors.SURFACE,
                 fg="#cccccc", font=("Segoe UI", 16)).pack(side="left", padx=8)

        # Rango personalizado
        tk.Label(barra, text="Desde:", font=self._FONT,
                 bg=Colors.SURFACE).pack(side="left", padx=(0, 3))

        self.entry_desde = tk.Entry(barra, width=11, font=self._FONT)
        self.entry_desde.pack(side="left")
        self.entry_desde.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(barra, text="Hasta:", font=self._FONT,
                 bg=Colors.SURFACE).pack(side="left", padx=(8, 3))

        self.entry_hasta = tk.Entry(barra, width=11, font=self._FONT)
        self.entry_hasta.pack(side="left")
        self.entry_hasta.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Button(
            barra, text="🔍 Buscar",
            font=self._FONT_B,
            bg="#1976D2", fg="white",
            activebackground="#1565C0",
            relief="flat", padx=10, pady=4,
            command=self._aplicar_filtro_personalizado
        ).pack(side="left", padx=(8, 0))

    # ── Tabla de historial ────────────────────────────────────────────────────

    def _setup_tabla(self, parent):
        frame = tk.Frame(parent, bg=Colors.BACKGROUND)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(frame, text="Historial de ventas",
                 font=self._FONT_H, bg=Colors.BACKGROUND,
                 fg=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(4, 6))

        # Treeview
        cols = ("id", "fecha", "total", "n_prod", "cajero")
        style = ttk.Style()
        style.theme_use("default")
        style.configure("RV.Treeview.Heading",
                        background=self._HDR_BG, foreground="white",
                        font=("Segoe UI", 13, "bold"))
        style.map("RV.Treeview.Heading",
                  background=[("active", self._HDR_BG)])
        style.configure("RV.Treeview",
                        font=self._FONT, rowheight=30,
                        fieldbackground=Colors.SURFACE)
        style.map("RV.Treeview",
                  background=[("selected", Colors.PRIMARY)],
                  foreground=[("selected", "white")])

        sb = ttk.Scrollbar(frame, orient="vertical")
        self.tree = ttk.Treeview(
            frame, columns=cols, show="headings",
            yscrollcommand=sb.set, style="RV.Treeview", height=20
        )
        sb.config(command=self.tree.yview)

        encabezados = {
            "id":     ("ID",          60,  "center"),
            "fecha":  ("Fecha",       160, "center"),
            "total":  ("Total",       130, "e"),
            "n_prod": ("Productos",   90,  "center"),
            "cajero": ("Cajero",      110, "center"),
        }
        for col, (texto, ancho, anchor) in encabezados.items():
            self.tree.heading(col, text=texto,
                              command=lambda c=col: self._ordenar(c))
            self.tree.column(col, width=ancho, anchor=anchor)

        self.tree.tag_configure("alt", background=self._ROW_ALT)

        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._mostrar_detalle)

    # ── Panel de detalle ──────────────────────────────────────────────────────

    def _setup_panel_detalle(self, parent):
        frame = tk.Frame(parent, bg=Colors.SURFACE,
                         relief="flat", bd=1, width=380)
        frame.pack(side="right", fill="y", padx=(0, 0))
        frame.pack_propagate(False)

        tk.Label(frame, text="Detalle de venta",
                 font=self._FONT_H, bg=Colors.SURFACE,
                 fg=Colors.TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(10, 6))

        # Info básica
        self.lbl_id     = tk.Label(frame, text="—", font=self._FONT,
                                    bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY)
        self.lbl_id.pack(anchor="w", padx=14)
        self.lbl_fecha  = tk.Label(frame, text="—", font=self._FONT,
                                    bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY)
        self.lbl_fecha.pack(anchor="w", padx=14)
        self.lbl_cajero = tk.Label(frame, text="—", font=self._FONT,
                                    bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY)
        self.lbl_cajero.pack(anchor="w", padx=14, pady=(0, 8))

        tk.Frame(frame, height=1, bg=Colors.PRIMARY).pack(fill="x",
                                                           padx=14, pady=(0, 8))

        # Tabla de productos de la venta seleccionada
        cols2 = ("descripcion", "cant", "precio", "subtotal")
        style2 = ttk.Style()
        style2.configure("DET.Treeview.Heading",
                         background="#1565C0", foreground="white",
                         font=("Segoe UI", 11, "bold"))
        style2.map("DET.Treeview.Heading",
                   background=[("active", "#1565C0")])
        style2.configure("DET.Treeview",
                         font=("Segoe UI", 11), rowheight=24)

        sb2 = ttk.Scrollbar(frame, orient="vertical")
        self.tree_det = ttk.Treeview(
            frame, columns=cols2, show="headings",
            yscrollcommand=sb2.set, style="DET.Treeview", height=14
        )
        sb2.config(command=self.tree_det.yview)

        self.tree_det.heading("descripcion", text="Producto", anchor="w")
        self.tree_det.heading("cant",        text="Cant",     anchor="center")
        self.tree_det.heading("precio",      text="Precio",   anchor="e")
        self.tree_det.heading("subtotal",    text="Subtotal", anchor="e")

        self.tree_det.column("descripcion", width=170, anchor="w")
        self.tree_det.column("cant",        width=45,  anchor="center")
        self.tree_det.column("precio",      width=78,  anchor="e")
        self.tree_det.column("subtotal",    width=80,  anchor="e")

        sb2.pack(side="right", fill="y", padx=(0, 2))
        self.tree_det.pack(fill="both", expand=True, padx=(14, 0), pady=(0, 8))

        # Total de la venta seleccionada
        self.lbl_total_det = tk.Label(frame, text="Total: —",
                                       font=("Segoe UI", 15, "bold"),
                                       bg=Colors.SURFACE, fg=Colors.PRIMARY)
        self.lbl_total_det.pack(anchor="e", padx=20, pady=(0, 12))

    # ── Pie ───────────────────────────────────────────────────────────────────

    def _setup_pie(self):
        pie = tk.Frame(self.window, bg=Colors.SURFACE, relief="groove", bd=1)
        pie.pack(fill="x", padx=14, pady=8)

        # Resumen estadístico
        res = tk.Frame(pie, bg=Colors.SURFACE)
        res.pack(side="left", padx=20, pady=8)

        self.lbl_n_ventas   = self._stat(res, "Ventas",    "0",    "#1565C0")
        self.lbl_total_per  = self._stat(res, "Total",     "$0",   Colors.SUCCESS)
        self.lbl_promedio   = self._stat(res, "Promedio",  "$0",   "#6a1b9a")
        self.lbl_ganancia   = self._stat(res, "Ganancia",  "$0",   "#e65100")
        self.lbl_utilidad   = self._stat(res, "Utilidad",  "0.0%", "#2e7d32")

        # Botones de acción
        botones = tk.Frame(pie, bg=Colors.SURFACE)
        botones.pack(side="right", padx=16, pady=8)

        tk.Button(
            botones, text="📄  Exportar PDF",
            font=self._FONT_B, bg=self._HDR_BG, fg="white",
            activebackground="#002a6e", relief="flat",
            padx=14, pady=6, command=self._exportar_pdf
        ).pack(side="left", padx=6)

        tk.Button(
            botones, text="🔄  Actualizar",
            font=self._FONT, bg="#546e7a", fg="white",
            activebackground="#37474f", relief="flat",
            padx=12, pady=6, command=self._refrescar
        ).pack(side="left", padx=6)

    def _stat(self, parent, titulo, valor, color):
        """Crea un widget de estadística con título y valor grande."""
        f = tk.Frame(parent, bg=Colors.SURFACE)
        f.pack(side="left", padx=20)
        tk.Label(f, text=titulo, font=("Segoe UI", 11),
                 bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY).pack()
        lbl = tk.Label(f, text=valor, font=("Segoe UI", 22, "bold"),
                       bg=Colors.SURFACE, fg=color)
        lbl.pack()
        return lbl

    # ─────────────────────────────────────────────────────────────────────────
    # LÓGICA DE FILTROS Y CARGA
    # ─────────────────────────────────────────────────────────────────────────

    def _aplicar_filtro_rapido(self, periodo: str):
        hoy = datetime.now().date()
        if periodo == "hoy":
            inicio = fin = hoy
        elif periodo == "semana":
            inicio = hoy - timedelta(days=hoy.weekday())
            fin    = hoy
        elif periodo == "mes":
            inicio = hoy.replace(day=1)
            fin    = hoy
        elif periodo == "anio":
            inicio = hoy.replace(month=1, day=1)
            fin    = hoy
        else:
            inicio = fin = hoy

        self._cargar(str(inicio), str(fin))

    def _aplicar_filtro_personalizado(self):
        desde = self.entry_desde.get().strip()
        hasta = self.entry_hasta.get().strip()
        try:
            datetime.strptime(desde, "%Y-%m-%d")
            datetime.strptime(hasta, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Fecha inválida",
                "Usa el formato YYYY-MM-DD\nEjemplo: 2026-02-18",
                parent=self.window
            )
            return
        self._cargar(desde, hasta)

    def _cargar(self, fecha_inicio: str, fecha_fin: str):
        """Consulta la BD, actualiza tabla y resumen."""
        # Guardar rango activo para el export
        self._fecha_inicio = fecha_inicio
        self._fecha_fin    = fecha_fin

        # Historial completo (hasta 2000 registros)
        todas = VentasController.obtener_historial_ventas(limite=2000)

        # Filtrar por rango en Python (el controller no filtra fechas directamente)
        def en_rango(v):
            try:
                fecha_v = v["fecha"][:10]   # 'YYYY-MM-DD'
                return fecha_inicio <= fecha_v <= fecha_fin
            except Exception:
                return False

        self._ventas_actuales = [v for v in todas if en_rango(v)]

        self._poblar_tabla()
        self._actualizar_resumen()
        self._limpiar_detalle()

    def _poblar_tabla(self):
        self.tree.delete(*self.tree.get_children())
        for i, v in enumerate(self._ventas_actuales):
            n_prod = len(v.get("productos", []))
            tag    = "alt" if i % 2 == 1 else ""
            self.tree.insert("", "end", iid=str(v["id"]),
                             values=(
                                 v["id"],
                                 _fmt_fecha(v["fecha"]),
                                 _fmt(v["total"]),
                                 n_prod,
                                 v.get("cajero", "Principal"),
                             ),
                             tags=(tag,))

    def _calcular_costo_venta(self, venta: dict) -> float:
        """Calcula el costo total de una venta consultando precio_compra en la BD."""
        import sqlite3
        from config.settings import DB_PATH
        costo = 0.0
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            for prod in venta.get("productos", []):
                codigo   = prod.get("codigo", "")
                cantidad = int(prod.get("cantidad", 0))
                cursor.execute(
                    "SELECT precio_compra FROM productos WHERE codigo_barras = ?",
                    (codigo,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    costo += float(row[0]) * cantidad
            conn.close()
        except Exception as e:
            logging.warning(f"No se pudo calcular costo de venta {venta.get('id')}: {e}")
        return costo

    def _actualizar_resumen(self):
        n      = len(self._ventas_actuales)
        total  = sum(v["total"] for v in self._ventas_actuales)
        prom   = total / n if n else 0

        costo_total = sum(self._calcular_costo_venta(v) for v in self._ventas_actuales)
        ganancia    = total - costo_total
        utilidad    = (ganancia / total * 100) if total > 0 else 0.0

        self.lbl_n_ventas.config(text=str(n))
        self.lbl_total_per.config(text=_fmt(total))
        self.lbl_promedio.config(text=_fmt(prom))
        self.lbl_ganancia.config(text=_fmt(ganancia))
        self.lbl_utilidad.config(text=f"{utilidad:.1f}%")

    def _limpiar_detalle(self):
        self.lbl_id.config(text="—")
        self.lbl_fecha.config(text="—")
        self.lbl_cajero.config(text="—")
        self.lbl_total_det.config(text="Total: —")
        self.tree_det.delete(*self.tree_det.get_children())
        self._venta_seleccionada = None

    def _refrescar(self):
        self._cargar(self._fecha_inicio, self._fecha_fin)

    # ─────────────────────────────────────────────────────────────────────────
    # DETALLE DE VENTA
    # ─────────────────────────────────────────────────────────────────────────

    def _mostrar_detalle(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return

        venta_id = int(sel[0])
        # Buscar en lista local (evita otra consulta)
        venta = next((v for v in self._ventas_actuales if v["id"] == venta_id), None)
        if not venta:
            return

        self._venta_seleccionada = venta

        self.lbl_id.config(text=f"Venta N° {venta['id']}")
        self.lbl_fecha.config(text=_fmt_fecha(venta["fecha"]))
        self.lbl_cajero.config(text=f"Cajero: {venta.get('cajero','Principal')}")
        self.lbl_total_det.config(text=f"Total: {_fmt(venta['total'])}")

        self.tree_det.delete(*self.tree_det.get_children())
        for prod in venta.get("productos", []):
            self.tree_det.insert("", "end", values=(
                str(prod.get("descripcion", ""))[:30],
                prod.get("cantidad", 0),
                _fmt(prod.get("precio_unitario", 0)),
                _fmt(prod.get("subtotal", 0)),
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # ORDENAR COLUMNAS
    # ─────────────────────────────────────────────────────────────────────────

    _orden_col = {}

    def _ordenar(self, col):
        datos = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        if col in ("total",):
            try:
                datos = [(float(v.replace("$","").replace(".","").replace(",",".")), k)
                         for v, k in datos]
            except Exception:
                pass
        elif col in ("id", "n_prod"):
            try:
                datos = [(int(v), k) for v, k in datos]
            except Exception:
                pass

        self._orden_col[col] = not self._orden_col.get(col, False)
        datos.sort(reverse=self._orden_col[col])
        for idx, (_, kid) in enumerate(datos):
            self.tree.move(kid, "", idx)
            self.tree.item(kid, tags=("alt" if idx % 2 else "",))

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORTAR PDF
    # ─────────────────────────────────────────────────────────────────────────

    def _exportar_pdf(self):
        if not REPORTLAB_OK:
            messagebox.showerror(
                "Módulo faltante",
                "Instala reportlab:\n  pip install reportlab",
                parent=self.window
            )
            return

        if not self._ventas_actuales:
            messagebox.showwarning(
                "Sin datos",
                "No hay ventas en el período seleccionado.",
                parent=self.window
            )
            return

        # Nombre del archivo con fechas
        nombre = (f"Reporte_Ventas_"
                  f"{self._fecha_inicio}_al_{self._fecha_fin}.pdf")
        ruta   = nombre.replace(" ", "_")

        try:
            self._construir_pdf(ruta)
            messagebox.showinfo(
                "✅ PDF generado",
                f"Reporte guardado como:\n{ruta}",
                parent=self.window
            )
            if os.name == "nt":
                os.startfile(ruta)
            else:
                os.system(f"xdg-open '{ruta}'")
        except Exception as exc:
            logging.error(f"Error generando PDF reporte: {exc}")
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{exc}",
                                 parent=self.window)

    def _construir_pdf(self, ruta: str):
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.units import cm

        AZUL  = HexColor("#003B8E")
        AZUL2 = HexColor("#1565C0")
        GRIS  = HexColor("#f4f6f8")
        VERDE = HexColor("#107c10")

        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=1.8*cm, rightMargin=1.8*cm,
            topMargin=1.5*cm,  bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()

        s_title  = ParagraphStyle("T",  fontSize=22, textColor=AZUL,
                                   leading=28, spaceAfter=4)
        s_sub    = ParagraphStyle("S",  fontSize=12, textColor=HexColor("#555555"),
                                   spaceAfter=14)
        s_sec    = ParagraphStyle("SE", fontSize=14, textColor=AZUL2,
                                   leading=20, spaceAfter=6, spaceBefore=10)
        s_body   = ParagraphStyle("B",  fontSize=10, leading=14,
                                   textColor=HexColor("#333333"))
        s_total  = ParagraphStyle("TO", fontSize=13, textColor=VERDE,
                                   leading=18, spaceAfter=4)

        story = []

        # ── Encabezado ─────────────────────────────────────────────────────
        story.append(Paragraph(f"Reporte de Ventas", s_title))
        story.append(Paragraph(
            f"{COMPANY_NAME}  •  NIT {COMPANY_NIT}  •  {COMPANY_BRANCH}",
            s_sub
        ))
        story.append(Paragraph(
            f"Período: {self._fecha_inicio} al {self._fecha_fin}  |  "
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            s_body
        ))
        story.append(HRFlowable(width="100%", thickness=2,
                                color=AZUL, spaceAfter=10))

        # ── Resumen ────────────────────────────────────────────────────────
        n     = len(self._ventas_actuales)
        total = sum(v["total"] for v in self._ventas_actuales)
        prom  = total / n if n else 0

        story.append(Paragraph("Resumen del período", s_sec))

        datos_res = [
            ["Número de ventas", str(n)],
            ["Total recaudado",  _fmt(total)],
            ["Promedio por venta", _fmt(prom)],
        ]
        tbl_res = Table(datos_res, colWidths=[10*cm, 6*cm])
        tbl_res.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), GRIS),
            ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 11),
            ("TEXTCOLOR",   (1, 0), (1, -1), VERDE),
            ("FONTNAME",    (1, 0), (1, -1), "Helvetica-Bold"),
            ("ALIGN",       (1, 0), (1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [GRIS, white]),
            ("GRID",        (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
            ("TOPPADDING",  (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(tbl_res)
        story.append(Spacer(1, 16))

        # ── Tabla de ventas ───────────────────────────────────────────────
        story.append(Paragraph("Detalle de ventas", s_sec))

        cabecera = [["ID", "Fecha", "Total", "Productos", "Cajero"]]
        filas    = cabecera + [
            [str(v["id"]),
             _fmt_fecha(v["fecha"]),
             _fmt(v["total"]),
             str(len(v.get("productos", []))),
             v.get("cajero", "Principal")]
            for v in self._ventas_actuales
        ]

        ancho_cols = [1.5*cm, 5*cm, 3.5*cm, 2.5*cm, 3.5*cm]
        tbl = Table(filas, colWidths=ancho_cols, repeatRows=1)
        tbl.setStyle(TableStyle([
            # Cabecera
            ("BACKGROUND",   (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR",    (0, 0), (-1, 0), white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 10),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            # Filas
            ("FONTSIZE",     (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, GRIS]),
            ("ALIGN",        (2, 1), (3, -1), "RIGHT"),
            ("ALIGN",        (0, 1), (1, -1), "CENTER"),
            ("ALIGN",        (4, 1), (4, -1), "CENTER"),
            ("GRID",         (0, 0), (-1, -1), 0.3, HexColor("#bbbbbb")),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))

        # ── Pie ────────────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1,
                                color=HexColor("#cccccc"), spaceAfter=6))
        story.append(Paragraph(
            f"FarmaTrack – {COMPANY_NAME}  |  Documento generado automáticamente",
            ParagraphStyle("pie", fontSize=8, textColor=HexColor("#888888"),
                           alignment=1)
        ))

        doc.build(story)