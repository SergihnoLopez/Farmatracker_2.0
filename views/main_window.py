"""
Ventana principal de la aplicación
✅ MIGRADO A CUSTOMTKINTER
✅ CORREGIDO: Usa video MP4 con OpenCV (cv2)
✅ CORREGIDO: Maximiza ventana DESPUÉS de configurar UI

Elimina TOTALMENTE:
- tk.Tk → ctk.CTk
- tk.Frame → ctk.CTkFrame
- tk.Label → ctk.CTkLabel
- tk.Button → ctk.CTkButton
- GIF animado → Video MP4 con OpenCV
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

# Importar OpenCV para reproducir video
try:
    import cv2
    VIDEO_DISPONIBLE = True
except ImportError:
    VIDEO_DISPONIBLE = False
    logging.warning("OpenCV no está instalado. Instala con: pip install opencv-python")


class MainWindow:
    """Ventana principal del sistema - CustomTkinter"""

    def __init__(self):
        # ✅ ctk.CTk en lugar de tk.Tk
        self.root = ctk.CTk()
        self.root.title("FarmaProStocker - Droguería Irlandesa")

        # ✅ fg_color en lugar de configure(bg=)
        self.root.configure(fg_color=Colors.BACKGROUND)

        # Variables para el video
        self.video_capture = None
        self.video_label = None
        self.video_after_id = None
        self.video_fps = 30  # FPS por defecto

        self._setup_ui()
        self._load_video()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ✅ MAXIMIZAR AL FINAL - Después de configurar toda la UI
        # Usar after() asegura que se ejecute después del renderizado inicial
        self.root.after(10, self._maximizar_ventana)

    def _maximizar_ventana(self):
        """
        Maximiza la ventana después de que se haya renderizado completamente.
        Se ejecuta 10ms después de la inicialización para evitar conflictos con CustomTkinter.
        """
        try:
            # Método principal para Windows
            self.root.state("zoomed")
            logging.info("Ventana maximizada con state('zoomed')")
        except Exception as e:
            logging.warning(f"state('zoomed') falló: {e}")
            # Fallback para diferentes plataformas
            try:
                # Linux/Mac
                self.root.attributes('-zoomed', True)
                logging.info("Ventana maximizada con attributes('-zoomed')")
            except Exception as e2:
                logging.warning(f"attributes('-zoomed') falló: {e2}")
                # Último recurso: geometry manual
                try:
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    self.root.geometry(f"{screen_width}x{screen_height}+0+0")
                    logging.info(f"Ventana maximizada con geometry manual: {screen_width}x{screen_height}")
                except Exception as e3:
                    logging.error(f"No se pudo maximizar la ventana: {e3}")

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # ✅ CTkFrame en lugar de Frame
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=Colors.SURFACE,
            corner_radius=0
        )
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # ✅ Label de tkinter para mostrar frames del video
        self.video_label = tk.Label(
            self.main_frame,
            bg=Colors.SURFACE
        )
        self.video_label.pack(pady=10)

        # ✅ CTkLabel para títulos
        title = ctk.CTkLabel(
            self.main_frame,
            text="FARMATRACK",
            font=(Fonts.FAMILY, 84, "bold"),
            text_color=Colors.PRIMARY
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Droguería Irlandesa",
            font=(Fonts.FAMILY, 56, "bold"),
            text_color=Colors.PRIMARY
        )
        subtitle.pack(pady=(0, 50))

        # Crear botones del menú principal
        self._create_buttons()

    def _create_buttons(self):
        """Crea los botones del menú principal"""
        # Importación condicional de ventanas
        try:
            from views.backup_window import BackupWindow
            BACKUP_DISPONIBLE = True
        except ImportError:
            BACKUP_DISPONIBLE = False
            logging.warning("Módulo de backups no disponible")

        # ✅ Importar ventanas necesarias
        from views.venta_window import VentaWindow
        from views.inventario_window import InventarioWindow
        from views.pedidos_window import PedidosWindow
        from views.agregar_producto_window import AgregarProductoWindow
        from views.liquidador_window import LiquidadorWindow
        from views.actualizador_window import ActualizadorWindow
        from views.verificacion_window import VerificacionWindow

        # ✅ Frame para primera fila de botones
        frame_botones1 = ctk.CTkFrame(
            self.main_frame,
            fg_color=Colors.SURFACE,
            corner_radius=0
        )
        frame_botones1.pack()

        # Primera fila de botones
        botones1 = [
            ("💰 Registrar Venta", lambda: VentaWindow(self.root)),
            ("📦 Ver Inventario", lambda: InventarioWindow(self.root)),
            ("➕ Agregar Producto", lambda: AgregarProductoWindow(self.root)),
            ("📋 Módulo de Pedidos", lambda: PedidosWindow(self.root))
        ]

        for texto, comando in botones1:
            btn = CTkPrimaryButton(
                frame_botones1,
                text=texto,
                command=comando,
                width=220,
                height=Dimensions.BUTTON_HEIGHT
            )
            btn.pack(side="left", padx=10)

        # ✅ Frame para segunda fila de botones
        frame_botones2 = ctk.CTkFrame(
            self.main_frame,
            fg_color=Colors.SURFACE,
            corner_radius=0
        )
        frame_botones2.pack(pady=10)

        # Segunda fila de botones
        botones2 = [
            ("💵 Liquidador", lambda: LiquidadorWindow(self.root)),
            ("🔄 Actualizar Inventario", lambda: ActualizadorWindow(self.root)),
            ("✅ Verificación Rápida", lambda: VerificacionWindow(self.root))
        ]

        for texto, comando in botones2:
            btn = CTkPrimaryButton(
                frame_botones2,
                text=texto,
                command=comando,
                width=220,
                height=Dimensions.BUTTON_HEIGHT
            )
            btn.pack(side="left", padx=10)

        # ✅ Botón de backups (solo si está disponible)
        if BACKUP_DISPONIBLE:
            btn_backup = CTkPrimaryButton(
                frame_botones2,
                text="💾 Backups",
                command=lambda: BackupWindow(self.root),
                width=220,
                height=Dimensions.BUTTON_HEIGHT,
                fg_color=Colors.SUCCESS  # Verde para destacarlo
            )
            btn_backup.pack(side="left", padx=10)

    def _load_video(self):
        """
        Carga y reproduce el video MP4 usando OpenCV
        ✅ Usa cv2.VideoCapture para leer frames
        ✅ Mantiene dimensiones originales del video
        ✅ Reproduce en loop infinito
        """
        if not VIDEO_DISPONIBLE:
            logging.warning("OpenCV no disponible, video no se mostrará")
            return

        video_path = RESOURCES_DIR / "escudo_vector_farmacia_tecnologia.mp4"

        if not video_path.exists():
            logging.warning(f"Video no encontrado: {video_path}")
            return

        try:
            # Abrir el video con OpenCV
            self.video_capture = cv2.VideoCapture(str(video_path))

            if not self.video_capture.isOpened():
                logging.error(f"No se pudo abrir el video: {video_path}")
                return

            # Obtener FPS del video
            fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.video_fps = int(fps) if fps > 0 else 30

            # Calcular delay entre frames (en milisegundos)
            self.video_delay = int(1000 / self.video_fps)

            # Obtener dimensiones del video
            width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

            logging.info(f"Video cargado: {video_path.name} ({width}x{height}px @ {self.video_fps}fps)")

            # Iniciar reproducción
            self._update_video_frame()

        except Exception as e:
            logging.error(f"Error al cargar video: {e}")

    def _update_video_frame(self):
        """
        Actualiza el frame actual del video
        Se llama recursivamente para crear el efecto de video
        """
        if not self.video_capture or not self.video_capture.isOpened():
            return

        # Leer siguiente frame
        ret, frame = self.video_capture.read()

        if not ret:
            # Si llegamos al final del video, reiniciar desde el principio
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()

        if ret:
            # Convertir de BGR (OpenCV) a RGB (PIL/Tkinter)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convertir a PIL Image
            img = Image.fromarray(frame_rgb)

            # Convertir a PhotoImage para tkinter
            photo = ImageTk.PhotoImage(image=img)

            # Actualizar el label con el nuevo frame
            self.video_label.configure(image=photo)
            self.video_label.image = photo  # Mantener referencia

        # Programar siguiente actualización
        self.video_after_id = self.root.after(self.video_delay, self._update_video_frame)

    def _on_close(self):
        """Maneja el cierre de la ventana"""
        # Detener actualización de frames
        if self.video_after_id:
            self.root.after_cancel(self.video_after_id)

        # Liberar recursos de OpenCV
        if self.video_capture:
            self.video_capture.release()

        # Cerrar aplicación
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Ejecuta el mainloop"""
        self.root.mainloop()


# ==============================================================================
# EJEMPLO DE USO
# ==============================================================================

if __name__ == "__main__":
    import customtkinter as ctk
    from ctk_design_system import initialize_customtkinter

    # ✅ Inicializar ANTES de crear ventanas
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    initialize_customtkinter()

    # Crear y ejecutar aplicación
    app = MainWindow()
    app.run()