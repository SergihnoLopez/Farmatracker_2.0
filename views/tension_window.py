"""
Ventana de Toma de Tensión Arterial - FarmaTrack
Droguería Irlandesa

✅ win32print/win32ui: importado silenciosamente (sin warning al arrancar)
   — solo se activa en Windows cuando el usuario pulsa Imprimir
✅ Si no está disponible, muestra los valores en pantalla sin imprimir
"""

import customtkinter as ctk
import tkinter.messagebox
import logging
from datetime import datetime

# Importar win32 silenciosamente (solo Windows; sin warning al cargar el módulo)
try:
    import win32print
    import win32ui
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
        self.window.geometry("430x520")
        self.window.resizable(False, False)
        self.window.grab_set()

        # Centrar en pantalla
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - 215
        y = (self.window.winfo_screenheight() // 2) - 260
        self.window.geometry(f"430x520+{x}+{y}")

        self._cargar_impresoras()
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────────
    def _cargar_impresoras(self):
        """Obtiene lista de impresoras; lista vacía si win32 no está disponible."""
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

        # Selector de impresora
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
        ).pack(fill="x", pady=(0, 18))

        # Botón imprimir
        ctk.CTkButton(
            body,
            text="🖨️  Imprimir Ticket",
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
            # Mostrar resultado en pantalla; no hay error, simplemente se informa
            tkinter.messagebox.showinfo(
                "Resultado de la medición",
                f"Tensión Arterial:  {sistolica} / {diastolica}  mmHg\n"
                f"Frecuencia cardíaca:  {frecuencia}  ppm\n\n"
                "ℹ️ La impresión física requiere Windows con\n"
                "   impresora térmica conectada.",
                parent=self.window,
            )
            return

        self._enviar_impresora(sistolica, diastolica, frecuencia)

    def _enviar_impresora(self, sistolica, diastolica, frecuencia):
        """Envía el ticket a la impresora térmica usando win32."""
        try:
            now   = datetime.now()
            meses = {
                "January":   "ENERO",     "February":  "FEBRERO",
                "March":     "MARZO",     "April":     "ABRIL",
                "May":       "MAYO",      "June":      "JUNIO",
                "July":      "JULIO",     "August":    "AGOSTO",
                "September": "SEPTIEMBRE","October":   "OCTUBRE",
                "November":  "NOVIEMBRE", "December":  "DICIEMBRE",
            }
            mes   = meses.get(now.strftime("%B"), now.strftime("%B").upper())
            fecha = f"{now.day} DE {mes} DE {now.year}"
            hora  = now.strftime("%#I:%M %p").lower()

            printer = self.impresora_var.get()
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer)
            hDC.StartDoc("Tensión Arterial")
            hDC.StartPage()

            W  = 384      # px para impresora térmica 58 mm
            cx = W // 2
            y  = 40

            def centro(texto, size, y_off, bold=True):
                font = win32ui.CreateFont({
                    "name": "Tahoma",
                    "height": size,
                    "weight": 700 if bold else 400,
                })
                hDC.SelectObject(font)
                tw = hDC.GetTextExtent(texto)[0]
                hDC.TextOut(cx - tw // 2, y_off, texto)

            centro("DROGUERIA IRLANDESA",       34, y, bold=True);  y += 52
            centro(fecha,                        37, y, bold=False); y += 56
            centro(hora,                         37, y, bold=False); y += 62
            hDC.MoveTo(10, y); hDC.LineTo(W - 10, y);              y += 44

            centro("TENSION",                    48, y);             y += 54
            centro("ARTERIAL",                   48, y);             y += 70
            centro(f"{sistolica}/{diastolica}",  70, y);             y += 124

            centro("FRECUENCIA",  40, y, bold=False);               y += 44
            centro("CARDIACA",    40, y, bold=False);               y += 58
            centro(frecuencia,    46, y);                            y += 102

            hDC.MoveTo(10, y); hDC.LineTo(W - 10, y);              y += 38
            centro("Vuelva pronto", 32, y, bold=False)

            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()

            tkinter.messagebox.showinfo(
                "✅ Impresión exitosa",
                "Ticket enviado a la impresora.",
                parent=self.window,
            )
            logging.info(
                f"Tensión impresa: {sistolica}/{diastolica} FC:{frecuencia}"
            )

            # Limpiar campos para nueva lectura
            for entry in self.entradas.values():
                entry.delete(0, "end")
            self.entradas["sistolica"].focus()

        except Exception as exc:
            logging.error(f"Error imprimiendo tensión: {exc}")
            tkinter.messagebox.showerror(
                "Error de impresión",
                f"No se pudo imprimir:\n{exc}",
                parent=self.window,
            )