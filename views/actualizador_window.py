"""
Ventana de actualización de inventario
✅ MEJORADO: Funcionalidad completa con edición inline y formulario de productos nuevos
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, W, END
from tkinter import ttk, messagebox
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_codigo_barras
import logging


class ActualizadorWindow:
    """Ventana para actualización rápida de inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Actualizar Inventario")
        self.window.state("zoomed")

        self._setup_ui()

        # Cerrar ventana correctamente
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

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

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id_producto, codigo_barras, descripcion, cantidad, 
                           precio_compra, precio_venta, impuesto, fecha_vencimiento 
                    FROM productos 
                    WHERE codigo_barras = ?
                """, (codigo,))

                producto = cursor.fetchone()

                if producto:
                    self.tree.insert("", "end", values=tuple(producto))
                    self.entry_cantidad.focus()
                else:
                    respuesta = messagebox.askyesno(
                        "Producto No Encontrado",
                        f"El código {codigo} no existe en el inventario.\n\n"
                        "¿Desea agregarlo como producto nuevo?"
                    )
                    if respuesta:
                        self._abrir_formulario_nuevo(codigo)

        except Exception as e:
            logging.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error al buscar producto: {e}")

    def _actualizar_cantidad(self, event=None):
        """Actualiza la cantidad del producto"""
        valor = self.entry_cantidad.get().strip()

        if not valor.isdigit():
            messagebox.showerror("Error", "Ingrese una cantidad válida")
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

            messagebox.showinfo("Éxito", f"Cantidad actualizada a {valor}")

            self.entry_cantidad.delete(0, END)
            self.entry_codigo.delete(0, END)
            self.entry_codigo.focus()
        else:
            messagebox.showerror("Error", "No se pudo actualizar la cantidad")

    def _editar_celda(self, event):
        """Permite editar celdas con doble clic"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item_id or not col:
            return

        col_idx = int(col.replace("#", "")) - 1
        columnas = ("ID", "Código", "Descripción", "Cantidad", "Precio Compra",
                    "Precio Venta", "Impuesto", "Vencimiento")
        nombre_col = columnas[col_idx].lower().replace(" ", "_")

        # No permitir editar ID ni Código de Barras
        if col_idx < 2:  # ID y Código
            messagebox.showwarning(
                "Advertencia",
                "No se puede editar el ID o código de barras"
            )
            return

        bbox = self.tree.bbox(item_id, col)
        if not bbox:
            return

        x, y, w, h = bbox
        valor_actual = self.tree.item(item_id, "values")[col_idx]

        editor = Entry(self.tree, font=FONT_STYLE)
        editor.place(x=x + 1, y=y + 1, width=w - 2, height=h - 2)
        editor.insert(0, valor_actual)
        editor.focus_set()
        editor.select_range(0, END)

        def guardar(event=None):
            nuevo = editor.get().strip()
            valores = list(self.tree.item(item_id, "values"))
            id_prod = valores[0]

            # Mapeo de nombres de columnas
            mapeo_cols = {
                "descripción": "descripcion",
                "cantidad": "cantidad",
                "precio_compra": "precio_compra",
                "precio_venta": "precio_venta",
                "impuesto": "impuesto",
                "vencimiento": "fecha_vencimiento"
            }

            campo_bd = mapeo_cols.get(nombre_col, nombre_col)

            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"UPDATE productos SET {campo_bd} = ? WHERE id_producto = ?",
                        (nuevo, id_prod)
                    )

                valores[col_idx] = nuevo
                self.tree.item(item_id, values=valores)
                messagebox.showinfo("Éxito", "Campo actualizado correctamente")

            except Exception as e:
                logging.error(f"Error al actualizar: {e}")
                messagebox.showerror("Error", f"No se pudo actualizar: {e}")

            editor.destroy()

        def cancelar(event=None):
            editor.destroy()

        editor.bind("<Return>", guardar)
        editor.bind("<Escape>", cancelar)
        editor.bind("<FocusOut>", cancelar)

    def _abrir_formulario_nuevo(self, codigo_barras):
        """Abre formulario para agregar producto nuevo"""
        form = Toplevel(self.window)
        form.title("Agregar Producto Nuevo")
        form.geometry("500x600")
        form.transient(self.window)
        form.grab_set()

        campos = [
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
            ("fecha_vencimiento", "Fecha Vencimiento (YYYY-MM-DD)")
        ]

        Label(
            form,
            text=f"Código: {codigo_barras}",
            font=("Titillium Web", 14, "bold"),
            fg="#2196F3"
        ).pack(pady=10)

        entradas = {}

        for campo, etiqueta in campos:
            frame = Frame(form)
            frame.pack(fill="x", padx=20, pady=5)

            Label(frame, text=f"{etiqueta}:", font=FONT_STYLE, width=20, anchor="w").pack(side="left")
            entrada = Entry(frame, font=FONT_STYLE, width=25)
            entrada.pack(side="left", fill="x", expand=True)
            entradas[campo] = entrada

        # Foco en primer campo
        entradas["descripcion"].focus()

        def guardar():
            datos = {
                'codigo_barras': codigo_barras,
                'descripcion': entradas["descripcion"].get().strip(),
                'proveedor': entradas["proveedor"].get().strip(),
                'unidad': entradas["unidad"].get().strip(),
                'cantidad': entradas["cantidad"].get().strip() or "0",
                'precio_compra': entradas["precio_compra"].get().strip() or "0",
                'precio_venta': entradas["precio_venta"].get().strip() or "0",
                'impuesto': entradas["impuesto"].get().strip(),
                'bonificacion': entradas["bonificacion"].get().strip() or "0",
                'grupo': entradas["grupo"].get().strip(),
                'subgrupo': entradas["subgrupo"].get().strip(),
                'fecha_vencimiento': entradas["fecha_vencimiento"].get().strip()
            }

            if not datos['descripcion']:
                messagebox.showerror("Error", "La descripción es obligatoria")
                return

            from controllers.inventario import InventarioController
            if InventarioController.agregar_producto(datos):
                form.destroy()
                self.entry_codigo.delete(0, END)
                self.entry_codigo.focus()
            else:
                messagebox.showerror("Error", "No se pudo agregar el producto")

        Button(
            form,
            text="Guardar Producto",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            command=guardar,
            width=20
        ).pack(pady=20)

    def _on_close(self):
        """Maneja el cierre de la ventana"""
        self.window.destroy()