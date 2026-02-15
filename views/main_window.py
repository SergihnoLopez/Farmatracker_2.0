"""
Ventana principal de la aplicación
✅ ACTUALIZADO: Todas las funcionalidades conectadas
✅ MEJORADO: Animación GIF optimizada con mejor rendimiento
"""
from tkinter import Tk, Frame, Label, Button, messagebox
from tkinter import LEFT
from PIL import Image, ImageTk
from config.settings import FONT_STYLE, BG_COLOR, RESOURCES_DIR
import logging


class MainWindow:
    """Ventana principal del sistema"""

    def __init__(self):
        self.root = Tk()
        self.root.title("FarmaProStocker - Droguería Irlandesa")
        self.root.configure(bg="#FFFFFF")
        self.root.state("zoomed")

        self.after_id = None
        self.gif_frames = []
        self.frame_delays = []  # ✅ NUEVO: Guardar delay de cada frame
        self.current_frame = 0

        self._setup_ui()
        self._load_animation()

        # Protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        self.main_frame = Frame(self.root, bg="#FFFFFF")
        self.main_frame.pack(expand=True)

        # Label para GIF (se cargará después)
        self.gif_label = Label(self.main_frame, bg="#FFFFFF")
        self.gif_label.pack(pady=10)

        # Títulos
        Label(
            self.main_frame,
            text="FARMATRACK",
            font=("Helvetica Neue", 84, "bold"),
            bg="#FFFFFF",
            fg="#02b2ea"
        ).pack()

        Label(
            self.main_frame,
            text="Droguería Irlandesa",
            font=("Helvetica Neue", 56, "bold"),
            bg="#FFFFFF",
            fg="#02b2ea"
        ).pack(pady=(0, 50))

        # Botones principales
        self._create_buttons()

    def _create_buttons(self):
        """Crea los botones del menú principal"""
        # Importación condicional del módulo de backups
        try:
            from views.backup_window import BackupWindow
            BACKUP_DISPONIBLE = True
        except ImportError:
            BACKUP_DISPONIBLE = False
            logging.warning("Módulo de backups no disponible - funcionalidad deshabilitada")

        # Importar controladores aquí para evitar importación circular
        from views.venta_window import VentaWindow
        from views.inventario_window import InventarioWindow
        from views.pedidos_window import PedidosWindow
        from views.agregar_producto_window import AgregarProductoWindow
        from views.liquidador_window import LiquidadorWindow
        from views.actualizador_window import ActualizadorWindow
        from views.verificacion_window import VerificacionWindow

        frame_botones1 = Frame(self.main_frame, bg=BG_COLOR)
        frame_botones1.pack()

        botones1 = [
            ("Registrar Venta", lambda: VentaWindow(self.root), "#3485e2"),
            ("Ver Inventario", lambda: InventarioWindow(self.root), "#3ec4ed"),
            ("Agregar Producto", lambda: AgregarProductoWindow(self.root), "#63cafe"),
            ("Módulo de Pedidos", lambda: PedidosWindow(self.root), "#c288e2")
        ]

        for texto, comando, color in botones1:
            Button(
                frame_botones1,
                text=texto,
                command=comando,
                font=FONT_STYLE,
                bg=color,
                fg="black",
                width=20,
                height=2
            ).pack(side=LEFT, padx=10)

        frame_botones2 = Frame(self.main_frame, bg=BG_COLOR)
        frame_botones2.pack(pady=10)

        botones2 = [
            ("Liquidador", lambda: LiquidadorWindow(self.root), "#c288e2"),
            ("Actualizar Inventario", lambda: ActualizadorWindow(self.root), "#3485e2"),
            ("Verificación Rápida", lambda: VerificacionWindow(self.root), "#3ec4ed")
        ]

        # Solo agregar botón de backups si está disponible
        if BACKUP_DISPONIBLE:
            botones2.append(("💾 Gestión de Backups", lambda: BackupWindow(self.root), "#4CAF50"))

        for texto, comando, color in botones2:
            Button(
                frame_botones2,
                text=texto,
                command=comando,
                font=FONT_STYLE,
                bg=color,
                fg="black",
                width=20,
                height=2
            ).pack(side=LEFT, padx=10)

    def _load_animation(self):
        """
        Carga y reproduce la animación GIF
        ✅ MEJORADO: Extrae delay de cada frame del GIF
        """
        gif_path = RESOURCES_DIR / "animacion.gif"

        try:
            gif = Image.open(gif_path)

            # ✅ NUEVO: Extraer frames y delays individuales
            frame_index = 0
            while True:
                try:
                    gif.seek(frame_index)

                    # Obtener delay del frame actual (en milisegundos)
                    # El GIF almacena el delay en la key 'duration'
                    try:
                        delay = gif.info.get('duration', 50)  # Default 50ms si no hay info
                    except:
                        delay = 50

                    # Asegurar delay mínimo de 20ms (50fps máximo) para fluidez
                    delay = max(20, delay)

                    # Redimensionar y convertir frame
                    frame_img = gif.copy().resize((300, 300), Image.LANCZOS)
                    frame_tk = ImageTk.PhotoImage(frame_img)

                    self.gif_frames.append(frame_tk)
                    self.frame_delays.append(delay)

                    frame_index += 1

                except EOFError:
                    break

            # Iniciar animación si hay frames
            if self.gif_frames:
                logging.info(f"GIF cargado: {len(self.gif_frames)} frames")
                self._update_gif_optimized(0)
            else:
                logging.warning("No se pudieron extraer frames del GIF")

        except FileNotFoundError:
            logging.warning(f"Archivo de animación no encontrado: {gif_path}")
            # Continuar sin animación
        except Exception as e:
            logging.error(f"Error al cargar GIF: {e}", exc_info=True)

    def _update_gif_optimized(self, index):
        """
        ✅ NUEVO: Actualiza el frame del GIF usando delay específico de cada frame
        Esto respeta el timing original del GIF para animaciones más fluidas
        """
        # Verificar que la ventana sigue existiendo
        if not self.gif_label.winfo_exists():
            return

        if self.gif_frames:
            # Mostrar frame actual
            frame = self.gif_frames[index]
            self.gif_label.config(image=frame)

            # Obtener delay para este frame específico
            delay = self.frame_delays[index]

            # Programar siguiente frame
            next_index = (index + 1) % len(self.gif_frames)
            self.after_id = self.root.after(
                delay,
                self._update_gif_optimized,
                next_index
            )

    def _update_gif(self, index):
        """
        ⚠️ DEPRECADO: Método antiguo - mantener por compatibilidad
        Usar _update_gif_optimized en su lugar
        """
        if not self.gif_label.winfo_exists():
            return

        if self.gif_frames:
            frame = self.gif_frames[index]
            self.gif_label.config(image=frame)
            self.after_id = self.root.after(
                100,
                self._update_gif,
                (index + 1) % len(self.gif_frames)
            )

    def _on_close(self):
        """Maneja el cierre de la ventana"""
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except:
                pass
        self.root.destroy()

    def run(self):
        """Inicia el bucle principal"""
        self.root.mainloop()