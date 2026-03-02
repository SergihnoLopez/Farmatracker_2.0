"""
Ventana de Toma de Tensión Arterial - FarmaTrack
Droguería Irlandesa

✅ win32print/win32ui: importado silenciosamente (sin warning al arrancar)
   — solo se activa en Windows cuando el usuario pulsa Imprimir
✅ Si no está disponible, muestra los valores en pantalla sin imprimir
✅ MEJORADO: Soporte para CUALQUIER impresora del sistema (térmica, láser, inkjet, PDF)
   — Detecta automáticamente el tamaño de página de la impresora seleccionada
   — Escala fuentes y diseño proporcionalmente al tamaño disponible
   — Funciona con impresoras térmicas (58mm/80mm), A4, Letter, etc.
"""

import customtkinter as ctk
import tkinter.messagebox
import logging
from datetime import datetime

# Importar win32 silenciosamente (solo Windows; sin warning al cargar el módulo)
try:
    import win32print
    import win32ui
    import win32con
    WIN32_OK = True
except ImportError:
    WIN32_OK = False   # se maneja en tiempo de ejecución, no al importar

try:
    from ctk_design_system import Colors, Fonts, Dimensions
except ImportError:
    class Colors:
        PRIMARY        = "#0f6cbd"
        PRIMARY_HOVER  = "#0c5aa6"
        SURFACE        = "#ffffff"
        BACKGROUND     = "#f4f6f8"
        TEXT_PRIMARY   = "#1a1a1a"
        TEXT_SECONDARY = "#616161"
    class Fonts:
        FAMILY = "Segoe UI"
    class Dimensions:
        BUTTON_HEIGHT = 46
        BUTTON_RADIUS = 8


