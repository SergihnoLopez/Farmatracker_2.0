"""
Ventana para agregar nuevos productos
"""
from tkinter import Toplevel, Frame, Label, Entry, Button, W, END
from tkinter import ttk
try:
    from tkcalendar import Calendar as _Calendar
    _TKCAL_OK = True
except ImportError:
    _TKCAL_OK = False
from tkinter import messagebox
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from controllers.inventario import InventarioController


class AgregarProductoWindow:
    """Ventana para agregar productos al inventario"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Agregar Producto")
        self.window.state("zoomed")
        self.window.grab_set()

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

            if campo == "impuesto":
                # Combobox con opciones fijas de impuesto
                entrada = ttk.Combobox(
                    self.window,
                    font=FONT_STYLE,
                    width=38,
                    state="readonly",
                    values=["0%  Exento", "19%  IVA"]
                )
                entrada.set("0%  Exento")  # valor por defecto
                entrada.grid(row=i, column=1, padx=10, pady=5, sticky=W)
                self.entradas[campo] = entrada

            elif campo == "fecha_vencimiento":
                # Entry + botón 📅 para abrir calendar
                frame_fecha = Frame(self.window)
                frame_fecha.grid(row=i, column=1, padx=10, pady=5, sticky=W)
                entrada = Entry(frame_fecha, font=FONT_STYLE, width=33)
                entrada.pack(side="left")
                Button(
                    frame_fecha, text="📅", font=FONT_STYLE,
                    command=lambda e=entrada: self._abrir_datepicker(e)
                ).pack(side="left", padx=(4, 0))
                self.entradas[campo] = entrada

            else:
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

    def _abrir_datepicker(self, entry_destino):
        """Abre un popup con calendario para seleccionar fecha."""
        if not _TKCAL_OK:
            from tkinter import messagebox as _mb
            _mb.showwarning(
                "tkcalendar no instalado",
                "Instala la dependencia con:\n  pip install tkcalendar\n\n"
                "Mientras tanto puedes escribir la fecha manualmente (YYYY-MM-DD).",
                parent=self.window
            )
            return

        popup = Toplevel(self.window)
        popup.title("Seleccionar fecha")
        popup.grab_set()
        popup.resizable(False, False)

        # Intentar pre-seleccionar fecha actual del entry
        from datetime import date as _date
        try:
            fecha_ini = datetime.strptime(entry_destino.get().strip(), "%Y-%m-%d").date()
        except Exception:
            fecha_ini = _date.today()

        cal = _Calendar(
            popup,
            selectmode="day",
            year=fecha_ini.year,
            month=fecha_ini.month,
            day=fecha_ini.day,
            date_pattern="yyyy-mm-dd",
            locale="es_CO",
        )
        cal.pack(padx=10, pady=10)

        def _confirmar():
            fecha = cal.get_date()
            entry_destino.delete(0, END)
            entry_destino.insert(0, fecha)
            popup.destroy()

        Button(popup, text="✔ Confirmar", font=FONT_STYLE,
               bg="#4CAF50", fg="white", command=_confirmar).pack(pady=(0, 10))

    def _guardar_producto(self):
        """Guarda el producto"""
        datos = {campo: entrada.get().strip() for campo, entrada in self.entradas.items()}

        if InventarioController.agregar_producto(datos):
            # Limpiar campos
            for entrada in self.entradas.values():
                entrada.delete(0, END)

            self.entradas['codigo_barras'].focus()
