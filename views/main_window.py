"""
Ventana principal - FarmaTrack / Droguería Irlandesa
✅ Sin texto encima de los botones (quitado FARMATRACK / Droguería Irlandesa del sidebar)
✅ Botones centrados verticalmente en el sidebar
✅ Video MP4 en tamaño ORIGINAL (sin resize forzado)
✅ 10 botones en 1 sola columna, todos con Colors.PRIMARY
"""

import customtkinter as ctk
from ctk_design_system import (
    CTkPrimaryButton,
    Colors,
    Fonts,
    Dimensions,
)
from config.settings import RESOURCES_DIR
import logging
from PIL import Image, ImageTk
import tkinter as tk

try:
    import cv2
    VIDEO_DISPONIBLE = True
except ImportError:
    VIDEO_DISPONIBLE = False
    logging.warning("OpenCV no instalado. Instala con: pip install opencv-python")


class MainWindow:
    """Ventana principal del sistema"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("FarmaProStocker - Droguería Irlandesa")
        self.root.configure(fg_color=Colors.BACKGROUND)

        self.video_capture  = None
        self.video_label    = None
        self.video_after_id = None
        self.video_delay    = 33

        self._setup_ui()
        self._load_video()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(10, self._maximizar_ventana)

    # ──────────────────────────────────────────────────────────────────────────
    def _maximizar_ventana(self):
        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                try:
                    w = self.root.winfo_screenwidth()
                    h = self.root.winfo_screenheight()
                    self.root.geometry(f"{w}x{h}+0+0")
                except Exception as exc:
                    logging.error(f"No se pudo maximizar: {exc}")

    # ──────────────────────────────────────────────────────────────────────────
    # LAYOUT
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # ── Sidebar izquierdo ─────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self.root,
            fg_color=Colors.SURFACE,
            corner_radius=0,
            width=265
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Frame interior que centra los botones verticalmente
        # Se logra con un frame que crece y empuja desde arriba y abajo
        self.frame_botones = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=Colors.PRIMARY,
            scrollbar_button_hover_color=Colors.PRIMARY_HOVER,
        )
        # expand=True + fill="both" hace que el scrollable ocupe todo el sidebar
        # Los botones quedan centrados porque pack los coloca desde el centro
        # cuando el frame tiene más espacio del que necesitan
        self.frame_botones.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=0      # sin margen extra — el centrado lo dan los spacers internos
        )

        # ── Área central ──────────────────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=Colors.SURFACE,
            corner_radius=0
        )
        self.main_frame.pack(side="right", expand=True, fill="both")

        # Label nativo de tkinter para los frames del video
        self.video_label = tk.Label(self.main_frame, bg=Colors.SURFACE)
        self.video_label.pack(pady=(40, 8))

        ctk.CTkLabel(
            self.main_frame,
            text="FARMATRACK",
            font=(Fonts.FAMILY, 74, "bold"),
            text_color=Colors.PRIMARY,
        ).pack()

        ctk.CTkLabel(
            self.main_frame,
            text="Droguería Irlandesa",
            font=(Fonts.FAMILY, 46, "bold"),
            text_color=Colors.PRIMARY,
        ).pack(pady=(0, 40))

        self._create_buttons()

    # ──────────────────────────────────────────────────────────────────────────
    # BOTONES — 1 columna centrada verticalmente
    # ──────────────────────────────────────────────────────────────────────────

    def _create_buttons(self):
        try:
            from views.backup_window import BackupWindow
            BACKUP_DISPONIBLE = True
        except ImportError:
            BACKUP_DISPONIBLE = False
            logging.warning("Módulo de backups no disponible")

        from views.venta_window            import VentaWindow
        from views.inventario_window       import InventarioWindow
        from views.pedidos_window          import PedidosWindow
        from views.agregar_producto_window import AgregarProductoWindow
        from views.liquidador_window       import LiquidadorWindow
        from views.actualizador_window     import ActualizadorWindow
        from views.verificacion_window     import VerificacionWindow
        from views.tension_window          import TensionWindow
        from views.pedido_centro_window    import PedidoCentroWindow
        from views.reporte_ventas_window   import ReporteVentasWindow

        botones = [
            ("💰  Registrar Venta",       lambda: VentaWindow(self.root)),
            ("📦  Ver Inventario",         lambda: InventarioWindow(self.root)),
            ("➕  Agregar Producto",        lambda: AgregarProductoWindow(self.root)),
            ("📋  Módulo de Pedidos",      lambda: PedidosWindow(self.root)),
            ("💵  Liquidador",             lambda: LiquidadorWindow(self.root)),
            ("🔄  Actualizar Inventario",  lambda: ActualizadorWindow(self.root)),
            ("✅  Verificación Rápida",    lambda: VerificacionWindow(self.root)),
            ("💾  Backups",
             (lambda: BackupWindow(self.root)) if BACKUP_DISPONIBLE
             else (lambda: None)),
            ("🩺  Toma de Tensión",        lambda: TensionWindow(self.root)),
            ("🏬  Pedido Centro",          lambda: PedidoCentroWindow(self.root)),
            ("📊  Reporte de Ventas",      lambda: ReporteVentasWindow(self.root)),
        ]

        n = len(botones)    # 10 botones
        BTN_H   = Dimensions.BUTTON_HEIGHT   # altura de cada botón (46 px)
        GAP     = 8                           # espacio entre botones
        total_h = n * BTN_H + (n - 1) * GAP  # alto total del bloque de botones

        # Spacer superior que empuja los botones hacia el centro
        # (usa place/pack trick: un frame transparente que se expande)
        top_spacer = ctk.CTkFrame(
            self.frame_botones, fg_color="transparent", height=1
        )
        top_spacer.pack(expand=True, fill="both")

        # Espacio equivalente a 2 botones antes del primero
        # 2 × BTN_H (46) + 2 × GAP (8) = 108 px
        TOP_OFFSET = 2 * (BTN_H + GAP)

        # Botones
        for idx, (texto, comando) in enumerate(botones):
            btn = CTkPrimaryButton(
                self.frame_botones,
                text=texto,
                command=comando,
                width=238,
                height=BTN_H,
                anchor="w",
            )
            btn.configure(
                fg_color=Colors.PRIMARY,
                hover_color=Colors.PRIMARY_HOVER,
            )
            # El primer botón lleva el margen superior extra
            top_pad = TOP_OFFSET if idx == 0 else 0
            btn.pack(fill="x", pady=(top_pad, GAP), padx=2)

        # Spacer inferior simétrico
        bot_spacer = ctk.CTkFrame(
            self.frame_botones, fg_color="transparent", height=1
        )
        bot_spacer.pack(expand=True, fill="both")

    # ──────────────────────────────────────────────────────────────────────────
    # VIDEO MP4 — tamaño ORIGINAL del archivo (sin resize)
    # ──────────────────────────────────────────────────────────────────────────

    def _load_video(self):
        if not VIDEO_DISPONIBLE:
            return

        video_path = RESOURCES_DIR / "escudo_vector_farmacia_tecnologia.mp4"
        if not video_path.exists():
            logging.warning(f"Video no encontrado: {video_path}")
            return

        try:
            self.video_capture = cv2.VideoCapture(str(video_path))
            if not self.video_capture.isOpened():
                logging.error("OpenCV no pudo abrir el video")
                return

            fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.video_delay = max(1, int(1000 / (fps if fps > 0 else 30)))

            vw = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            vh = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logging.info(
                f"Video: {video_path.name} {vw}x{vh} @ {fps:.1f}fps (tamaño original)"
            )

            self._update_video_frame()

        except Exception as exc:
            logging.error(f"Error cargando video: {exc}")

    def _update_video_frame(self):
        if not self.video_capture or not self.video_capture.isOpened():
            return

        ret, frame = self.video_capture.read()
        if not ret:
            # Loop: volver al inicio
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()

        if ret:
            # Sin resize — dimensiones originales del video
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
            self.video_label.configure(image=photo)
            self.video_label.image = photo   # referencia obligatoria para evitar GC

        self.video_after_id = self.root.after(
            self.video_delay, self._update_video_frame
        )

    # ──────────────────────────────────────────────────────────────────────────
    def _on_close(self):
        if self.video_after_id:
            self.root.after_cancel(self.video_after_id)
        if self.video_capture:
            self.video_capture.release()
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()