"""
Ventana principal de la aplicación
"""
from tkinter import Tk, Frame, Label, Button, messagebox
from tkinter import LEFT
from PIL import Image, ImageTk
from config.settings import FONT_STYLE, BG_COLOR, RESOURCES_DIR
import logging
from views.backup_window import BackupWindow


class MainWindow:
    """Ventana principal del sistema"""

    def __init__(self):
        self.root = Tk()
        self.root.title("FarmaProStocker - Droguería Irlandesa")
        self.root.configure(bg="#FFFFFF")
        self.root.state("zoomed")

        self.after_id = None
        self.gif_frames = []

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

    def _abrir_gestion_backups(self):
        """Abre la ventana de gestión de backups"""
        BackupWindow(self.root)

    def _create_buttons(self):
        """Crea los botones del menú principal"""
        # Importar controladores aquí para evitar importación circular
        from views.venta_window import VentaWindow
        from views.inventario_window import InventarioWindow
        from views.pedidos_window import PedidosWindow
        from views.backup_window import BackupWindow  # ← NUEVO

        frame_botones1 = Frame(self.main_frame, bg=BG_COLOR)
        frame_botones1.pack()

        botones1 = [
            ("Registrar Venta", lambda: VentaWindow(self.root), "#3485e2"),
            ("Ver Inventario", lambda: InventarioWindow(self.root), "#3ec4ed"),
            ("Agregar Producto", self._abrir_agregar_producto, "#63cafe"),
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
            ("Liquidador", self._abrir_liquidador, "#c288e2"),
            ("Actualizar Inventario", self._abrir_actualizar_inventario, "#3485e2"),
            ("Verificación Rápida", self._abrir_verificacion_rapida, "#3ec4ed"),
            ("💾 Gestión de Backups", self._abrir_gestion_backups, "#4CAF50")  # ← NUEVO
        ]

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

    # Al final de la clase, agregar el método handler:

    def _abrir_gestion_backups(self):
        """Abre la ventana de gestión de backups"""
        BackupWindow(self.root)

    def _load_animation(self):
        """Carga y reproduce la animación GIF"""
        gif_path = RESOURCES_DIR / "animacion.gif"

        try:
            gif = Image.open(gif_path)

            # Extraer frames
            while True:
                try:
                    frame_img = gif.copy().resize((300, 300), Image.LANCZOS)
                    frame_tk = ImageTk.PhotoImage(frame_img)
                    self.gif_frames.append(frame_tk)
                    gif.seek(len(self.gif_frames))
                except EOFError:
                    break

            # Iniciar animación
            if self.gif_frames:
                self._update_gif(0)

        except FileNotFoundError:
            logging.warning(f"Archivo de animación no encontrado: {gif_path}")
            # Continuar sin animación

    def _update_gif(self, index):
        """Actualiza el frame del GIF"""
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

    # Métodos placeholder para funcionalidades pendientes
    def _abrir_agregar_producto(self):
        messagebox.showinfo("Info", "Función en desarrollo")

    def _abrir_liquidador(self):
        messagebox.showinfo("Info", "Función en desarrollo")

    def _abrir_actualizar_inventario(self):
        messagebox.showinfo("Info", "Función en desarrollo")

    def _abrir_verificacion_rapida(self):
        messagebox.showinfo("Info", "Función en desarrollo")

    def run(self):
        """Inicia el bucle principal"""
        self.root.mainloop()
