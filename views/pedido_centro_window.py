"""
Ventana de Pedido Centro
Droguería Irlandesa - FarmaTrack
Basada en main.py adjunto, integrada a la arquitectura del proyecto.

Funcionalidad:
  - Carga productos desde "Compra activa.xlsx"
  - Edición de cantidades y precios con doble clic
  - Cálculo automático de subtotales y total
  - Exporta PDF del pedido sin precios (con QR)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import datetime
import os

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.colors import HexColor, black
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.barcode import qr
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

try:
    from ctk_design_system import Colors, Fonts
except ImportError:
    class Colors:
        PRIMARY    = "#0f6cbd"
        BACKGROUND = "#f4f6f8"
        SURFACE    = "#ffffff"
        TEXT_PRIMARY   = "#1a1a1a"
        TEXT_SECONDARY = "#616161"
    class Fonts:
        FAMILY = "Segoe UI"

# ── Intentar registrar fuente Anton si existe ─────────────────────────────────
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    _anton = next(
        (p for p in ["Anton-Regular.ttf",
                     os.path.join(os.path.dirname(__file__), "..", "Anton-Regular.ttf")]
         if os.path.exists(p)),
        None
    )
    if _anton:
        pdfmetrics.registerFont(TTFont("Anton", _anton))
except Exception:
    pass

# ── Estilos internos ──────────────────────────────────────────────────────────
_FUENTE_TABLA  = ("Arial", 14)
_FUENTE_GRANDE = ("Arial", 16)
_AZUL_HEADER   = "#003B8E"
_AZUL_BTN_PDF  = "#004AAD"


class PedidoCentroWindow:
    """Ventana de gestión de pedidos al centro de distribución"""

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.grab_set()
        self.window.title("🏬  Pedido Centro – Droguería Irlandesa")
        self.window.state("zoomed")
        self.window.configure(bg=Colors.BACKGROUND)

        self._setup_ui()
        self._cargar_productos()

    # ──────────────────────────────────────────────────────────────────────────
    # INTERFAZ
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # ── Barra de título ──────────────────────────────────────────────────
        barra = tk.Frame(self.window, bg=_AZUL_HEADER)
        barra.pack(fill="x")

        tk.Label(
            barra,
            text="🏬  Pedido Centro  –  Droguería Irlandesa",
            font=("Arial", 17, "bold"),
            bg=_AZUL_HEADER,
            fg="white"
        ).pack(pady=10, padx=18, anchor="w")

        # ── Tabla ────────────────────────────────────────────────────────────
        frame_tabla = tk.Frame(self.window)
        frame_tabla.pack(fill=tk.BOTH, expand=True)

        columnas = ("ARTICULO", "PRECIO", "CANTIDAD", "SUBTOTAL")

        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "PC.Treeview.Heading",
            background=_AZUL_HEADER,
            foreground="white",
            font=("Arial", 15, "bold")
        )
        style.map("PC.Treeview.Heading",
                  background=[("active", _AZUL_HEADER)])
        style.configure("PC.Treeview",
                        font=_FUENTE_TABLA, rowheight=33)

        style.configure(
            "PC.Vertical.TScrollbar",
            gripcount=0,
            background=_AZUL_HEADER,
            darkcolor=_AZUL_HEADER,
            lightcolor=_AZUL_HEADER,
            troughcolor="#E0E0E0",
            bordercolor=_AZUL_HEADER,
            arrowcolor=_AZUL_HEADER,
            thickness=60
        )
        style.map("PC.Vertical.TScrollbar",
                  background=[("active", "#0055CC")])

        sb = ttk.Scrollbar(frame_tabla, orient="vertical",
                           style="PC.Vertical.TScrollbar")

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            yscrollcommand=sb.set,
            style="PC.Treeview",
            height=18
        )
        sb.config(command=self.tree.yview)

        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # Encabezados
        _orden = {}

        def sort_col(col):
            datos = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
            try:
                datos = [(float(v), k) for v, k in datos]
            except Exception:
                pass
            _orden[col] = not _orden.get(col, False)
            datos.sort(reverse=_orden[col])
            for i, (_, kid) in enumerate(datos):
                self.tree.move(kid, "", i)

        for col in columnas:
            if col == "ARTICULO":
                self.tree.heading(col, text=col, anchor="w",
                                  command=lambda c=col: sort_col(c))
                self.tree.column(col, width=430, anchor="w")
            else:
                self.tree.heading(col, text=col, anchor="center",
                                  command=lambda c=col: sort_col(c))
                self.tree.column(col, width=175, anchor="center")

        self.tree.bind("<Double-1>", self._editar_celda)

        # ── Total ────────────────────────────────────────────────────────────
        self.total_var = tk.StringVar(value="TOTAL: $0")
        tk.Label(
            self.window,
            textvariable=self.total_var,
            font=("Arial", 20, "bold"),
            bg="#E8E8E8",
            anchor="e",
            padx=20
        ).pack(fill="x", pady=4)

        # ── Botones ───────────────────────────────────────────────────────────
        frame_btns = tk.Frame(self.window, bg=Colors.BACKGROUND)
        frame_btns.pack(pady=6)

        tk.Button(
            frame_btns,
            text="📄  Exportar PDF (sin precios)",
            font=("Arial", 15, "bold"),
            bg=_AZUL_BTN_PDF, fg="white",
            height=1, padx=16,
            command=self._exportar_pdf
        ).pack(side="left", padx=8)

        tk.Button(
            frame_btns,
            text="🔄  Recargar Excel",
            font=("Arial", 13),
            bg="#4CAF50", fg="white",
            height=1, padx=10,
            command=self._cargar_productos
        ).pack(side="left", padx=8)

        tk.Button(
            frame_btns,
            text="🗑️  Limpiar Cantidades",
            font=("Arial", 13),
            bg="#f44336", fg="white",
            height=1, padx=10,
            command=self._limpiar_cantidades
        ).pack(side="left", padx=8)

    # ──────────────────────────────────────────────────────────────────────────
    # DATOS
    # ──────────────────────────────────────────────────────────────────────────

    def _cargar_productos(self):
        """Carga / recarga productos desde Compra activa.xlsx"""
        if not PANDAS_OK:
            messagebox.showerror(
                "Módulo faltante",
                "Instala pandas:\n  pip install pandas openpyxl",
                parent=self.window
            )
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        # Buscar Excel en varias ubicaciones
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidatos = [
            "Compra activa.xlsx",
            os.path.join(_base, "Compra activa.xlsx"),
        ]
        ruta = next((r for r in candidatos if os.path.exists(r)), None)

        if not ruta:
            messagebox.showwarning(
                "Archivo no encontrado",
                "Coloca 'Compra activa.xlsx' en la carpeta del proyecto.",
                parent=self.window
            )
            return

        try:
            df = pd.read_excel(ruta)[["ARTICULO", "PRECIO"]]
            for _, row in df.iterrows():
                try:
                    precio_fmt = f"${row['PRECIO']:,.0f}".replace(",", ".")
                except Exception:
                    precio_fmt = str(row["PRECIO"])
                self.tree.insert("", tk.END,
                                 values=(row["ARTICULO"], precio_fmt, "0", "0"))
            self._actualizar_total()
            logging.info(f"Pedido Centro: {len(df)} productos cargados.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel:\n{exc}",
                                 parent=self.window)

    def _limpiar_cantidades(self):
        for item in self.tree.get_children():
            self.tree.set(item, "CANTIDAD", "0")
            self.tree.set(item, "SUBTOTAL", "0")
        self._actualizar_total()

    # ──────────────────────────────────────────────────────────────────────────
    # EDICIÓN INLINE
    # ──────────────────────────────────────────────────────────────────────────

    def _editar_celda(self, event):
        region  = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        columna = self.tree.identify_column(event.x)
        fila    = self.tree.identify_row(event.y)
        if columna not in ("#2", "#3"):   # PRECIO=#2, CANTIDAD=#3
            return

        bbox = self.tree.bbox(fila, columna)
        if not bbox:
            return
        x, y, ancho, alto = bbox

        valor = self.tree.set(fila, columna)
        entry = tk.Entry(self.window, font=_FUENTE_GRANDE)
        entry.place(x=x, y=y + 120, width=ancho, height=alto)
        entry.insert(0, valor)
        entry.focus()
        entry.select_range(0, tk.END)

        def guardar(ev=None):
            self.tree.set(fila, columna, entry.get())
            entry.destroy()
            self._recalcular_fila(fila)

        entry.bind("<Return>",   guardar)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def _recalcular_fila(self, item_id):
        try:
            precio   = self._num(self.tree.set(item_id, "PRECIO"))
            cantidad = int(self.tree.set(item_id, "CANTIDAD"))
            subtotal = precio * cantidad
            self.tree.set(item_id, "SUBTOTAL",
                          f"${subtotal:,.0f}".replace(",", "."))
        except Exception:
            self.tree.set(item_id, "SUBTOTAL", "0")
        self._actualizar_total()

    def _actualizar_total(self):
        total = sum(self._num(self.tree.set(i, "SUBTOTAL"))
                    for i in self.tree.get_children())
        self.total_var.set(f"TOTAL: ${total:,.0f}".replace(",", "."))

    @staticmethod
    def _num(valor: str) -> float:
        try:
            return float(str(valor).replace("$", "").replace(".", "").replace(",", ".") or 0)
        except Exception:
            return 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # EXPORTAR PDF
    # ──────────────────────────────────────────────────────────────────────────

    def _exportar_pdf(self):
        if not REPORTLAB_OK:
            messagebox.showerror(
                "Módulo faltante",
                "Instala reportlab:\n  pip install reportlab",
                parent=self.window
            )
            return

        seleccionados = [
            (self.tree.item(i, "values")[0], self.tree.set(i, "CANTIDAD"))
            for i in self.tree.get_children()
            if self.tree.set(i, "CANTIDAD").strip() not in ("", "0")
        ]

        if not seleccionados:
            messagebox.showwarning(
                "Sin productos",
                "Ingresa al menos una cantidad antes de exportar.",
                parent=self.window
            )
            return

        # Fecha en español
        meses = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]
        ahora = datetime.datetime.now()
        fecha_es = (f"{ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"
                    f" – {ahora.strftime('%H:%M')}")

        A5_LARGO = (A5[0], A5[1] + 200)
        ruta_pdf = "Pedido.pdf"

        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=A5_LARGO,
            leftMargin=20, rightMargin=20,
            topMargin=22,  bottomMargin=22
        )

        styles  = getSampleStyleSheet()
        NARANJA = "#FF9900"

        s_header  = ParagraphStyle("H",  fontSize=26, leading=32,
                                   textColor=HexColor(NARANJA), spaceAfter=8)
        s_date    = ParagraphStyle("D",  fontSize=12,
                                   textColor=HexColor("#444444"), spaceAfter=15)
        s_section = ParagraphStyle("S",  fontSize=16, leading=20,
                                   textColor=HexColor(NARANJA), spaceAfter=8)
        s_text    = ParagraphStyle("T",  fontSize=12, leading=16,
                                   textColor=HexColor("#333333"))
        s_product = ParagraphStyle("P",  fontSize=14, leading=18,
                                   textColor=black, spaceAfter=2)
        s_qty     = ParagraphStyle("Q",  fontSize=12, leading=16,
                                   textColor=HexColor("#555555"))

        SEP = ('<font color="#D0D0D0">'
               '─────────────────────────────────────────────'
               '</font>')

        story = [
            Paragraph("Pedido Realizado", s_header),
            Paragraph(fecha_es, s_date),
            Paragraph("Generado por: FarmaTrack – Droguería Irlandesa", s_text),
            Paragraph("Tipo: Solicitud al Centro de Distribución", s_text),
            Spacer(1, 18),
            Paragraph(SEP, styles["Normal"]),
            Spacer(1, 14),
            Paragraph("Artículos solicitados", s_section),
            Spacer(1, 5),
        ]

        for art, cant in seleccionados:
            story += [
                Paragraph(art, s_product),
                Paragraph(f"Cantidad: {cant}", s_qty),
                Spacer(1, 7),
                Paragraph(SEP, styles["Normal"]),
                Spacer(1, 10),
            ]

        # QR
        contenido_qr = f"PEDIDO-{ahora.strftime('%Y%m%d-%H%M%S')}"
        qr_w = qr.QrCodeWidget(contenido_qr)
        bounds = qr_w.getBounds()
        d = Drawing(140, 140)
        d.add(qr_w)

        story += [
            Spacer(1, 22),
            Paragraph("Código QR de Verificación", s_section),
            d,
            Paragraph(f"ID: {contenido_qr}", s_text),
            Spacer(1, 30),
            Paragraph("Notas del pedido", s_section),
            Paragraph(
                "• Informe discrepancias al responsable de compras.<br/>"
                "• Documento generado automáticamente por FarmaTrack.",
                s_text
            ),
            Spacer(1, 25),
            Paragraph(
                '<para alignment="center">'
                '<font size=10 color="#777777">'
                'Droguería Irlandesa – FarmaTrack'
                '</font></para>',
                styles["Normal"]
            ),
        ]

        try:
            doc.build(story)
            messagebox.showinfo(
                "✅ PDF generado",
                f"'{ruta_pdf}' exportado correctamente.\n"
                f"Productos: {len(seleccionados)}",
                parent=self.window
            )
            if os.name == "nt" and os.path.exists(ruta_pdf):
                os.startfile(ruta_pdf)
        except Exception as exc:
            logging.error(f"Error generando PDF Pedido Centro: {exc}")
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{exc}",
                                 parent=self.window)