"""
Ventana para agregar nuevos productos
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, W, END
from tkinter import messagebox
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from controllers.inventario import InventarioController


class AgregarProductoWindow:
    """Ventana para agregar productos al inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Agregar Producto")
        self.window.state("zoomed")

        self.campos = [
            ("codigo_barras", "Código de Barras"),
            ("descripcion", "Descripción"),
            ("proveedor", "Proveedor"),
            ("unidad", "Unidad"),
            ("cantidad", "Cantidad"),
            ("precio_compra", "Precio Compra"),
            ("precio_venta", "Precio Venta"),
            ("impuesto", "Impuesto"),
            ("bonificacion", "Bonificación"),
            ("grupo", "Grupo"),
            ("subgrupo", "Subgrupo"),
            ("fecha_vencimiento", "Fecha de Vencimiento (YYYY-MM-DD)")
        ]

        self.entradas = {}
        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz"""
        for i, (campo, etiqueta) in enumerate(self.campos):
            Label(
                self.window,
                text=f"{etiqueta}:",
                font=FONT_STYLE
            ).grid(row=i, column=0, padx=10, pady=5, sticky=W)

            entrada = Entry(self.window, font=FONT_STYLE, width=40)
            entrada.grid(row=i, column=1, padx=10, pady=5, sticky=W)
            self.entradas[campo] = entrada

        # Foco en primer campo
        self.entradas['codigo_barras'].focus()

        # Botón guardar
        Button(
            self.window,
            text="Guardar Producto",
            font=FONT_STYLE,
            bg=BTN_COLOR,
            fg=BTN_FG,
            command=self._guardar_producto
        ).grid(row=len(self.campos), column=0, columnspan=2, pady=20)

    def _guardar_producto(self):
        """Guarda el producto"""
        datos = {campo: entrada.get().strip() for campo, entrada in self.entradas.items()}

        if InventarioController.agregar_producto(datos):
            # Limpiar campos
            for entrada in self.entradas.values():
                entrada.delete(0, END)

            self.entradas['codigo_barras'].focus()