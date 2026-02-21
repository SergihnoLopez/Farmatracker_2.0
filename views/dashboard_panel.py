"""
Dashboard Operativo - FarmaTrack
Ventas del día · Stock bajo · Vencimientos · Valor inventario
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime

try:
    from ctk_design_system import Colors, Fonts, Dimensions
except ImportError:
    class Colors:
        PRIMARY="#0f6cbd"; PRIMARY_HOVER="#0c5aa6"; SURFACE="#ffffff"
        BACKGROUND="#f4f6f8"; TEXT_PRIMARY="#1a1a1a"; TEXT_SECONDARY="#616161"
        SUCCESS="#107c10"; ERROR="#d13438"; WARNING="#f7630c"; BORDER="#e3e6ea"
    class Fonts:
        FAMILY="Segoe UI"; BODY=("Segoe UI",13)
    class Dimensions:
        BUTTON_HEIGHT=46; BUTTON_RADIUS=8


def _fmt(v):
    try: return f"${int(round(float(v))):,}".replace(",",".")
    except: return str(v)


# ==============================================================================
# MINI GRÁFICO DE BARRAS (Canvas puro — sin matplotlib)
# ==============================================================================

class MiniBarChart(tk.Canvas):
    def __init__(self, parent, data=None, **kw):
        super().__init__(parent, bg=Colors.SURFACE, highlightthickness=0, **kw)
        self._data = data or []
        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, data):
        self._data = data; self._draw()

    def _draw(self):
        self.delete("all")
        if not self._data: return
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: return
        PL, PR, PT, PB = 10, 10, 10, 28
        n  = len(self._data)
        mx = max((d["total"] for d in self._data), default=1) or 1
        bw = (w - PL - PR) / n
        ch = h - PT - PB
        for i, d in enumerate(self._data):
            x0 = PL + i*bw + bw*0.1
            x1 = PL + (i+1)*bw - bw*0.1
            bh = max(2, d["total"]/mx * ch)
            y0, y1 = h - PB - bh, h - PB
            color = Colors.SUCCESS if i == n-1 else Colors.PRIMARY
            self.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            self.create_text((x0+x1)/2, h-PB+10, text=d["dia"],
                             fill=Colors.TEXT_SECONDARY,
                             font=("Segoe UI",9), anchor="n")


# ==============================================================================
# KPI CARD
# ==============================================================================

class KpiCard(ctk.CTkFrame):
    def __init__(self, parent, titulo, valor, subtitulo="", color_valor=None, **kw):
        super().__init__(parent, fg_color=Colors.SURFACE, corner_radius=12,
                         border_width=1, border_color=Colors.BORDER, **kw)
        color_valor = color_valor or Colors.PRIMARY
        ctk.CTkLabel(self, text=titulo, font=(Fonts.FAMILY,12),
                     text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(anchor="w", padx=18, pady=(14,2))
        self.lbl_valor = ctk.CTkLabel(self, text=valor,
                                       font=(Fonts.FAMILY,26,"bold"),
                                       text_color=color_valor)
        self.lbl_valor.pack(anchor="w", padx=18)
        self._lbl_sub = ctk.CTkLabel(self, text=subtitulo,
                                      font=(Fonts.FAMILY,11),
                                      text_color=Colors.TEXT_SECONDARY)
        self._lbl_sub.pack(anchor="w", padx=18, pady=(2,12))

    def update_valor(self, valor, color=None, subtitulo=None):
        self.lbl_valor.configure(text=valor)
        if color:    self.lbl_valor.configure(text_color=color)
        if subtitulo: self._lbl_sub.configure(text=subtitulo)


# ==============================================================================
# DASHBOARD PANEL
# ==============================================================================

class DashboardPanel(ctk.CTkFrame):
    REFRESH_MS = 60_000

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=Colors.BACKGROUND, corner_radius=0, **kw)
        self._after_id = None
        self._datos    = {}
        self._setup_ui()
        self._cargar_datos()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Encabezado
        hdr = ctk.CTkFrame(self, fg_color=Colors.PRIMARY, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="📊  Dashboard Operativo",
                     font=(Fonts.FAMILY,19,"bold"), text_color="white"
        ).pack(side="left", padx=20, pady=12)
        self.lbl_hora = ctk.CTkLabel(hdr, text="",
                                      font=(Fonts.FAMILY,12), text_color="#a8c8f8")
        self.lbl_hora.pack(side="right", padx=20)
        self._tick_hora()

        # Área scrollable
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=Colors.BACKGROUND, corner_radius=0)
        self.scroll.pack(fill="both", expand=True)
        self.scroll.grid_columnconfigure((0,1,2,3), weight=1)

        # ── Fila 0: KPI Cards ─────────────────────────────────────────────────
        self.card_ventas = KpiCard(
            self.scroll, "💰 Ventas del Día", "$0",
            subtitulo="0 transacciones hoy", color_valor=Colors.SUCCESS)
        self.card_ventas.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.card_stock = KpiCard(
            self.scroll, "⚠️ Stock Bajo", "0",
            subtitulo="Umbral ≤ 5 unidades", color_valor=Colors.WARNING)
        self.card_stock.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.card_venc = KpiCard(
            self.scroll, "📅 Próximos a Vencer", "0",
            subtitulo="Próximos 30 días", color_valor=Colors.ERROR)
        self.card_venc.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        self.card_inv = KpiCard(
            self.scroll, "📦 Valor Inventario", "$0",
            subtitulo="precio de compra", color_valor=Colors.PRIMARY)
        self.card_inv.grid(row=0, column=3, padx=8, pady=8, sticky="nsew")

        # ── Fila 1: Gráfico semana + Tabla stock bajo ─────────────────────────
        frame_sem = ctk.CTkFrame(self.scroll, fg_color=Colors.SURFACE,
                                  corner_radius=12, border_width=1,
                                  border_color=Colors.BORDER)
        frame_sem.grid(row=1, column=0, columnspan=2,
                       padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(frame_sem, text="Ventas últimos 7 días",
                     font=(Fonts.FAMILY,13,"bold"),
                     text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=16, pady=(12,4))
        self.chart = MiniBarChart(frame_sem, height=140)
        self.chart.pack(fill="both", expand=True, padx=12, pady=(0,12))

        frame_stock = ctk.CTkFrame(self.scroll, fg_color=Colors.SURFACE,
                                    corner_radius=12, border_width=1,
                                    border_color=Colors.BORDER)
        frame_stock.grid(row=1, column=2, columnspan=2,
                         padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(frame_stock, text="⚠️  Productos con Stock Bajo",
                     font=(Fonts.FAMILY,13,"bold"), text_color=Colors.WARNING
        ).pack(anchor="w", padx=16, pady=(12,4))
        self.tree_stock = self._make_tree(
            frame_stock,
            cols=("Descripción", "Cant.", "Proveedor"),
            widths=(220, 55, 140),
        )

        # ── Fila 2: Tabla vencimientos ────────────────────────────────────────
        frame_venc = ctk.CTkFrame(self.scroll, fg_color=Colors.SURFACE,
                                   corner_radius=12, border_width=1,
                                   border_color=Colors.BORDER)
        frame_venc.grid(row=2, column=0, columnspan=4,
                        padx=8, pady=8, sticky="nsew")

        hv = ctk.CTkFrame(frame_venc, fg_color="transparent")
        hv.pack(fill="x", padx=16, pady=(12,4))
        ctk.CTkLabel(hv, text="📅  Alertas de Vencimiento",
                     font=(Fonts.FAMILY,13,"bold"), text_color=Colors.ERROR
        ).pack(side="left")
        self.lbl_venc_ok = ctk.CTkLabel(hv, text="",
                                         font=(Fonts.FAMILY,12),
                                         text_color=Colors.SUCCESS)
        self.lbl_venc_ok.pack(side="right")

        self.tree_venc = self._make_tree(
            frame_venc,
            cols=("Descripción","Vencimiento","Días Rest.","Estado","Cant.","Proveedor"),
            widths=(260, 110, 110, 95, 60, 150),
        )
        self.tree_venc.tag_configure("vencido", background="#fde8e8", foreground="#b91c1c")
        self.tree_venc.tag_configure("critico",  background="#fff3cd", foreground="#92400e")
        self.tree_venc.tag_configure("proximo",  background="#ecfdf5", foreground="#065f46")

        # ── Footer ────────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=Colors.SURFACE, corner_radius=0,
                               border_width=1, border_color=Colors.BORDER)
        footer.pack(fill="x", side="bottom")
        self.lbl_act = ctk.CTkLabel(
            footer, text="Última actualización: —",
            font=(Fonts.FAMILY,11), text_color=Colors.TEXT_SECONDARY)
        self.lbl_act.pack(side="left", padx=14, pady=6)
        ctk.CTkButton(
            footer, text="🔄 Actualizar",
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            height=30, corner_radius=6, font=(Fonts.FAMILY,12),
            command=self._cargar_datos,
        ).pack(side="right", padx=14, pady=6)

    def _make_tree(self, parent, cols, widths, height=6):
        """Crea un Treeview estilizado dentro de parent."""
        style = ttk.Style()
        style.configure("Dash.Treeview",
                        font=("Segoe UI",11), rowheight=24,
                        background=Colors.SURFACE,
                        fieldbackground=Colors.SURFACE,
                        borderwidth=0)
        style.configure("Dash.Treeview.Heading",
                        font=("Segoe UI",11,"bold"),
                        background=Colors.BACKGROUND, borderwidth=0)
        wrap = tk.Frame(parent, bg=Colors.SURFACE)
        wrap.pack(fill="both", expand=True, padx=10, pady=(0,10))
        tree = ttk.Treeview(wrap, columns=cols, show="headings",
                             style="Dash.Treeview", height=height)
        vsb  = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w" if w > 70 else "center")
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tree

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _cargar_datos(self):
        try:
            from controllers.dashboard import DashboardController
            self._datos = DashboardController.resumen_completo()
            self._poblar_ui()
            self.lbl_act.configure(
                text=f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
        except Exception as e:
            logging.error(f"Error cargando dashboard: {e}")

        if self._after_id:
            try: self.after_cancel(self._after_id)
            except Exception: pass
        self._after_id = self.after(self.REFRESH_MS, self._cargar_datos)

    def _poblar_ui(self):
        d = self._datos

        # KPIs
        vd = d.get("ventas_hoy", {})
        self.card_ventas.update_valor(
            _fmt(vd.get("total", 0)),
            color=Colors.SUCCESS if vd.get("total", 0) > 0 else Colors.TEXT_SECONDARY,
            subtitulo=f"{vd.get('cantidad', 0)} transacciones hoy",
        )

        sb = d.get("stock_bajo", [])
        self.card_stock.update_valor(
            str(len(sb)),
            color=Colors.ERROR if len(sb)>10
                  else Colors.WARNING if sb
                  else Colors.SUCCESS,
        )

        pv = d.get("por_vencer", [])
        vencidos = [x for x in pv if x.get("estado") == "vencido"]
        self.card_venc.update_valor(
            str(len(pv)),
            color=Colors.ERROR if vencidos
                  else Colors.WARNING if pv
                  else Colors.SUCCESS,
        )

        inv = d.get("inventario", {})
        self.card_inv.update_valor(_fmt(inv.get("valor_costo", 0)))

        # Gráfico semanal
        self.chart.update_data(d.get("ventas_semana", []))

        # Tabla stock bajo
        for i in self.tree_stock.get_children():
            self.tree_stock.delete(i)
        for p in sb:
            self.tree_stock.insert("", "end", values=(
                p.get("descripcion","")[:35],
                p.get("cantidad", 0),
                p.get("proveedor","—")[:20],
            ))

        # Tabla vencimientos
        for i in self.tree_venc.get_children():
            self.tree_venc.delete(i)
        if not pv:
            self.lbl_venc_ok.configure(
                text="✅ Sin alertas de vencimiento en los próximos 30 días")
        else:
            self.lbl_venc_ok.configure(text="")
            for p in pv:
                dias  = p.get("dias_restantes")
                estado = p.get("estado","")
                if dias is None:
                    dias_txt = "—"
                elif dias < 0:
                    dias_txt = f"Hace {abs(dias)}d"
                elif dias == 0:
                    dias_txt = "HOY"
                else:
                    dias_txt = f"{dias} días"
                estado_txt = {
                    "vencido": "🔴 VENCIDO",
                    "critico": "🟠 CRÍTICO",
                    "proximo": "🟡 Próximo",
                }.get(estado, "—")
                self.tree_venc.insert("", "end", tags=(estado,), values=(
                    p.get("descripcion","")[:38],
                    p.get("fecha_vencimiento","—"),
                    dias_txt,
                    estado_txt,
                    p.get("cantidad", 0),
                    p.get("proveedor","—")[:20],
                ))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tick_hora(self):
        self.lbl_hora.configure(
            text=datetime.now().strftime("%A %d/%m/%Y  %H:%M:%S").capitalize()
        )
        self.after(1000, self._tick_hora)

    def destruir(self):
        """Llamar antes de destruir para cancelar timers."""
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except Exception: pass
            self._after_id = None