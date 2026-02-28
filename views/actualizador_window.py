"""
Ventana de actualización de inventario
✅ MEJORADO: Funcionalidad completa con edición inline y formulario de productos nuevos
✅ FRACCIÓN: Cantidad acepta decimales (ej: 0.2, 1.5, 0.333)
✅ FECHA VENCIMIENTO: DatePicker inline después de ingresar cantidad
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, W, END, Spinbox
from tkinter import ttk, messagebox
import tkinter as tk
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager, get_db_connection
from utils.validators import validate_codigo_barras
import logging
from datetime import datetime, date
import calendar


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
        self.entry_cantidad.bind("<Return>", self._confirmar_cantidad)

        Label(
            frame_cantidad,
            text="(acepta decimales: 0.2, 1.5, 0.333...)",
            font=("Arial", 9),
            fg="#888888"
        ).pack(side="left", padx=5)

        # ── Frame Fecha de Vencimiento (DatePicker inline) ────────────────────
        self.frame_fecha = Frame(self.window)
        self.frame_fecha.pack(pady=10)

        Label(self.frame_fecha, text="Fecha de Vencimiento:", font=FONT_STYLE).pack(side="left", padx=5)

        # Día / Mes / Año con Spinbox
        hoy = date.today()

        self.spin_dia = Spinbox(self.frame_fecha, from_=1, to=31, width=4,
                                font=FONT_STYLE, justify="center",
                                command=self._validar_dia)
        self.spin_dia.pack(side="left")
        self.spin_dia.delete(0, END)
        self.spin_dia.insert(0, str(hoy.day).zfill(2))

        Label(self.frame_fecha, text="/", font=FONT_STYLE).pack(side="left")

        self.spin_mes = Spinbox(self.frame_fecha, from_=1, to=12, width=4,
                                font=FONT_STYLE, justify="center",
                                command=self._validar_dia)
        self.spin_mes.pack(side="left")
        self.spin_mes.delete(0, END)
        self.spin_mes.insert(0, str(hoy.month).zfill(2))

        Label(self.frame_fecha, text="/", font=FONT_STYLE).pack(side="left")

        self.spin_anio = Spinbox(self.frame_fecha, from_=2020, to=2040, width=6,
                                 font=FONT_STYLE, justify="center")
        self.spin_anio.pack(side="left")
        self.spin_anio.delete(0, END)
        self.spin_anio.insert(0, str(hoy.year))

        Button(
            self.frame_fecha,
            text="✔ Confirmar Fecha",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            command=self._confirmar_fecha
        ).pack(side="left", padx=10)

        # Tecla Enter en Año → confirma fecha
        self.spin_anio.bind("<Return>", lambda e: self._confirmar_fecha())
        self.spin_mes.bind("<Return>", lambda e: self.spin_anio.focus_set())
        self.spin_dia.bind("<Return>", lambda e: self.spin_mes.focus_set())

        Label(
            self.frame_fecha,
            text="(Opcional — Enter para omitir)",
            font=("Arial", 9),
            fg="#888888"
        ).pack(side="left", padx=5)

        # Botón para omitir fecha (solo actualiza cantidad)
        Button(
            self.frame_fecha,
            text="⏭ Omitir Fecha",
            font=("Arial", 9),
            bg="#FF9800",
            fg="white",
            command=self._omitir_fecha
        ).pack(side="left", padx=5)

        # Inicialmente ocultar el frame de fecha
        self.frame_fecha.pack_forget()

        # Cantidad temporal guardada antes de pedir fecha
        self._cantidad_pendiente = None

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

    def _confirmar_cantidad(self, event=None):
        """
        Valida la cantidad ingresada y abre el DatePicker de vencimiento.
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

        self._cantidad_pendiente = cantidad
        # Mostrar frame de fecha y dar foco al día
        self.frame_fecha.pack(pady=10)
        self.spin_dia.focus_set()

    def _validar_dia(self):
        """Ajusta el día máximo según el mes y año seleccionados."""
        try:
            mes = int(self.spin_mes.get())
            anio = int(self.spin_anio.get())
            max_dia = calendar.monthrange(anio, mes)[1]
            self.spin_dia.config(to=max_dia)
        except (ValueError, TypeError):
            pass

    def _confirmar_fecha(self, event=None):
        """Confirma la fecha seleccionada, actualiza BD y vuelve al inicio."""
        try:
            dia  = int(self.spin_dia.get())
            mes  = int(self.spin_mes.get())
            anio = int(self.spin_anio.get())
            fecha_obj = date(anio, mes, dia)
            fecha_str = fecha_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Fecha inválida. Revise día, mes y año.")
            self.spin_dia.focus_set()
            return

        self._guardar_actualizacion(fecha_str)

    def _omitir_fecha(self, event=None):
        """Actualiza solo la cantidad, sin modificar fecha de vencimiento."""
        self._guardar_actualizacion(None)

    def _guardar_actualizacion(self, fecha_str):
        """
        Guarda cantidad (y opcionalmente fecha_vencimiento) en la BD.
        Luego reinicia el formulario para escanear un nuevo producto.
        """
        if self._cantidad_pendiente is None:
            return

        cantidad = self._cantidad_pendiente
        items = self.tree.get_children()
        if not items:
            return

        item_id = items[0]
        valores = list(self.tree.item(item_id, "values"))
        id_prod = valores[0]

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if fecha_str:
                    cursor.execute(
                        "UPDATE productos SET cantidad = ?, fecha_vencimiento = ? WHERE id_producto = ?",
                        (cantidad, fecha_str, int(id_prod))
                    )
                else:
                    cursor.execute(
                        "UPDATE productos SET cantidad = ? WHERE id_producto = ?",
                        (cantidad, int(id_prod))
                    )
                exito = cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error al actualizar producto: {e}")
            exito = False

        if exito:
            cantidad_display = int(cantidad) if cantidad == int(cantidad) else round(cantidad, 6)
            valores[3] = cantidad_display
            if fecha_str:
                valores[7] = fecha_str
            self.tree.item(item_id, values=valores)

            msg = f"✅ Actualizado: cantidad={cantidad_display}"
            if fecha_str:
                msg += f", vencimiento={fecha_str}"
            # Toast breve — no detiene el flujo
            self.window.title(msg)
            self.window.after(2000, lambda: self.window.title("Actualizar Inventario"))
        else:
            messagebox.showerror("Error", "No se pudo actualizar el producto")

        # Reiniciar para siguiente escaneo
        self._cantidad_pendiente = None
        self.frame_fecha.pack_forget()
        self.entry_cantidad.delete(0, END)
        self.entry_codigo.delete(0, END)
        self.entry_codigo.focus()

    def _actualizar_cantidad(self, event=None):
        """
        Mantiene compatibilidad con doble clic en treeview (edición inline).
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