"""
Ventana de módulo de pedidos
"""
from tkinter import (Toplevel, Frame, Label, Entry, Button, Menu,
                     messagebox, END, W, BOTH, LEFT, RIGHT, Y)
from tkinter import ttk
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager, get_db_connection
from controllers.pedidos import PedidosController
from utils.formatters import format_precio_display


class PedidosWindow:
    """Ventana para gestión de pedidos"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Módulo de Pedidos")
        self.window.state("zoomed")

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz"""
        # Frame de búsqueda
        frame_busqueda = Frame(self.window)
        frame_busqueda.pack(pady=10)

        Label(frame_busqueda, text="Buscar producto:", font=FONT_STYLE).pack(side=LEFT, padx=5)

        self.entry_busqueda = Entry(frame_busqueda, font=FONT_STYLE)
        self.entry_busqueda.pack(side=LEFT, padx=5)
        self.entry_busqueda.bind("<Return>", lambda e: self._buscar_productos())

        Button(
            frame_busqueda,
            text="Buscar",
            command=self._buscar_productos,
            font=FONT_STYLE,
            bg=BTN_COLOR,
            fg=BTN_FG
        ).pack(side=LEFT, padx=5)

        # Treeview de productos disponibles
        Label(self.window, text="Productos Disponibles", font=("Titillium Web", 12, "bold")).pack(pady=5)

        columnas_productos = ("ID", "Código", "Descripción", "Stock", "Proveedor", "Precio Compra")
        self.tree_productos = ttk.Treeview(self.window, columns=columnas_productos, show="headings", height=10)

        for col in columnas_productos:
            self.tree_productos.heading(col, text=col)
            self.tree_productos.column(col, width=150, anchor="w")

        self.tree_productos.pack(pady=10, fill=BOTH, expand=True)

        # Frame cantidad
        frame_cantidad = Frame(self.window)
        frame_cantidad.pack(pady=5)

        Label(frame_cantidad, text="Cantidad a pedir:", font=FONT_STYLE).pack(side=LEFT, padx=5)

        self.entry_cantidad = Entry(frame_cantidad, font=FONT_STYLE, width=10)
        self.entry_cantidad.pack(side=LEFT)

        # Botones agregar/eliminar
        botones_frame = Frame(frame_cantidad)
        botones_frame.pack(side=LEFT, padx=10)

        Button(
            botones_frame,
            text="➕",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=3,
            command=self._agregar_a_pedido
        ).pack(side=LEFT, padx=4)

        Button(
            botones_frame,
            text="➖",
            font=("Arial", 14, "bold"),
            bg="#f44336",
            fg="white",
            width=3,
            command=self._eliminar_de_pedido
        ).pack(side=LEFT, padx=4)

        # Treeview de pedido
        Label(self.window, text="Productos en Pedido", font=("Titillium Web", 14, "bold")).pack(pady=5)

        columnas_pedido = ("Código", "Descripción", "Cantidad", "Precio Compra")
        self.tree_pedido = ttk.Treeview(self.window, columns=columnas_pedido, show="headings", height=10)

        for col in columnas_pedido:
            self.tree_pedido.heading(col, text=col)
            self.tree_pedido.column(col, width=200, anchor='w')

        self.tree_pedido.pack(pady=10, fill=BOTH, expand=True)

        # Label costo total
        self.label_costo_total = Label(
            self.window,
            text="Costo total: $0",
            font=("Titillium Web", 14, "bold"),
            fg="black"
        )
        self.label_costo_total.pack(pady=5)

        # Menú de opciones
        self._crear_menu_opciones()

    def _crear_menu_opciones(self):
        """Crea el menú de opciones (engranaje)"""
        self.menu_opciones = Menu(self.window, tearoff=0)
        self.menu_opciones.add_command(label="Cargar desde Excel (SIP)", command=self._cargar_desde_excel)
        self.menu_opciones.add_command(label="Cargar desde TXT", command=self._cargar_desde_txt)
        self.menu_opciones.add_separator()
        self.menu_opciones.add_command(label="Exportar a TXT", command=self._exportar_txt)
        self.menu_opciones.add_command(label="Exportar a Excel", command=self._exportar_excel)
        self.menu_opciones.add_command(label="Exportar a PDF", command=self._exportar_pdf)

        def mostrar_menu():
            try:
                self.menu_opciones.tk_popup(
                    self.boton_menu.winfo_rootx(),
                    self.boton_menu.winfo_rooty() + self.boton_menu.winfo_height()
                )
            finally:
                self.menu_opciones.grab_release()

        self.boton_menu = Button(
            self.window,
            text="⚙️",
            font=("Arial", 22, "bold"),
            bg="#8DCCF1",
            fg="black",
            width=3,
            height=1,
            command=mostrar_menu
        )
        self.boton_menu.pack(pady=10)

    def _buscar_productos(self):
        """Busca productos en el inventario"""
        consulta = self.entry_busqueda.get().strip().lower()

        if not consulta:
            messagebox.showwarning("Búsqueda vacía", "Ingresa una palabra clave")
            return

        # Limpiar treeview
        for item in self.tree_productos.get_children():
            self.tree_productos.delete(item)

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id_producto, codigo_barras, descripcion, cantidad, proveedor, precio_compra
                    FROM productos
                    WHERE LOWER(codigo_barras) LIKE ? 
                       OR LOWER(descripcion) LIKE ?
                       OR LOWER(proveedor) LIKE ?
                """, (f"%{consulta}%", f"%{consulta}%", f"%{consulta}%"))

                resultados = cursor.fetchall()

                if resultados:
                    for fila in resultados:
                        fila_lista = list(fila)
                        # Formatear precio
                        fila_lista[5] = format_precio_display(float(fila_lista[5]))
                        self.tree_productos.insert("", "end", values=fila_lista)
                else:
                    messagebox.showinfo("Sin resultados", "No se encontraron productos")

        except Exception as e:
            messagebox.showerror("Error", f"Error en búsqueda: {e}")

    def _agregar_a_pedido(self):
        """Agrega producto seleccionado al pedido"""
        selected = self.tree_productos.focus()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return

        cantidad = self.entry_cantidad.get()
        if not cantidad.isdigit() or int(cantidad) <= 0:
            messagebox.showerror("Error", "Ingrese una cantidad válida")
            return

        valores = self.tree_productos.item(selected, "values")
        codigo = valores[1]
        descripcion = valores[2]
        precio_str = valores[5]

        # Obtener precio real
        producto = DatabaseManager.buscar_producto_por_codigo(codigo)
        precio_compra = producto['precio_compra'] if producto else 0.0

        # Agregar a pedido
        self.tree_pedido.insert("", "end", values=(
            codigo,
            descripcion,
            cantidad,
            format_precio_display(precio_compra)
        ))

        self.entry_cantidad.delete(0, END)
        self._actualizar_costo_total()

    def _eliminar_de_pedido(self):
        """Elimina producto del pedido"""
        selected = self.tree_pedido.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto del pedido")
            return

        for item in selected:
            self.tree_pedido.delete(item)

        self._actualizar_costo_total()

    def _actualizar_costo_total(self):
        """Actualiza el costo total del pedido"""
        total = 0.0

        for item in self.tree_pedido.get_children():
            valores = self.tree_pedido.item(item, "values")
            cantidad = int(valores[2])
            precio_str = valores[3].replace('$', '').replace('.', '')

            try:
                precio = float(precio_str)
                total += precio * cantidad
            except:
                pass

        self.label_costo_total.config(text=f"Costo total: ${total:,.0f}".replace(",", "."))

    def _obtener_productos_pedido(self) -> list:
        """Obtiene lista de productos del pedido"""
        productos = []

        for item in self.tree_pedido.get_children():
            valores = self.tree_pedido.item(item, "values")
            precio_str = valores[3].replace('$', '').replace('.', '')

            productos.append({
                'codigo': valores[0],
                'descripcion': valores[1],
                'cantidad': valores[2],
                'precio_compra': float(precio_str)
            })

        return productos

    def _cargar_desde_excel(self):
        """Carga pedido desde Excel"""
        from tkinter import filedialog

        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )

        if not archivo:
            return

        productos = PedidosController.cargar_pedido_desde_excel(archivo)

        for prod in productos:
            self.tree_pedido.insert("", "end", values=(
                prod['codigo'],
                prod['descripcion'],
                prod['cantidad'],
                format_precio_display(prod['precio_compra'])
            ))

        self._actualizar_costo_total()
        messagebox.showinfo("Éxito", f"{len(productos)} productos cargados")

    def _cargar_desde_txt(self):
        """Carga pedido desde TXT"""
        from tkinter import filedialog

        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo TXT",
            filetypes=[("Archivos de texto", "*.txt")]
        )

        if not archivo:
            return

        productos = PedidosController.cargar_pedido_desde_txt(archivo)

        for prod in productos:
            self.tree_pedido.insert("", "end", values=(
                prod['codigo'],
                prod['descripcion'],
                prod['cantidad'],
                format_precio_display(prod['precio_compra'])
            ))

        self._actualizar_costo_total()
        messagebox.showinfo("Éxito", f"{len(productos)} productos cargados")

    def _exportar_pdf(self):
        """Exporta pedido a PDF"""
        productos = self._obtener_productos_pedido()
        PedidosController.exportar_pedido_pdf(productos)

    def _exportar_excel(self):
        """Exporta pedido a Excel"""
        productos = self._obtener_productos_pedido()
        PedidosController.exportar_pedido_excel(productos)

    def _exportar_txt(self):
        """Exporta pedido a TXT"""
        productos = self._obtener_productos_pedido()
        PedidosController.exportar_pedido_txt(productos)