class TensionWindow:
    """Ventana modal para medición e impresión de tensión arterial"""

    def __init__(self, parent):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Tensión Arterial")
        self.window.geometry("430x580")
        self.window.resizable(False, False)
        self.window.grab_set()

        # Centrar en pantalla
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - 215
        y = (self.window.winfo_screenheight() // 2) - 290
        self.window.geometry(f"430x580+{x}+{y}")

        self._cargar_impresoras()
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────────
    def _cargar_impresoras(self):
        """Obtiene lista de impresoras del sistema operativo Windows."""
        self.impresoras = []
        if WIN32_OK:
            try:
                printers = win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                )
                self.impresoras = [p[2] for p in printers]
            except Exception as exc:
                logging.error(f"Error listando impresoras: {exc}")

        if not self.impresoras:
            self.impresoras = ["(Sin impresoras disponibles)"]

    # ──────────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        # Cabecera azul
        header = ctk.CTkFrame(self.window, fg_color=Colors.PRIMARY, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="🏥  Droguería Irlandesa",
            font=(Fonts.FAMILY, 18, "bold"),
            text_color="white",
        ).pack(pady=(14, 2))

        ctk.CTkLabel(
            header,
            text="Medidor de Tensión Arterial",
            font=(Fonts.FAMILY, 12),
            text_color="#cce4ff",
        ).pack(pady=(0, 14))

        # Cuerpo
        body = ctk.CTkFrame(self.window, fg_color=Colors.BACKGROUND, corner_radius=0)
        body.pack(fill="both", expand=True, padx=32, pady=20)

        campos = [
            ("Presión Sistólica  (mmHg)", "Ej: 120", "sistolica"),
            ("Presión Diastólica (mmHg)", "Ej: 80",  "diastolica"),
            ("Frecuencia Cardíaca (ppm)", "Ej: 75",  "frecuencia"),
        ]

        self.entradas    = {}
        widgets_en_orden = []

        for etiqueta, placeholder, clave in campos:
            ctk.CTkLabel(
                body,
                text=etiqueta,
                font=(Fonts.FAMILY, 13, "bold"),
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
            ).pack(fill="x", pady=(8, 2))

            entry = ctk.CTkEntry(
                body,
                placeholder_text=placeholder,
                height=42,
                font=(Fonts.FAMILY, 15),
            )
            entry.pack(fill="x", pady=(0, 4))
            self.entradas[clave] = entry
            widgets_en_orden.append(entry)

        # Navegación con Enter entre campos
        widgets_en_orden[0].bind("<Return>", lambda e: widgets_en_orden[1].focus())
        widgets_en_orden[1].bind("<Return>", lambda e: widgets_en_orden[2].focus())
        widgets_en_orden[2].bind("<Return>", lambda e: self._imprimir())

        # ── Selector de impresora ─────────────────────────────────────────────
        ctk.CTkLabel(
            body,
            text="Impresora:",
            font=(Fonts.FAMILY, 13, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(12, 2))

        self.impresora_var = ctk.StringVar(value=self.impresoras[0])
        ctk.CTkOptionMenu(
            body,
            values=self.impresoras,
            variable=self.impresora_var,
            height=38,
            font=(Fonts.FAMILY, 13),
        ).pack(fill="x", pady=(0, 8))

        # ── Selector de modo de impresión ─────────────────────────────────────
        ctk.CTkLabel(
            body,
            text="Modo de impresión:",
            font=(Fonts.FAMILY, 13, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        self.modo_var = ctk.StringVar(value="Ticket (térmica)")
        ctk.CTkOptionMenu(
            body,
            values=["Ticket (térmica)", "Página completa (láser/inkjet)"],
            variable=self.modo_var,
            height=38,
            font=(Fonts.FAMILY, 13),
        ).pack(fill="x", pady=(0, 14))

        # Botón imprimir
        ctk.CTkButton(
            body,
            text="🖨️  Imprimir Resultado",
            command=self._imprimir,
            height=Dimensions.BUTTON_HEIGHT,
            corner_radius=Dimensions.BUTTON_RADIUS,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color="white",
            font=(Fonts.FAMILY, 16, "bold"),
        ).pack(fill="x")

        # Pie
        ctk.CTkLabel(
            self.window,
            text=f"© Droguería Irlandesa {datetime.now().year}",
            font=(Fonts.FAMILY, 10),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=(2, 8))

        widgets_en_orden[0].focus()

    # ──────────────────────────────────────────────────────────────────────────
    def _imprimir(self):
        sistolica  = self.entradas["sistolica"].get().strip()
        diastolica = self.entradas["diastolica"].get().strip()
        frecuencia = self.entradas["frecuencia"].get().strip()

        if not all([sistolica, diastolica, frecuencia]):
            tkinter.messagebox.showwarning(
                "Campos incompletos",
                "Completa los tres campos antes de imprimir.",
                parent=self.window,
            )
            return

        try:
            int(sistolica); int(diastolica); int(frecuencia)
        except ValueError:
            tkinter.messagebox.showerror(
                "Valor inválido",
                "Solo se permiten números enteros.\nEjemplo: 120 / 80 / 75",
                parent=self.window,
            )
            return

        if not WIN32_OK:
            tkinter.messagebox.showinfo(
                "Resultado de la medición",
                f"Tensión Arterial:  {sistolica} / {diastolica}  mmHg\n"
                f"Frecuencia cardíaca:  {frecuencia}  ppm\n\n"
                "ℹ️ La impresión física requiere Windows con\n"
                "   impresora conectada (pywin32 instalado).",
                parent=self.window,
            )
            return

        # Verificar que hay impresora válida seleccionada
        printer = self.impresora_var.get()
        if printer == "(Sin impresoras disponibles)":
            tkinter.messagebox.showerror(
                "Sin impresora",
                "No se detectaron impresoras en el sistema.\n\n"
                "Verifica que tengas al menos una impresora\n"
                "instalada en Windows.",
                parent=self.window,
            )
            return

        # Determinar modo de impresión
        modo = self.modo_var.get()
        if "Ticket" in modo:
            self._imprimir_ticket(sistolica, diastolica, frecuencia, printer)
        else:
            self._imprimir_pagina(sistolica, diastolica, frecuencia, printer)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO 1: TICKET (impresoras térmicas 58mm / 80mm)
    # ══════════════════════════════════════════════════════════════════════════

    def _imprimir_ticket(self, sistolica, diastolica, frecuencia, printer):
        """
        Imprime en formato ticket para impresoras térmicas.
        Detecta automáticamente el ancho de la impresora.
        """
        try:
            now   = datetime.now()
            fecha = self._formato_fecha(now)
            hora  = now.strftime("%#I:%M %p").lower()

            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer)

            # ── Obtener dimensiones reales de la impresora ────────────────
            W = hDC.GetDeviceCaps(win32con.HORZRES)   # Ancho en píxeles
            H = hDC.GetDeviceCaps(win32con.VERTRES)    # Alto en píxeles

            # Si el ancho es muy grande (> 1000px = probablemente A4),
            # limitar a un ancho de ticket razonable
            if W > 1000:
                W = 576  # 80mm estándar

            cx = W // 2
            margen = max(10, W // 40)

            # Escalar fuentes proporcionalmente al ancho
            # Base: 384px = impresora 58mm
            factor = W / 384.0

            hDC.StartDoc("Tensión Arterial - Ticket")
            hDC.StartPage()

            y = int(30 * factor)

            def _font(size, bold=True):
                return win32ui.CreateFont({
                    "name":   "Tahoma",
                    "height": int(size * factor),
                    "weight": 700 if bold else 400,
                })

            def centro(texto, size, bold=True):
                nonlocal y
                font = _font(size, bold)
                hDC.SelectObject(font)
                tw = hDC.GetTextExtent(texto)[0]
                hDC.TextOut(cx - tw // 2, y, texto)

            def linea():
                nonlocal y
                hDC.MoveTo(margen, y)
                hDC.LineTo(W - margen, y)

            # ── Contenido del ticket ──────────────────────────────────────
            centro("DROGUERIA IRLANDESA", 34, bold=True);    y += int(50 * factor)
            centro(fecha, 30, bold=False);                    y += int(44 * factor)
            centro(hora, 30, bold=False);                     y += int(48 * factor)

            linea();                                          y += int(36 * factor)

            centro("TENSION", 48, bold=True);                 y += int(54 * factor)
            centro("ARTERIAL", 48, bold=True);                y += int(64 * factor)

            centro(f"{sistolica}/{diastolica}", 70, bold=True)
            y += int(100 * factor)

            centro("mmHg", 30, bold=False);                   y += int(60 * factor)

            linea();                                          y += int(36 * factor)

            centro("FRECUENCIA", 40, bold=False);             y += int(44 * factor)
            centro("CARDIACA", 40, bold=False);               y += int(52 * factor)

            centro(frecuencia, 46, bold=True);                y += int(48 * factor)
            centro("ppm", 30, bold=False);                    y += int(70 * factor)

            linea();                                          y += int(36 * factor)
            centro("Vuelva pronto", 28, bold=False)

            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()

            self._exito_impresion(sistolica, diastolica, frecuencia, "ticket")

        except Exception as exc:
            self._error_impresion(exc)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO 2: PÁGINA COMPLETA (láser, inkjet, PDF, cualquier impresora)
    # ══════════════════════════════════════════════════════════════════════════

    def _imprimir_pagina(self, sistolica, diastolica, frecuencia, printer):
        """
        Imprime en formato página completa para impresoras estándar.
        Se adapta al tamaño de página real (A4, Letter, Legal, etc).
        Diseño profesional centrado con márgenes apropiados.
        """
        try:
            now   = datetime.now()
            fecha = self._formato_fecha(now)
            hora  = now.strftime("%#I:%M %p").lower()

            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer)

            # ── Obtener dimensiones reales de la impresora ────────────────
            W = hDC.GetDeviceCaps(win32con.HORZRES)   # Ancho área imprimible
            H = hDC.GetDeviceCaps(win32con.VERTRES)    # Alto área imprimible
            dpi_x = hDC.GetDeviceCaps(win32con.LOGPIXELSX)  # DPI horizontal
            dpi_y = hDC.GetDeviceCaps(win32con.LOGPIXELSY)  # DPI vertical

            # Márgenes en píxeles (aprox. 2cm en cada lado)
            margen_x = int(dpi_x * 0.79)  # ~2cm
            margen_y = int(dpi_y * 0.79)

            # Área útil
            area_w = W - (2 * margen_x)
            area_h = H - (2 * margen_y)
            cx     = W // 2  # Centro horizontal de la página

            # Factor de escala basado en DPI (base: 300 DPI)
            scale = dpi_y / 300.0

            hDC.StartDoc("Tensión Arterial - Resultado")
            hDC.StartPage()

            y = margen_y

            def _font(pts, bold=True, name="Segoe UI"):
                """Crea fuente escalada al DPI de la impresora."""
                # Convertir puntos a unidades lógicas del dispositivo
                height = -int(pts * dpi_y / 72)
                return win32ui.CreateFont({
                    "name":   name,
                    "height": height,
                    "weight": 700 if bold else 400,
                })

            def centro(texto, pts, bold=True, name="Segoe UI"):
                nonlocal y
                font = _font(pts, bold, name)
                hDC.SelectObject(font)
                tw = hDC.GetTextExtent(texto)[0]
                hDC.TextOut(cx - tw // 2, y, texto)

            def izquierda(texto, pts, bold=False, name="Segoe UI"):
                nonlocal y
                font = _font(pts, bold, name)
                hDC.SelectObject(font)
                hDC.TextOut(margen_x, y, texto)

            def derecha(texto, pts, bold=False, name="Segoe UI"):
                nonlocal y
                font = _font(pts, bold, name)
                hDC.SelectObject(font)
                tw = hDC.GetTextExtent(texto)[0]
                hDC.TextOut(W - margen_x - tw, y, texto)

            def linea_horizontal(grosor=2):
                nonlocal y
                pen = win32ui.CreatePen(0, grosor, 0x00000000)  # negro
                hDC.SelectObject(pen)
                hDC.MoveTo(margen_x, y)
                hDC.LineTo(W - margen_x, y)

            def linea_color(color_rgb, grosor=3):
                """Línea con color personalizado (R, G, B)."""
                nonlocal y
                r, g, b = color_rgb
                color = r | (g << 8) | (b << 16)  # COLORREF = 0x00BBGGRR
                pen = win32ui.CreatePen(0, grosor, color)
                hDC.SelectObject(pen)
                hDC.MoveTo(margen_x, y)
                hDC.LineTo(W - margen_x, y)

            def espacio(pts):
                nonlocal y
                y += int(pts * dpi_y / 72)

            # ══════════════════════════════════════════════════════════════
            #  ENCABEZADO
            # ══════════════════════════════════════════════════════════════

            # Línea azul superior decorativa
            linea_color((15, 108, 189), grosor=6)   # Colors.PRIMARY
            espacio(16)

            centro("DROGUERÍA IRLANDESA", 22, bold=True)
            espacio(28)

            centro("Servicio de Toma de Tensión Arterial", 12, bold=False)
            espacio(20)

            linea_horizontal(1)
            espacio(8)

            # Fecha y hora en la misma línea
            font_info = _font(10, bold=False)
            hDC.SelectObject(font_info)
            hDC.TextOut(margen_x, y, f"Fecha: {fecha}")
            tw_hora = hDC.GetTextExtent(f"Hora: {hora}")[0]
            hDC.TextOut(W - margen_x - tw_hora, y, f"Hora: {hora}")
            espacio(20)

            linea_horizontal(1)
            espacio(24)

            # ══════════════════════════════════════════════════════════════
            #  RESULTADOS PRINCIPALES
            # ══════════════════════════════════════════════════════════════

            centro("RESULTADO DE MEDICIÓN", 16, bold=True)
            espacio(32)

            # ── Cuadro de Tensión Arterial ────────────────────────────────
            # Marco exterior
            box_w   = int(area_w * 0.65)
            box_h   = int(dpi_y * 2.0)  # ~2 pulgadas de alto
            box_x   = cx - box_w // 2
            box_y_start = y

            # Borde del cuadro
            pen_box = win32ui.CreatePen(0, 3, 0x00BD6C0F)  # azul PRIMARY
            hDC.SelectObject(pen_box)
            hDC.MoveTo(box_x, box_y_start)
            hDC.LineTo(box_x + box_w, box_y_start)
            hDC.LineTo(box_x + box_w, box_y_start + box_h)
            hDC.LineTo(box_x, box_y_start + box_h)
            hDC.LineTo(box_x, box_y_start)

            # Contenido dentro del cuadro
            espacio(12)
            centro("TENSIÓN ARTERIAL", 14, bold=True)
            espacio(22)

            # Valor grande centrado
            centro(f"{sistolica} / {diastolica}", 36, bold=True)
            espacio(42)

            centro("mmHg", 12, bold=False)
            espacio(18)

            # Clasificación de la tensión
            clasificacion = self._clasificar_tension(int(sistolica), int(diastolica))
            centro(clasificacion, 11, bold=True)

            # Mover Y después del cuadro
            y = box_y_start + box_h
            espacio(20)

            # ── Cuadro de Frecuencia Cardíaca ─────────────────────────────
            box2_w  = int(area_w * 0.50)
            box2_h  = int(dpi_y * 1.3)
            box2_x  = cx - box2_w // 2
            box2_y  = y

            pen_box2 = win32ui.CreatePen(0, 2, 0x00888888)  # gris
            hDC.SelectObject(pen_box2)
            hDC.MoveTo(box2_x, box2_y)
            hDC.LineTo(box2_x + box2_w, box2_y)
            hDC.LineTo(box2_x + box2_w, box2_y + box2_h)
            hDC.LineTo(box2_x, box2_y + box2_h)
            hDC.LineTo(box2_x, box2_y)

            espacio(10)
            centro("FRECUENCIA CARDÍACA", 12, bold=True)
            espacio(18)

            centro(frecuencia, 28, bold=True)
            espacio(34)

            centro("ppm (pulsaciones por minuto)", 9, bold=False)

            y = box2_y + box2_h
            espacio(28)

            # ══════════════════════════════════════════════════════════════
            #  TABLA DE REFERENCIA
            # ══════════════════════════════════════════════════════════════

            linea_horizontal(1)
            espacio(12)

            centro("Tabla de Referencia - Tensión Arterial (AHA)", 10, bold=True)
            espacio(16)

            # Encabezados de tabla
            col1_x = margen_x + int(area_w * 0.05)
            col2_x = margen_x + int(area_w * 0.45)
            col3_x = margen_x + int(area_w * 0.72)

            font_th = _font(9, bold=True)
            hDC.SelectObject(font_th)
            hDC.TextOut(col1_x, y, "Categoría")
            hDC.TextOut(col2_x, y, "Sistólica")
            hDC.TextOut(col3_x, y, "Diastólica")
            espacio(14)

            linea_horizontal(1)
            espacio(6)

            # Filas de la tabla
            tabla = [
                ("Normal",                "< 120",     "< 80"),
                ("Elevada",               "120 - 129", "< 80"),
                ("Hipertensión Etapa 1",  "130 - 139", "80 - 89"),
                ("Hipertensión Etapa 2",  "≥ 140",     "≥ 90"),
                ("Crisis hipertensiva",   "> 180",     "> 120"),
            ]

            font_td = _font(8, bold=False)
            for categoria, sist, diast in tabla:
                hDC.SelectObject(font_td)
                hDC.TextOut(col1_x, y, categoria)
                hDC.TextOut(col2_x, y, sist)
                hDC.TextOut(col3_x, y, diast)
                espacio(13)

            espacio(8)
            linea_horizontal(1)
            espacio(20)

            # ══════════════════════════════════════════════════════════════
            #  PIE DE PÁGINA
            # ══════════════════════════════════════════════════════════════

            centro("Este resultado es informativo y no reemplaza", 8, bold=False)
            espacio(12)
            centro("una consulta médica profesional.", 8, bold=False)
            espacio(20)

            linea_color((15, 108, 189), grosor=4)
            espacio(10)

            centro("Droguería Irlandesa - FarmaTrack", 9, bold=True)
            espacio(14)
            centro("¡Gracias por su visita!", 10, bold=False)

            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()

            self._exito_impresion(sistolica, diastolica, frecuencia, "página")

        except Exception as exc:
            self._error_impresion(exc)

    # ══════════════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _formato_fecha(now):
        """Retorna fecha en formato '26 DE FEBRERO DE 2026'."""
        meses = {
            "January":   "ENERO",     "February":  "FEBRERO",
            "March":     "MARZO",     "April":     "ABRIL",
            "May":       "MAYO",      "June":      "JUNIO",
            "July":      "JULIO",     "August":    "AGOSTO",
            "September": "SEPTIEMBRE","October":   "OCTUBRE",
            "November":  "NOVIEMBRE", "December":  "DICIEMBRE",
        }
        mes = meses.get(now.strftime("%B"), now.strftime("%B").upper())
        return f"{now.day} DE {mes} DE {now.year}"

    @staticmethod
    def _clasificar_tension(sistolica, diastolica):
        """Clasifica la tensión arterial según la AHA."""
        if sistolica > 180 or diastolica > 120:
            return "⚠ CRISIS HIPERTENSIVA - Consulte urgente"
        elif sistolica >= 140 or diastolica >= 90:
            return "Hipertensión Etapa 2"
        elif 130 <= sistolica <= 139 or 80 <= diastolica <= 89:
            return "Hipertensión Etapa 1"
        elif 120 <= sistolica <= 129 and diastolica < 80:
            return "Tensión Elevada"
        elif sistolica < 120 and diastolica < 80:
            return "✓ Normal"
        else:
            return "—"

    def _exito_impresion(self, sistolica, diastolica, frecuencia, modo):
        """Muestra mensaje de éxito y limpia campos."""
        tkinter.messagebox.showinfo(
            "✅ Impresión exitosa",
            f"Resultado enviado a la impresora ({modo}).\n\n"
            f"  Tensión:    {sistolica}/{diastolica} mmHg\n"
            f"  Frecuencia: {frecuencia} ppm",
            parent=self.window,
        )
        logging.info(
            f"Tensión impresa ({modo}): {sistolica}/{diastolica} FC:{frecuencia} "
            f"→ {self.impresora_var.get()}"
        )

        # Limpiar campos para nueva lectura
        for entry in self.entradas.values():
            entry.delete(0, "end")
        self.entradas["sistolica"].focus()

    def _error_impresion(self, exc):
        """Muestra mensaje de error de impresión."""
        logging.error(f"Error imprimiendo tensión: {exc}")
        tkinter.messagebox.showerror(
            "Error de impresión",
            f"No se pudo imprimir el resultado:\n\n{exc}\n\n"
            "Verifica que la impresora esté encendida,\n"
            "conectada y configurada correctamente.",
            parent=self.window,
        )