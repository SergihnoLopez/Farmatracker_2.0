"""
Ventana de actualización de inventario
✅ MEJORADO: Funcionalidad completa con edición inline y formulario de productos nuevos
✅ FRACCIÓN: Cantidad acepta decimales (ej: 0.2, 1.5, 0.333)
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, W, END
from tkinter import ttk, messagebox
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_codigo_barras
import logging


def _parse_cantidad_float(valor: str):
    """
    Convierte texto a float permitiendo decimales (ej: 0.2, 1.5).
    Acepta coma o punto como separador decimal.
    Retorna float o None si inválido.
    """
    try:
        v = float(str(valor).strip().replace(",", "."))
        if v < 0:
            return None
        return v
    except (ValueError, TypeError):
        return None


class ActualizadorWindow:
    """Ventana para actualización rápida de inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Actualizar Inventario")
        self.window.state("zoomed")
        self.window.grab_set()
        self._setup_ui()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """Configura la interfaz"""
        Label(self.window, text="Escanee Código de Barras:", font=FONT_STYLE).pack(pady=10)

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

        # Frame cantidad — acepta fracciones
        frame_cantidad = Frame(self.window)
        frame_cantidad.pack(pady=10)

        Label(frame_cantidad, text="Nueva Cantidad:", font=FONT_STYLE).pack(side="left", padx=5)

        self.entry_cantidad = Entry(frame_cantidad, font=FONT_STYLE, width=10)
        self.entry_cantidad.pack(side="left", padx=5)
        self.entry_cantidad.bind("<Return>", self._actualizar_cantidad)

        Label(
            frame_cantidad,
            text="(acepta decimales: 0.2, 1.5, 0.333...)",
            font=("Arial", 9),
            fg="#888888"
        ).pack(side="left", padx=5)

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
                    FROM productos WHERE codigo_barras = ?
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
        """
        Actualiza la cantidad del producto.
        ✅ FRACCIÓN: acepta decimales como 0.2 o 1.5
        """
        valor = self.entry_cantidad.get().strip()

        cantidad = _parse_cantidad_float(valor)
        if cantidad is None:
            messagebox.showerror(
                "Error",
                "Ingrese una cantidad válida.\n"
                "Puede usar decimales: 1, 0.5, 0.2, 1.333..."
            )
            return

        items = self.tree.get_children()
        if not items:
            return

        item_id = items[0]
        valores = list(self.tree.item(item_id, "values"))
        id_prod = valores[0]

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE productos SET cantidad = ? WHERE id_producto = ?",
                    (cantidad, int(id_prod))
                )
                exito = cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error al actualizar cantidad: {e}")
            exito = False

        if exito:
            cantidad_display = int(cantidad) if cantidad == int(cantidad) else round(cantidad, 6)
            valores[3] = cantidad_display
            self.tree.item(item_id, values=valores)
            messagebox.showinfo("Éxito", f"Cantidad actualizada a {cantidad_display}")
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
        columnas_bd = ("id_producto", "codigo_barras", "descripcion", "cantidad",
                       "precio_compra", "precio_venta", "impuesto", "fecha_vencimiento")
        nombre_col = columnas_bd[col_idx]

        if col_idx < 2:
            messagebox.showwarning("Advertencia", "No se puede editar el ID o código de barras")
            return

        bbox = self.tree.bbox(item_id, col)
        if not bbox:
            return

        x, y, w, h = bbox
        valores = self.tree.item(item_id, "values")
        valor_actual = str(valores[col_idx])

        editor = Entry(self.tree, font=FONT_STYLE)
        editor.place(x=x + 1, y=y + 1, width=w - 2, height=h - 2)
        editor.insert(0, valor_actual)
        editor.focus_set()
        editor.select_range(0, END)

        def guardar(event=None):
            nuevo_valor = editor.get().strip()

            if nombre_col == "cantidad":
                cantidad = _parse_cantidad_float(nuevo_valor)
                if cantidad is None:
                    messagebox.showerror("Error", "Cantidad inválida. Use números como 1, 0.5, 0.2")
                    editor.focus_set()
                    return
                nuevo_valor_bd = cantidad
                nuevo_valor_display = int(cantidad) if cantidad == int(cantidad) else round(cantidad, 6)
            elif nombre_col in ("precio_compra", "precio_venta"):
                try:
                    precio = float(nuevo_valor.replace(",", "."))
                    if precio < 0:
                        raise ValueError
                    nuevo_valor_bd = precio
                    nuevo_valor_display = nuevo_valor_bd
                except ValueError:
                    messagebox.showerror("Error", "Precio inválido")
                    editor.focus_set()
                    return
            else:
                nuevo_valor_bd = nuevo_valor
                nuevo_valor_display = nuevo_valor

            id_prod = valores[0]
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"UPDATE productos SET {nombre_col} = ? WHERE id_producto = ?",
                        (nuevo_valor_bd, int(id_prod))
                    )
                    exito = cursor.rowcount > 0
            except Exception as e:
                logging.error(f"Error al editar celda: {e}")
                exito = False

            if exito:
                nuevos_valores = list(valores)
                nuevos_valores[col_idx] = nuevo_valor_display
                self.tree.item(item_id, values=nuevos_valores)
            else:
                messagebox.showerror("Error", "No se pudo actualizar el dato")

            editor.destroy()

        editor.bind("<Return>", guardar)
        editor.bind("<Escape>", lambda e: editor.destroy())
        editor.bind("<FocusOut>", lambda e: editor.destroy())

    def _abrir_formulario_nuevo(self, codigo_barras: str):
        """Abre formulario para agregar un producto nuevo"""
        form = Toplevel(self.window)
        form.title("Nuevo Producto")
        form.geometry("500x620")
        form.transient(self.window)
        form.grab_set()

        campos = [
            ("descripcion", "Descripción"),
            ("proveedor", "Proveedor"),
            ("unidad", "Unidad"),
            ("cantidad", "Cantidad (acepta decimales)"),
            ("precio_compra", "Precio Compra"),
            ("precio_venta", "Precio Venta"),
            ("impuesto", "Impuesto"),
            ("bonificacion", "Bonificación"),
            ("grupo", "Grupo"),
            ("subgrupo", "Subgrupo"),
            ("fecha_vencimiento", "Fecha Vencimiento (YYYY-MM-DD)")
        ]

        Label(form, text=f"Código: {codigo_barras}",
              font=("Titillium Web", 14, "bold"), fg="#2196F3").pack(pady=10)

        entradas = {}
        for campo, etiqueta in campos:
            frame = Frame(form)
            frame.pack(fill="x", padx=20, pady=5)
            Label(frame, text=f"{etiqueta}:", font=FONT_STYLE, width=22, anchor="w").pack(side="left")
            entrada = Entry(frame, font=FONT_STYLE, width=25)
            entrada.pack(side="left", fill="x", expand=True)
            entradas[campo] = entrada

        entradas["descripcion"].focus()

        def guardar():
            datos = {
                "codigo_barras": codigo_barras,
                "descripcion": entradas["descripcion"].get().strip(),
                "proveedor": entradas["proveedor"].get().strip(),
                "unidad": entradas["unidad"].get().strip(),
                "cantidad": entradas["cantidad"].get().strip() or "0",
                "precio_compra": entradas["precio_compra"].get().strip() or "0",
                "precio_venta": entradas["precio_venta"].get().strip() or "0",
                "impuesto": entradas["impuesto"].get().strip(),
                "bonificacion": entradas["bonificacion"].get().strip() or "0",
                "grupo": entradas["grupo"].get().strip(),
                "subgrupo": entradas["subgrupo"].get().strip(),
                "fecha_vencimiento": entradas["fecha_vencimiento"].get().strip()
            }
            if not datos["descripcion"]:
                messagebox.showerror("Error", "La descripción es obligatoria")
                return
            from controllers.inventario import InventarioController
            if InventarioController.agregar_producto(datos):
                form.destroy()
                self.entry_codigo.delete(0, END)
                self.entry_codigo.focus()
            else:
                messagebox.showerror("Error", "No se pudo agregar el producto")

        Button(form, text="Guardar Producto", font=FONT_STYLE,
               bg="#4CAF50", fg="white", command=guardar, width=20).pack(pady=20)

    def _on_close(self):
        self.window.destroy()
