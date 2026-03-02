"""
Ventana de gestión de inventario
✅ CORREGIDO: Alineación correcta de columnas en Treeview
✅ CORREGIDO: Orden consistente entre SELECT, columnas y valores
"""
from tkinter import (Toplevel, Frame, Label, Entry, Button, Menu, END, W,
                     messagebox, filedialog, Scrollbar, BOTH, LEFT, RIGHT, Y, VERTICAL)
from tkinter import ttk
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager, get_db_connection
from controllers.inventario import InventarioController
from utils.validators import sanitize_sql_column, validate_precio
from utils.formatters import format_precio_display
import bcrypt
from config.settings import PASSWORD_HASH

# AuthManager para control de acceso por rol
try:
    from views.login_window import AuthManager
except ImportError:
    AuthManager = None

import pandas as pd
import logging


class InventarioWindow:
    """Ventana para ver y editar inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Inventario de Productos")
        self.window.state("zoomed")
        self.window.grab_set()
        self.conn = None
        self._setup_ui()
        self._cargar_proveedores()
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
        self.search_entry.focus()

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

        # ============================================================
        # FRAME FILTRO POR PROVEEDOR
        # ============================================================
        filter_frame = Frame(self.window)
        filter_frame.pack(fill='x', padx=10, pady=(0, 4))

        Label(
            filter_frame,
            text="🏭 Proveedor:",
            font=FONT_STYLE
        ).pack(side=LEFT, padx=(5, 4))

        self.combo_proveedor = ttk.Combobox(
            filter_frame,
            font=FONT_STYLE,
            width=35,
            state="readonly"
        )
        self.combo_proveedor.pack(side=LEFT, padx=(0, 6))
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._filtrar_proveedor())

        Button(
            filter_frame,
            text="✖ Limpiar",
            font=FONT_STYLE,
            bg="#e53935",
            fg="white",
            width=10,
            command=self._limpiar_filtro_proveedor
        ).pack(side=LEFT, padx=2)

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
        # ✅ CORREGIDO: Orden de columnas consistente
        # ============================================================
        frame_tabla = Frame(self.window)
        frame_tabla.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # ✅ DEFINICIÓN CORRECTA DE COLUMNAS (orden específico)
        columnas = (
            "id_producto",
            "codigo_barras",
            "descripcion",
            "cantidad",
            "proveedor",
            "precio_compra",
            "precio_venta",
            "unidad",
            "impuesto",
            "bonificacion",
            "grupo",
            "subgrupo",
            "fecha_vencimiento"
        )

        # Crear Treeview
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

        # ✅ Configurar encabezados con nombres legibles
        nombres_columnas = {
            "id_producto": "ID",
            "codigo_barras": "Código",
            "descripcion": "Descripción",
            "cantidad": "Cantidad",
            "proveedor": "Proveedor",
            "precio_compra": "P. Compra",
            "precio_venta": "P. Venta",
            "unidad": "UND",
            "impuesto": "Impuesto",
            "bonificacion": "Boni",
            "grupo": "Grupo",
            "subgrupo": "Subgrupo",
            "fecha_vencimiento": "Vencimiento"
        }

        # ✅ Anchos optimizados
        anchos_columnas = {
            "id_producto": 60,
            "codigo_barras": 100,
            "descripcion": 290,
            "cantidad": 70,
            "proveedor": 150,
            "precio_compra": 90,
            "precio_venta": 90,
            "unidad": 50,
            "impuesto": 80,
            "bonificacion": 60,
            "grupo": 120,
            "subgrupo": 120,
            "fecha_vencimiento": 100
        }

        for col in columnas:
            self.tree.heading(
                col,
                text=nombres_columnas.get(col, col),
                command=lambda _col=col: self._ordenar_columna(_col)
            )
            self.tree.column(
                col,
                width=anchos_columnas.get(col, 100),
                anchor='w'
            )

        # Scrollbar vertical
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
        self.tree.bind("<MouseWheel>", self._scroll_mouse)
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))

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
        # Solo agregar opción de reset si el usuario es admin
        if AuthManager and AuthManager.es_admin():
            self.menu_contextual.add_command(
                label="⚠️ Resetear TODO el stock a 0 (admin)",
                command=self._resetear_stock
            )

        self.tree.bind("<Button-3>", self._mostrar_menu_contextual)

    def _cargar_productos(self):
        """
        ✅ CORREGIDO: Carga productos con SELECT en el orden correcto,
        respetando el filtro de proveedor activo.
        """
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Proveedor seleccionado desde el Combobox
        proveedor_sel = None
        val = self.combo_proveedor.get()
        if val and val != "(Todos los proveedores)":
            proveedor_sel = val

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                if proveedor_sel:
                    cursor.execute("""
                        SELECT
                            id_producto, codigo_barras, descripcion, cantidad,
                            proveedor, precio_compra, precio_venta, unidad,
                            impuesto, bonificacion, grupo, subgrupo, fecha_vencimiento
                        FROM productos
                        WHERE TRIM(proveedor) = TRIM(?)
                        ORDER BY id_producto
                    """, (proveedor_sel,))
                else:
                    cursor.execute("""
                        SELECT
                            id_producto, codigo_barras, descripcion, cantidad,
                            proveedor, precio_compra, precio_venta, unidad,
                            impuesto, bonificacion, grupo, subgrupo, fecha_vencimiento
                        FROM productos
                        ORDER BY id_producto
                    """)

                productos = cursor.fetchall()

                for producto in productos:
                    self.tree.insert("", "end", values=tuple(producto))

                logging.info(f"Cargados {len(productos)} productos en inventario")

        except Exception as e:
            logging.error(f"Error al cargar productos: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al cargar inventario:\n{e}")

        # Actualizar total
        self._actualizar_total()
    def _buscar(self):
        """Busca productos por texto, combinando con el filtro de proveedor activo."""
        consulta = self.search_entry.get().strip().lower()

        # Si no hay texto, recarga respetando el filtro de proveedor
        if not consulta:
            self._cargar_productos()
            return

        # Proveedor seleccionado desde el Combobox
        proveedor_sel = None
        val = self.combo_proveedor.get()
        if val and val != "(Todos los proveedores)":
            proveedor_sel = val

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                params = [f"%{consulta}%"] * 5

                if proveedor_sel:
                    _SELECT = """
                        SELECT
                            id_producto, codigo_barras, descripcion, cantidad,
                            proveedor, precio_compra, precio_venta, unidad,
                            impuesto, bonificacion, grupo, subgrupo, fecha_vencimiento
                        FROM productos
                        WHERE (
                            LOWER(codigo_barras) LIKE ?
                            OR LOWER(descripcion) LIKE ?
                            OR LOWER(proveedor)   LIKE ?
                            OR LOWER(grupo)       LIKE ?
                            OR LOWER(subgrupo)    LIKE ?
                        )
                        AND TRIM(LOWER(proveedor)) = TRIM(LOWER(?))
                    """
                    params.append(proveedor_sel)
                else:
                    _SELECT = """
                        SELECT
                            id_producto, codigo_barras, descripcion, cantidad,
                            proveedor, precio_compra, precio_venta, unidad,
                            impuesto, bonificacion, grupo, subgrupo, fecha_vencimiento
                        FROM productos
                        WHERE (
                            LOWER(codigo_barras) LIKE ?
                            OR LOWER(descripcion) LIKE ?
                            OR LOWER(proveedor)   LIKE ?
                            OR LOWER(grupo)       LIKE ?
                            OR LOWER(subgrupo)    LIKE ?
                        )
                    """

                cursor.execute(_SELECT, params)
                resultados = cursor.fetchall()

                for item in self.tree.get_children():
                    self.tree.delete(item)

                for producto in resultados:
                    self.tree.insert("", "end", values=tuple(producto))

                if not resultados:
                    messagebox.showinfo("Sin resultados", "No se encontraron productos")

        except Exception as e:
            logging.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error en búsqueda: {e}")
    def _cargar_proveedores(self):
        """Carga la lista de proveedores únicos desde la BD y puebla el Combobox."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT TRIM(proveedor)
                    FROM productos
                    WHERE proveedor IS NOT NULL AND TRIM(proveedor) != ''
                    ORDER BY TRIM(proveedor) ASC
                """)
                proveedores = ["(Todos los proveedores)"] + [r[0] for r in cursor.fetchall()]
            self.combo_proveedor["values"] = proveedores
            self.combo_proveedor.set("(Todos los proveedores)")
        except Exception as e:
            logging.error(f"Error al cargar proveedores: {e}")

    def _filtrar_proveedor(self):
        """Aplica el filtro de proveedor y recarga la tabla."""
        # Si hay texto en el buscador, relanza la búsqueda combinada
        if self.search_entry.get().strip():
            self._buscar()
        else:
            self._cargar_productos()

    def _limpiar_filtro_proveedor(self):
        """Resetea el filtro de proveedor y muestra todos los productos."""
        self.combo_proveedor.set("(Todos los proveedores)")
        self._cargar_productos()

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

        # ✅ Lista de columnas en el orden correcto
        columnas = [
            "id_producto",
            "codigo_barras",
            "descripcion",
            "cantidad",
            "proveedor",
            "precio_compra",
            "precio_venta",
            "unidad",
            "impuesto",
            "bonificacion",
            "grupo",
            "subgrupo",
            "fecha_vencimiento"
        ]

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
                # ✅ FRACCIÓN: acepta decimales (0.2, 1.5, 0.333...)
                try:
                    val_float = float(str(nuevo_valor).replace(',', '.'))
                    if val_float < 0:
                        raise ValueError
                    nuevo_valor = str(int(val_float)) if val_float == int(val_float) else str(round(val_float, 6))
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        "Cantidad inválida.\nUse números como: 1, 0.5, 0.2, 1.333"
                    )
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
        Resetea todo el stock a 0.
        Requiere: rol admin + contrasena del admin verificada contra la BD.
        """
        import sqlite3 as _sq3

        # Verificar rol
        if not AuthManager or not AuthManager.es_admin():
            messagebox.showerror(
                "Acceso denegado",
                "Solo el administrador puede resetear el stock.",
                parent=self.window
            )
            return

        # Dialogo de confirmacion + contrasena
        dlg = Toplevel(self.window)
        dlg.title("Resetear Stock — Confirmacion Admin")
        dlg.geometry("400x260")
        dlg.resizable(False, False)
        dlg.transient(self.window)
        dlg.grab_set()

        Frame(dlg, bg="#b71c1c", height=6).pack(fill="x")

        Label(
            dlg,
            text="⚠️  Resetear TODO el Stock a 0",
            font=("Segoe UI", 14, "bold"),
            fg="#b71c1c"
        ).pack(pady=(14, 4))

        Label(
            dlg,
            text="Esta accion pondra en 0 la cantidad de TODOS\n"
                 "los productos. No se puede deshacer.\n"
                 "Se recomienda hacer un backup antes.",
            font=("Segoe UI", 10),
            fg="#555555",
            justify="center"
        ).pack(pady=(0, 12))

        Label(
            dlg,
            text="Contrasena de administrador:",
            font=FONT_STYLE
        ).pack()

        entry_pass = Entry(dlg, show="*", font=FONT_STYLE, width=20, justify="center")
        entry_pass.pack(pady=(4, 14))
        entry_pass.focus()

        frame_btns = Frame(dlg)
        frame_btns.pack()

        def _confirmar():
            pwd = entry_pass.get()
            if not pwd:
                messagebox.showerror("Error", "Ingresa la contrasena.", parent=dlg)
                return

            # Verificar contra BD (mismo hash bcrypt del login)
            try:
                from config.settings import DB_PATH
                conn = _sq3.connect(str(DB_PATH))
                conn.row_factory = _sq3.Row
                usuario = AuthManager.usuario_actual()
                row = conn.execute(
                    "SELECT password_hash FROM usuarios WHERE username=? AND rol='admin'",
                    (usuario.get("username", "admin"),)
                ).fetchone()
                conn.close()

                if not row:
                    messagebox.showerror("Error", "Usuario admin no encontrado.", parent=dlg)
                    return

                if not bcrypt.checkpw(pwd.encode(), row["password_hash"].encode()):
                    messagebox.showerror("Acceso denegado", "Contrasena incorrecta.", parent=dlg)
                    entry_pass.delete(0, END)
                    entry_pass.focus()
                    return

            except Exception as e:
                logging.error(f"Error verificando contrasena reset stock: {e}")
                messagebox.showerror("Error", f"No se pudo verificar:\n{e}", parent=dlg)
                return

            dlg.destroy()

            # Confirmacion final
            if not messagebox.askyesno(
                "Ultima confirmacion",
                "¿Esta SEGURO de resetear TODO el stock a 0?\n\n"
                "Esta accion NO se puede deshacer.",
                parent=self.window
            ):
                return

            if DatabaseManager.resetear_stock():
                self._cargar_productos()
                logging.warning(
                    f"RESET_STOCK | Usuario: {AuthManager.usuario_actual().get('username')} | "
                    "Todo el stock reseteado a 0."
                )
                messagebox.showinfo(
                    "Exito",
                    "Todo el stock ha sido reseteado a 0 correctamente.",
                    parent=self.window
                )
            else:
                messagebox.showerror("Error", "No se pudo resetear el stock.", parent=self.window)

        Button(
            frame_btns,
            text="Confirmar Reset",
            font=FONT_STYLE,
            bg="#b71c1c", fg="white",
            command=_confirmar,
            width=16
        ).pack(side="left", padx=8)

        Button(
            frame_btns,
            text="Cancelar",
            font=FONT_STYLE,
            bg="#546e7a", fg="white",
            command=dlg.destroy,
            width=10
        ).pack(side="left", padx=8)

        entry_pass.bind("<Return>", lambda e: _confirmar())
        entry_pass.bind("<Escape>", lambda e: dlg.destroy())


    def _mostrar_menu_contextual(self, event):
        """Muestra menú contextual en clic derecho"""
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
        Exporta inventario completo a Excel conservando estructura del modelo

        Estructura: 19 columnas en el orden del archivo modelo
        - Centro, Proveedor, Material, Denominación, Lote, UND, Cantidad,
          Venta Real, Venta Cte, Impuesto, $Marcado, % Boni, Fecha Creación,
          Catalogo, Grupo, SubGrupo, Plazo 2, Plazo 3, EAN
        """
        try:
            import pandas as pd
            from datetime import datetime
            from tkinter import filedialog, messagebox
            from models.database import get_db_connection
            import logging

            # Obtener productos de la base de datos
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT 
                        id_producto,
                        codigo_barras,
                        descripcion,
                        cantidad,
                        proveedor,
                        precio_compra,
                        precio_venta,
                        unidad,
                        impuesto,
                        bonificacion,
                        grupo,
                        subgrupo,
                        fecha_vencimiento
                    FROM productos
                    ORDER BY id_producto
                """)

                productos = cursor.fetchall()

            if not productos:
                messagebox.showwarning(
                    "Inventario Vacío",
                    "No hay productos en el inventario para exportar."
                )
                return

            # Solicitar ubicación de guardado
            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialfile="inventario_exportado.xlsx"
            )

            if not ruta:
                return

            # Preparar datos con la estructura del modelo
            datos_exportar = []
            fecha_actual = datetime.now().strftime("%Y%m%d")  # Formato YYYYMMDD

            for producto in productos:
                # Extraer valores del producto
                id_prod = producto[0]
                codigo_barras = producto[1] or ""
                descripcion = producto[2] or ""
                cantidad = producto[3] or 0
                proveedor = producto[4] or ""
                precio_compra = producto[5] or 0
                precio_venta = producto[6] or 0
                unidad = producto[7] or "UN"
                impuesto = producto[8] or "0%  Exento"
                bonificacion = producto[9] or 0.0
                grupo = producto[10] or ""
                subgrupo = producto[11] or ""
                # fecha_vencimiento = producto[12]  # No se usa en el Excel modelo

                # Construir fila con EXACTAMENTE el orden del modelo
                fila = {
                    'Centro': 8100.0,  # Valor fijo del modelo
                    'Proveedor': proveedor,
                    'Material': float(id_prod) if id_prod else 0.0,
                    'Denominación': descripcion,
                    'Lote': 'NORMAL_0',  # Valor por defecto del modelo
                    'UND': unidad,
                    'Cantidad': int(cantidad),
                    'Venta Real': int(precio_compra),  # El modelo usa enteros
                    'Venta Cte': int(precio_venta),  # El modelo usa enteros
                    'Impuesto': impuesto,
                    '$Marcado': 0.0,  # Valor por defecto
                    '% Boni': float(bonificacion),
                    'Fecha Creación': float(fecha_actual),  # Como número YYYYMMDD
                    'Catalogo': 'ETICOS',  # Valor por defecto del modelo
                    'Grupo': grupo,
                    'SubGrupo': subgrupo,
                    'Plazo 2': '',  # Vacío por defecto
                    'Plazo 3': '',  # Vacío por defecto
                    'EAN': codigo_barras
                }

                datos_exportar.append(fila)

            # Crear DataFrame con el orden exacto de columnas del modelo
            columnas_orden = [
                'Centro',
                'Proveedor',
                'Material',
                'Denominación',
                'Lote',
                'UND',
                'Cantidad',
                'Venta Real',
                'Venta Cte',
                'Impuesto',
                '$Marcado',
                '% Boni',
                'Fecha Creación',
                'Catalogo',
                'Grupo',
                'SubGrupo',
                'Plazo 2',
                'Plazo 3',
                'EAN'
            ]

            df = pd.DataFrame(datos_exportar, columns=columnas_orden)

            # Exportar a Excel
            df.to_excel(ruta, index=False, sheet_name="Sheet1", engine='openpyxl')

            messagebox.showinfo(
                "✅ Exportación Exitosa",
                f"Inventario exportado correctamente con formato modelo:\n\n"
                f"{ruta}\n\n"
                f"Total productos exportados: {len(productos)}\n"
                f"Columnas: {len(columnas_orden)}"
            )

            logging.info(f"Inventario exportado: {len(productos)} productos a {ruta}")

        except Exception as e:
            logging.error(f"Error al exportar a Excel: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def _actualizar_desde_excel(self):
        """
        Actualiza inventario desde archivo Excel

        Compatible con:
        - Archivo modelo (19 columnas con EAN, Denominación, Venta Real, etc.)
        - Archivos .xls (antiguos) y .xlsx (modernos)

        El método delega el trabajo pesado al InventarioController
        """
        from tkinter import filedialog, messagebox, Toplevel, Label
        from tkinter import ttk
        from controllers.inventario import InventarioController

        # Seleccionar archivo
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo Excel con precios",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )

        if not archivo:
            return

        # Ventana de progreso
        ventana_progreso = Toplevel(self.window)
        ventana_progreso.title("Procesando...")
        ventana_progreso.geometry("400x150")
        ventana_progreso.transient(self.window)
        ventana_progreso.grab_set()

        Label(
            ventana_progreso,
            text="Procesando archivo Excel...\n\nPor favor espere, esto puede tomar unos momentos.",
            font=FONT_STYLE,
            justify="center"
        ).pack(pady=20)

        # Barra de progreso
        progress = ttk.Progressbar(
            ventana_progreso,
            mode='indeterminate',
            length=300
        )
        progress.pack(pady=10)
        progress.start(10)

        # Forzar actualización de la ventana
        ventana_progreso.update()

        # Procesar archivo en segundo plano
        def procesar():
            try:
                # Llamar al controlador para procesar el archivo
                actualizados, insertados, errores = InventarioController.actualizar_producto_desde_excel(archivo)

                # Cerrar ventana de progreso
                progress.stop()
                ventana_progreso.destroy()

                # Recargar productos en la tabla
                if actualizados > 0 or insertados > 0:
                    self._cargar_productos()

            except Exception as e:
                progress.stop()
                ventana_progreso.destroy()
                messagebox.showerror("Error", f"Error al procesar archivo:\n{e}")
                import logging
                logging.error(f"Error en _actualizar_desde_excel: {e}", exc_info=True)

        # Ejecutar después de un pequeño delay para que la ventana se muestre
        self.window.after(100, procesar)

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

        entry_busqueda.bind("<Return>", lambda e: entry_compra.focus())
        entry_compra.bind("<Return>", lambda e: entry_venta.focus())
        entry_venta.bind("<Return>", lambda e: ejecutar())

    def _on_close(self):
        """Maneja el cierre de la ventana"""
        self.window.destroy()