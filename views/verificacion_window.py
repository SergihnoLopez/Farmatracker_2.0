"""
Ventana de verificación rápida
"""
from tkinter import Toplevel, Label, Entry, StringVar
from models.database import DatabaseManager


class VerificacionWindow:
    """Ventana para verificar si productos están en inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Verificación Rápida")
        self.window.geometry("500x250")
        self.window.resizable(False, False)
        self.window.grab_set()

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz"""
        Label(
            self.window,
            text="Escanee o ingrese el código de barras",
            font=("Arial", 13, "bold")
        ).pack(pady=(20, 10))

        self.codigo_var = StringVar(master=self.window)

        self.entry_codigo = Entry(
            self.window,
            textvariable=self.codigo_var,
            font=("Arial", 16),
            justify="center",
            width=30
        )
        self.entry_codigo.pack(pady=10)
        self.entry_codigo.focus_set()
        self.entry_codigo.bind("<Return>", self._verificar_codigo)

        self.lbl_resultado = Label(
            self.window,
            text="",
            font=("Arial", 14, "bold")
        )
        self.lbl_resultado.pack(pady=20)

    def _verificar_codigo(self, event=None):
        """Verifica si el código existe en BD"""
        codigo = self.codigo_var.get().strip()

        if not codigo:
            return

        producto = DatabaseManager.buscar_producto_por_codigo(codigo)

        if producto:
            desc = producto.get('descripcion', '')
            self.lbl_resultado.config(
                text=f"✅ ESTÁ EN EL INVENTARIO\n{desc}",
                fg="green"
            )
        else:
            self.lbl_resultado.config(
                text="❌ NO ESTÁ INVENTARIADO",
                fg="red"
            )

        # Limpiar para siguiente lectura
        self.codigo_var.set("")
        self.entry_codigo.focus_set()