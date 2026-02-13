"""
Ventana de actualización de inventario
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, W, END
from tkinter import ttk, messagebox
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_codigo_barras


class ActualizadorWindow:
    """Ventana para actualización rápida de inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Actualizar Inventario")
        self.window.state("zoomed")

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz"""
        Label(
            self.window,
            text="Escanee Código de Barras:",
            font=FONT_STYLE
        ).pack(pady=10)

        self.entry_codigo = Entry(self.window, font=FONT_STYLE, width=50)
        self.entry_codigo.pack()
        self.entry_codigo.focus()
        self.entry_codigo.bind("<Return>", self._buscar_producto)

        # Treeview
        columnas = ("ID", "Código", "Descripción", "Cantidad", "Precio Compra",
                    "Precio Venta", "Impuesto", "Vencimiento")

        self.tree = ttk.Treeview(self.window, columns=columnas, show="headings", height=1)

        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        self.tree.pack(pady=20, fill="x")

        # Frame cantidad
        frame_cantidad = Frame(self.window)
        frame_cantidad.pack(pady=10)

        Label(frame_cantidad, text="Nueva Cantidad:", font=FONT_STYLE).pack(side="left", padx=5)

        self.entry_cantidad = Entry(frame_cantidad, font=FONT_STYLE, width=10)
        self.entry_cantidad.pack(side="left", padx=5)
        self.entry_cantidad.bind("<Return>", self._actualizar_cantidad)

        # Doble clic para editar
        self.tree.bind("<Double-1>", self._editar_celda)

    def _buscar_producto(self, event=None):
        """Busca producto por código"""
        codigo = self.entry_codigo.get().strip()

        if not validate_codigo_barras(codigo):
            return

        self.tree.delete(*self.tree.get_children())

        producto = DatabaseManager.buscar_producto_por_codigo(codigo)

        if producto:
            self.tree.insert("", "end", values=(
                producto['id_producto'],
                producto['codigo_barras'],
                producto['descripcion'],
                producto['cantidad'],
                producto['precio_compra'],
                producto['precio_venta'],
                producto.get('impuesto', ''),
                producto.get('fecha_vencimiento', '')
            ))
            self.entry_cantidad.focus()
        else:
            messagebox.showinfo("No existe", "Producto no encontrado")

    def _actualizar_cantidad(self, event=None):
        """Actualiza la cantidad del producto"""
        valor = self.entry_cantidad.get().strip()

        if not valor.isdigit():
            return

        items = self.tree.get_children()
        if not items:
            return

        item_id = items[0]
        valores = list(self.tree.item(item_id, "values"))
        id_prod = valores[0]

        if DatabaseManager.actualizar_cantidad(int(id_prod), int(valor)):
            valores[3] = valor
            self.tree.item(item_id, values=valores)

            self.entry_cantidad.delete(0, END)
            self.entry_codigo.delete(0, END)
            self.entry_codigo.focus()

    def _editar_celda(self, event):
        """Edita celda con doble clic"""
        # Implementación similar a inventario_window
        messagebox.showinfo("Info", "Edición inline - Por implementar")
