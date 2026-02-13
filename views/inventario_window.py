"""
Ventana de gestión de inventario
✅ MEJORADO: Bugs corregidos + Registro de auditoría
"""
from tkinter import (Toplevel, Frame, Label, Entry, Button, Menu, END, W,
                     messagebox, filedialog, Scrollbar, BOTH, LEFT, RIGHT, Y, VERTICAL)
from tkinter import ttk
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG, COLUMN_WIDTHS
from models.database import DatabaseManager, get_db_connection
from controllers.inventario import InventarioController
from utils.validators import sanitize_sql_column, validate_precio
from utils.formatters import format_precio_display
import bcrypt
from config.settings import PASSWORD_HASH
import pandas as pd
import logging


class InventarioWindow:
    """Ventana para ver y editar inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Inventario de Productos")
        self.window.state("zoomed")

        self.conn = None
        self._setup_ui()
        self._cargar_productos()

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """Configura la interfaz"""
        # ============================================================
        # FRAME DE BÚSQUEDA Y BOTONES
        # ============================================================
        search_frame = Frame(self.window)
        search_frame.pack(fill='x', padx=10, pady=5)

        # Entry de búsqueda
        self.search_entry = Entry(search_frame, font=FONT_STYLE)
        self.search_entry.pack(side=LEFT, expand=True, fill='x', padx=5)
        self.search_entry.bind("<Return>", lambda e: self._buscar())
        self.search_entry.focus()  # Foco inicial en búsqueda

        # Botón Buscar
        Button(
            search_frame,
            text="🔍 Buscar",
            command=self._buscar,
            font=FONT_STYLE,
            bg=BTN_COLOR,
            fg=BTN_FG,
            width=12
        ).pack(side=LEFT, padx=2)

        # Botón Buscar/Reemplazar Precios
        Button(
            search_frame,
            text="💰 Buscar/Reemplazar",
            font=FONT_STYLE,
            bg="#2196F3",
            fg="white",
            width=18,
            command=self._buscar_y_reemplazar
        ).pack(side=RIGHT, padx=2)

        # Botón Exportar a Excel
        Button(
            search_frame,
            text="📊 Exportar Excel",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            width=15,
            command=self._exportar_a_excel
        ).pack(side=RIGHT, padx=2)

        # Botón Actualizar desde Excel
        Button(
            search_frame,
            text="📥 Actualizar Excel",
            font=FONT_STYLE,
            bg="#FFA500",
            fg="white",
            width=16,
            command=self._actualizar_desde_excel
        ).pack(side=RIGHT, padx=2)

        # ============================================================
        # FRAME TABLA CON SCROLLBAR
        # ============================================================
        frame_tabla = Frame(self.window)
        frame_tabla.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Configurar columnas
        columnas = list(COLUMN_WIDTHS.keys())

        # Crear Treeview
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

        # Configurar encabezados y anchos
        for col in columnas:
            self.tree.heading(
                col,
                text=col.replace("_", " ").title(),
                command=lambda _col=col: self._ordenar_columna(_col)
            )
            self.tree.column(
                col,
                width=COLUMN_WIDTHS[col],
                anchor='w'
            )

        # Scrollbar vertical (gruesa para mejor visibilidad)
        scrollbar_y = Scrollbar(
            frame_tabla,
            orient=VERTICAL,
            command=self.tree.yview,
            width=30,
            troughcolor="#E0E0E0",
            bg="#9E9E9E",
            activebackground="#616161"
        )
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        # Posicionar elementos
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_y.pack(side=RIGHT, fill=Y)

        # Scroll con rueda del mouse
        self.tree.bind("<MouseWheel>", self._scroll_mouse)  # Windows
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))  # Linux
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))  # Linux

        # ============================================================
        # FRAME TOTAL CON BOTÓN ACTUALIZAR
        # ============================================================
        total_frame = Frame(self.window)
        total_frame.pack(pady=5)

        # Label total
        self.total_label = Label(
            total_frame,
            text="💰 Valor total del inventario: $0",
            font=("Titillium Web", 14, "bold"),
            fg="black"
        )
        self.total_label.pack(side=LEFT, padx=(10, 5))

        # Botón actualizar total
        Button(
            total_frame,
            text="⟳",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
            fg="white",
            width=2,
            height=1,
            relief="flat",
            command=self._actualizar_total
        ).pack(side=LEFT, padx=5)

        # ============================================================
        # MENÚ CONTEXTUAL Y EVENTOS
        # ============================================================

        # Menú contextual (clic derecho)
        self._setup_context_menu()

        # Doble clic para editar
        self.tree.bind("<Double-1>", self._editar_celda)

        # Variable para control de orden
        self.orden_columnas = {}



    def _setup_context_menu(self):
        """Configura menú de clic derecho"""
        self.menu_contextual = Menu(self.window, tearoff=0)
        self.menu_contextual.add_command(label="Copiar celda", command=self._copiar_celda)
        self.menu_contextual.add_command(label="Eliminar producto", command=self._eliminar_producto)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(
            label="Resetear stock (requiere contraseña)",
            command=self._resetear_stock
        )

        self.tree.bind("<Button-3>", self._mostrar_menu_contextual)

    def _cargar_productos(self):
        """Carga todos los productos en el treeview"""
        productos = DatabaseManager.obtener_todos_productos()

        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insertar productos
        for producto in productos:
            self.tree.insert("", "end", values=producto)

        # Actualizar total
        self._actualizar_total()

    def _buscar(self):
        """Busca productos por texto"""
        consulta = self.search_entry.get().strip().lower()

        if not consulta:
            self._cargar_productos()
            return

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Buscar en todas las columnas
                columnas = list(COLUMN_WIDTHS.keys())
                condiciones = " OR ".join([f"LOWER({col}) LIKE ?" for col in columnas])

                cursor.execute(
                    f"SELECT * FROM productos WHERE {condiciones}",
                    tuple(f"%{consulta}%" for _ in columnas)
                )

                resultados = cursor.fetchall()

                # Limpiar y mostrar
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Convertir Row objects a tuplas antes de insertar
                for producto in resultados:
                    self.tree.insert("", "end", values=tuple(producto))

                if not resultados:
                    messagebox.showinfo("Sin resultados", "No se encontraron productos")

        except Exception as e:
            logging.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error en búsqueda: {e}")

    def _ordenar_columna(self, col):
        """Ordena el treeview por columna"""
        # Obtener todos los datos
        datos = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

        # Determinar si es numérico
        es_numerico = True
        for v, _ in datos:
            try:
                float(str(v).replace(',', '.'))
            except ValueError:
                es_numerico = False
                break

        # Cambiar orden
        descendente = self.orden_columnas.get(col, False)
        self.orden_columnas[col] = not descendente

        # Ordenar
        if es_numerico:
            datos.sort(
                key=lambda t: float(str(t[0]).replace(',', '.')) if t[0] else 0,
                reverse=descendente
            )
        else:
            datos.sort(
                key=lambda t: str(t[0]).lower() if t[0] else '',
                reverse=descendente
            )

        # Reordenar items
        for index, (_, k) in enumerate(datos):
            self.tree.move(k, '', index)

    def _actualizar_total(self):
        """Actualiza el valor total del inventario"""
        total = DatabaseManager.calcular_valor_inventario()
        self.total_label.config(
            text=f"💰 Valor total del inventario: ${total:,.0f}".replace(",", ".")
        )

    def _scroll_mouse(self, event):
        """Scroll con rueda del mouse"""
        self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _editar_celda(self, event):
        """Permite editar celda con doble clic"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not item_id or not col:
            return

        # Obtener índice de columna
        col_num = int(col.replace("#", "")) - 1
        columnas = list(COLUMN_WIDTHS.keys())
        nombre_col = columnas[col_num]

        # No permitir editar ID ni código de barras
        if nombre_col in ('id_producto', 'codigo_barras'):
            messagebox.showwarning(
                "Advertencia",
                "No se puede editar el ID o código de barras"
            )
            return

        # Obtener coordenadas y valor actual
        bbox = self.tree.bbox(item_id, col)
        if not bbox:
            return

        x, y, width, height = bbox
        valores = self.tree.item(item_id, "values")
        valor_actual = valores[col_num]

        # Crear Entry para edición
        editor = Entry(self.tree, font=FONT_STYLE)
        editor.place(x=x + 1, y=y + 1, width=width - 2, height=height - 2)
        editor.insert(0, valor_actual)
        editor.focus_set()
        editor.select_range(0, END)

        def guardar(event=None):
            nuevo_valor = editor.get().strip()

            # Validar según tipo de columna
            if nombre_col in ('precio_compra', 'precio_venta', 'bonificacion'):
                precio_validado = validate_precio(nuevo_valor)
                if precio_validado is None:
                    messagebox.showerror("Error", "Precio inválido")
                    editor.focus_set()
                    return
                nuevo_valor = str(precio_validado)

            elif nombre_col == 'cantidad':
                try:
                    nuevo_valor = str(int(nuevo_valor))
                except ValueError:
                    messagebox.showerror("Error", "Cantidad inválida")
                    editor.focus_set()
                    return

            # Obtener ID del producto
            id_prod = valores[0]

            # Validar nombre de columna
            campo_validado = sanitize_sql_column(nombre_col)
            if not campo_validado:
                messagebox.showerror("Error", "Columna no válida para edición")
                editor.destroy()
                return

            # Actualizar en BD
            if DatabaseManager.actualizar_campo_producto(int(id_prod), campo_validado, nuevo_valor):
                # Actualizar en treeview
                nuevos_valores = list(valores)
                nuevos_valores[col_num] = nuevo_valor
                self.tree.item(item_id, values=nuevos_valores)

                # Actualizar total si cambió precio o cantidad
                if nombre_col in ('precio_compra', 'precio_venta', 'cantidad'):
                    self._actualizar_total()

                messagebox.showinfo("Éxito", "Celda actualizada correctamente")
            else:
                messagebox.showerror("Error", "No se pudo actualizar el dato")

            editor.destroy()

        def cancelar(event=None):
            editor.destroy()

        # Bindings
        editor.bind("<Return>", guardar)
        editor.bind("<Escape>", cancelar)
        editor.bind("<FocusOut>", cancelar)

    def _copiar_celda(self):
        """Copia celda al portapapeles"""
        try:
            item_id = self.tree.focus()
            if not item_id:
                return

            # Obtener columna del menú contextual
            col_x = self.tree.winfo_pointerx() - self.tree.winfo_rootx()
            col = self.tree.identify_column(col_x)

            if not col:
                return

            col_index = int(col.replace("#", "")) - 1
            valor = self.tree.item(item_id, "values")[col_index]

            self.window.clipboard_clear()
            self.window.clipboard_append(str(valor))

            messagebox.showinfo("Copiado", f"Valor copiado al portapapeles:\n{valor}")

        except Exception as e:
            logging.error(f"Error al copiar celda: {e}")
            messagebox.showerror("Error", f"No se pudo copiar: {e}")

    def _eliminar_producto(self):
        """Elimina producto seleccionado"""
        item_id = self.tree.focus()
        if not item_id:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return

        valores = self.tree.item(item_id, "values")
        id_producto = valores[0]
        descripcion = valores[2]

        confirmacion = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el producto?\n\n"
            f"ID: {id_producto}\n"
            f"Descripción: {descripcion}"
        )

        if confirmacion:
            if DatabaseManager.eliminar_producto(int(id_producto)):
                self.tree.delete(item_id)
                self._actualizar_total()
                messagebox.showinfo("Éxito", "Producto eliminado correctamente")
            else:
                messagebox.showerror("Error", "No se pudo eliminar el producto")

    def _resetear_stock(self):
        """
        Resetea todo el stock a 0 (requiere contraseña)
        ✅ MEJORADO: Registra en log de auditoría
        """
        # Ventana de contraseña
        ventana_pass = Toplevel(self.window)
        ventana_pass.title("Confirmación requerida")
        ventana_pass.geometry("350x150")
        ventana_pass.transient(self.window)
        ventana_pass.grab_set()

        Label(
            ventana_pass,
            text="Ingrese la contraseña para continuar:",
            font=FONT_STYLE
        ).pack(pady=10)

        entry_pass = Entry(ventana_pass, show="*", font=FONT_STYLE, width=15)
        entry_pass.pack(pady=5)
        entry_pass.focus()

        def confirmar_reset():
            password = entry_pass.get().encode('utf-8')

            # Verificar hash de contraseña
            try:
                if not bcrypt.checkpw(password, PASSWORD_HASH.encode('utf-8')):
                    messagebox.showerror("Acceso denegado", "Contraseña incorrecta")
                    ventana_pass.destroy()
                    return
            except Exception as e:
                logging.error(f"Error al verificar contraseña: {e}")
                messagebox.showerror("Error", "Error al verificar contraseña")
                ventana_pass.destroy()
                return

            # Confirmación adicional
            confirmacion = messagebox.askyesno(
                "Confirmar reseteo",
                "⚠️ ¿Está seguro de resetear TODO el stock a 0?\n\n"
                "Esta acción NO se puede deshacer.\n\n"
                "Se recomienda hacer un respaldo antes de continuar."
            )

            if not confirmacion:
                ventana_pass.destroy()
                return

            # ✅ REGISTRO DE AUDITORÍA
            from datetime import datetime
            logging.warning(
                f"AUDITORÍA - Reseteo de stock iniciado - "
                f"Usuario: Principal - "
                f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Ejecutar reseteo (incluye backup automático en database.py)
            if DatabaseManager.resetear_stock():
                self._cargar_productos()

                # ✅ REGISTRO DE AUDITORÍA EXITOSA
                logging.warning(
                    f"AUDITORÍA - Reseteo de stock COMPLETADO - "
                    f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                messagebox.showinfo(
                    "Éxito",
                    "Todo el stock ha sido reseteado a 0 correctamente.\n\n"
                    "✅ Se creó un backup automático antes de la operación.\n"
                    "✅ La operación fue registrada en el log de auditoría."
                )
            else:
                logging.error("AUDITORÍA - Reseteo de stock FALLÓ")
                messagebox.showerror("Error", "No se pudo resetear el stock")

            ventana_pass.destroy()

        Button(
            ventana_pass,
            text="Confirmar",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            command=confirmar_reset
        ).pack(pady=10)

        # Permitir confirmar con Enter
        entry_pass.bind("<Return>", lambda e: confirmar_reset())

    def _mostrar_menu_contextual(self, event):
        """Muestra menú contextual en clic derecho"""
        # Seleccionar item bajo el cursor
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)

        try:
            self.menu_contextual.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_contextual.grab_release()

    def _exportar_a_excel(self):
        """
        Exporta inventario completo a Excel
        ✅ MEJORADO: Validación de datos antes de exportar
        """
        try:
            # ✅ VALIDACIÓN: Verificar que hay productos
            productos = DatabaseManager.obtener_todos_productos()

            if not productos:
                messagebox.showwarning(
                    "Inventario Vacío",
                    "No hay productos en el inventario para exportar."
                )
                return

            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialfile="inventario.xlsx"
            )

            if not ruta:
                return

            # Obtener datos
            columnas = list(COLUMN_WIDTHS.keys())

            # Crear DataFrame
            df = pd.DataFrame(productos, columns=columnas)

            # Exportar
            df.to_excel(ruta, index=False, sheet_name="Inventario")

            messagebox.showinfo(
                "✅ Exportación Exitosa",
                f"Inventario exportado correctamente:\n\n"
                f"{ruta}\n\n"
                f"Total productos exportados: {len(productos)}"
            )

        except Exception as e:
            logging.error(f"Error al exportar a Excel: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def _actualizar_desde_excel(self):
        """
        Actualiza precios desde archivo Excel
        ✅ MEJORADO: Ventana de progreso real
        """
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo Excel con precios",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )

        if not archivo:
            return

        # ✅ VENTANA DE PROGRESO REAL
        ventana_progreso = Toplevel(self.window)
        ventana_progreso.title("Procesando...")
        ventana_progreso.geometry("400x100")
        ventana_progreso.transient(self.window)
        ventana_progreso.grab_set()

        Label(
            ventana_progreso,
            text="Procesando archivo Excel...\nPor favor espere.",
            font=FONT_STYLE
        ).pack(pady=20)

        # Barra de progreso indeterminada
        from tkinter import ttk
        progress = ttk.Progressbar(
            ventana_progreso,
            mode='indeterminate',
            length=300
        )
        progress.pack(pady=10)
        progress.start(10)

        # Forzar actualización de la ventana
        ventana_progreso.update()

        # Actualizar en segundo plano
        def actualizar():
            actualizados, insertados = InventarioController.actualizar_producto_desde_excel(archivo)

            # Cerrar ventana de progreso
            progress.stop()
            ventana_progreso.destroy()

            if actualizados or insertados:
                self._cargar_productos()
                messagebox.showinfo(
                    "✅ Actualización Completada",
                    f"Productos actualizados: {actualizados}\n"
                    f"Productos insertados: {insertados}\n\n"
                    f"Total procesados: {actualizados + insertados}"
                )
            else:
                messagebox.showwarning(
                    "Sin Cambios",
                    "No se realizaron actualizaciones.\n\n"
                    "Verifica que el archivo contenga las columnas:\n"
                    "- EAN o Código de Barras\n"
                    "- Venta Real o Precio Compra"
                )

        # Ejecutar actualización después de un pequeño delay
        self.window.after(100, actualizar)

    def _buscar_y_reemplazar(self):
        """Abre diálogo de búsqueda y reemplazo de precios"""
        ventana = Toplevel(self.window)
        ventana.title("Buscar y reemplazar precios")
        ventana.geometry("500x300")
        ventana.transient(self.window)
        ventana.grab_set()

        Label(
            ventana,
            text="Texto a buscar (parcial):",
            font=FONT_STYLE
        ).pack(pady=5)

        entry_busqueda = Entry(ventana, font=FONT_STYLE, width=40)
        entry_busqueda.pack(pady=5)
        entry_busqueda.focus()

        Label(
            ventana,
            text="Nuevo precio de COMPRA (opcional):",
            font=FONT_STYLE
        ).pack(pady=5)

        entry_compra = Entry(ventana, font=FONT_STYLE, width=20)
        entry_compra.pack(pady=5)

        Label(
            ventana,
            text="Nuevo precio de VENTA (opcional):",
            font=FONT_STYLE
        ).pack(pady=5)

        entry_venta = Entry(ventana, font=FONT_STYLE, width=20)
        entry_venta.pack(pady=5)

        def ejecutar():
            texto = entry_busqueda.get().strip()
            compra = entry_compra.get().strip()
            venta = entry_venta.get().strip()

            if not texto:
                messagebox.showerror("Error", "Debe ingresar un texto de búsqueda")
                return

            if not compra and not venta:
                messagebox.showerror(
                    "Error",
                    "Debe ingresar al menos un precio (compra o venta)"
                )
                return

            actualizados = InventarioController.buscar_y_reemplazar_precios(
                texto, compra, venta
            )

            if actualizados:
                self._cargar_productos()
                messagebox.showinfo(
                    "Completado",
                    f"Se actualizaron {actualizados} productos"
                )

            ventana.destroy()

        Button(
            ventana,
            text="Aplicar cambios",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            command=ejecutar
        ).pack(pady=15)

        # Permitir ejecutar con Enter
        entry_busqueda.bind("<Return>", lambda e: entry_compra.focus())
        entry_compra.bind("<Return>", lambda e: entry_venta.focus())
        entry_venta.bind("<Return>", lambda e: ejecutar())

    def _on_close(self):
        """Maneja el cierre de la ventana"""
        self.window.destroy()