"""
Ventana principal de la aplicación
✅ MIGRADO A CUSTOMTKINTER
✅ CORREGIDO: Usa CTkImage para imágenes (sin warnings)
✅ CORREGIDO: Maximiza ventana DESPUÉS de configurar UI

Elimina TOTALMENTE:
- tk.Tk → ctk.CTk
- tk.Frame → ctk.CTkFrame
- tk.Label → ctk.CTkLabel
- tk.Button → ctk.CTkButton
- PIL.ImageTk.PhotoImage → customtkinter.CTkImage (sin warnings)
"""

import customtkinter as ctk
from ctk_design_system import (
    CTkPrimaryButton,
    Colors,
    Fonts,
    Dimensions,
)
from PIL import Image
from config.settings import RESOURCES_DIR
import logging


class MainWindow:
    """Ventana principal del sistema - CustomTkinter"""

    def __init__(self):
        # ✅ ctk.CTk en lugar de tk.Tk
        self.root = ctk.CTk()
        self.root.title("FarmaProStocker - Droguería Irlandesa")

        # ✅ fg_color en lugar de configure(bg=)
        self.root.configure(fg_color=Colors.BACKGROUND)

        self.after_id = None
        self.gif_frames = []  # Lista de CTkImage
        self.frame_delays = []
        self.current_frame = 0

        self._setup_ui()
        self._load_animation()

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

        # ✅ CTkLabel para GIF (se llenará con CTkImage)
        self.gif_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            fg_color="transparent"
        )
        self.gif_label.pack(pady=10)

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

    def _load_animation(self):
        """
        Carga el GIF animado usando CTkImage
        ✅ CORREGIDO: Usa CTkImage en lugar de ImageTk.PhotoImage
        """
        gif_path = RESOURCES_DIR / "animacion.gif"

        if not gif_path.exists():
            logging.warning(f"GIF no encontrado: {gif_path}")
            return

        try:
            gif = Image.open(gif_path)

            # Extraer frames del GIF
            frame_index = 0
            while True:
                try:
                    gif.seek(frame_index)

                    # Copiar frame actual
                    frame = gif.copy()
                    frame = frame.resize((400, 400), Image.Resampling.LANCZOS)

                    # ✅ IMPORTANTE: Usar CTkImage en lugar de ImageTk.PhotoImage
                    ctk_image = ctk.CTkImage(
                        light_image=frame,
                        dark_image=frame,  # Mismo para light/dark (solo usamos light)
                        size=(400, 400)
                    )

                    self.gif_frames.append(ctk_image)

                    # Guardar delay del frame
                    delay = gif.info.get('duration', 50)
                    self.frame_delays.append(delay)

                    frame_index += 1
                except EOFError:
                    break

            if self.gif_frames:
                self._animate_gif()
                logging.info(f"GIF cargado: {len(self.gif_frames)} frames")

        except Exception as e:
            logging.error(f"Error al cargar GIF: {e}")

    def _animate_gif(self):
        """Anima el GIF frame por frame"""
        if not self.gif_frames:
            return

        # ✅ Configurar imagen usando CTkImage (no hay warning)
        self.gif_label.configure(image=self.gif_frames[self.current_frame])

        # Siguiente frame
        self.current_frame = (self.current_frame + 1) % len(self.gif_frames)

        # Programar siguiente actualización con delay específico del frame
        delay = self.frame_delays[self.current_frame] if self.frame_delays else 50
        self.after_id = self.root.after(delay, self._animate_gif)

    def _on_close(self):
        """Maneja el cierre de la ventana"""
        # Detener animación
        if self.after_id:
            self.root.after_cancel(self.after_id)

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