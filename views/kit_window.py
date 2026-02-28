"""
Kit Window v5 – Sugerencias predictivas y cálculos en tiempo real.
- Sugerencias: Frame sobre _filas_frame (evita problemas de grab_set y Canvas z-order)
- Cálculos: KeyRelease en entry_uds y entry_cant (sin StringVar/trace)
- Sin textvariable en entry_prod para evitar búsquedas al cargar descripción
"""
from __future__ import annotations

import json
import logging
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from tkinter import (
    Toplevel, Frame, Label, Entry, Button, Listbox, Scrollbar,
    messagebox, END, Canvas
)
import tkinter as tk

from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from models.database import DatabaseManager


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_dec(v) -> Decimal:
    try:
        return Decimal(str(v))
    except InvalidOperation:
        return Decimal("0")


def _fmt(v) -> str:
    try:
        return f"${int(round(float(v))):,}".replace(",", ".")
    except Exception:
        return "$0"


# ── KitRow ────────────────────────────────────────────────────────────────────

class KitRow:

    def __init__(self, parent: Frame, index: int, on_remove,
                 kw: "KitWindow"):
        self.index        = index
        self.on_remove    = on_remove
        self.kw           = kw
        self.producto_data: dict | None = None
        self.uds_caja     = Decimal("1")
        self._resultados: list = []
        self._lb_frame: Frame | None = None
        self._lb: Listbox | None = None
        self._cargando: bool = False

        # ── Contenedor externo ────────────────────────────────────────────────
        self.outer = Frame(parent, bd=1, relief="groove", bg="#f4f6f9")
        self.outer.pack(fill="x", padx=10, pady=4)

        # ══ FILA A ═══════════════════════════════════════════════════════════
        rowA = Frame(self.outer, bg="#f4f6f9")
        rowA.pack(fill="x", padx=6, pady=(6, 2))

        Label(rowA, text=f"#{index+1}",
              font=("Arial", 11, "bold"), bg="#f4f6f9",
              fg="#003B8E", width=3).pack(side="left")

        Label(rowA, text="Producto:",
              font=("Arial", 10), bg="#f4f6f9").pack(side="left", padx=(4, 2))

        # SIN textvariable — Entry directo para evitar que .insert() dispare búsqueda
        self.entry_prod = Entry(rowA, font=FONT_STYLE, width=40)
        self.entry_prod.pack(side="left", padx=4)

        self.lbl_stock = Label(rowA, text="Stock: —",
                               font=("Arial", 10), fg="#007700",
                               bg="#f4f6f9", width=22, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)

        Button(rowA, text="✕ Quitar",
               font=("Arial", 9), bg="#f44336", fg="white",
               command=lambda: self.on_remove(self)).pack(side="right", padx=4)

        # ══ FILA B ═══════════════════════════════════════════════════════════
        rowB = Frame(self.outer, bg="#e8edf3")
        rowB.pack(fill="x", padx=6, pady=(2, 6))

        Label(rowB, text="   ", bg="#e8edf3", width=3).pack(side="left")

        Label(rowB, text="Uds/caja:",
              font=("Arial", 10), bg="#e8edf3").pack(side="left", padx=(10, 2))
        # SIN StringVar/trace — KeyRelease es suficiente y más confiable
        self.entry_uds = Entry(rowB, font=FONT_STYLE, width=6,
                               justify="center", bg="white")
        self.entry_uds.insert(0, "1")
        self.entry_uds.pack(side="left", padx=2)

        Label(rowB, text="Cant. uds:",
              font=("Arial", 10), bg="#e8edf3").pack(side="left", padx=(14, 2))
        self.entry_cant = Entry(rowB, font=FONT_STYLE, width=7,
                                justify="center", bg="white")
        self.entry_cant.pack(side="left", padx=2)

        self.lbl_desc = Label(rowB, text="  Desc: —",
                              font=("Arial", 10), fg="#880000",
                              bg="#e8edf3", width=30, anchor="w")
        self.lbl_desc.pack(side="left", padx=10)

        self.lbl_costo = Label(rowB, text="Costo: $0",
                               font=("Arial", 10, "bold"), fg="#003B8E",
                               bg="#e8edf3", width=18, anchor="w")
        self.lbl_costo.pack(side="left", padx=4)

        # ── Bindings ──────────────────────────────────────────────────────────
        self.entry_prod.bind("<KeyRelease>", self._on_prod_keyrelease)
        self.entry_prod.bind("<Return>",     self._on_enter_prod)
        self.entry_prod.bind("<Down>",       self._bajar_lista)
        self.entry_prod.bind("<Up>",         self._subir_lista)
        self.entry_prod.bind("<Escape>",     lambda e: self._cerrar_lista())

        self.entry_uds.bind("<KeyRelease>",  lambda e: self._recalc_and_update())
        self.entry_uds.bind("<Return>",      lambda e: self.entry_cant.focus())

        self.entry_cant.bind("<KeyRelease>", lambda e: self._recalc_and_update())
        self.entry_cant.bind("<Return>",     lambda e: self.kw._foco_siguiente(self))

    # ── Sugerencias ───────────────────────────────────────────────────────────

    def _on_prod_keyrelease(self, event):
        """Busca sugerencias al escribir."""
        if event.keysym in ("Return", "Up", "Down", "Escape", "Tab"):
            return
        if self._cargando:
            return
        texto = self.entry_prod.get().strip()
        if not texto:
            self._cerrar_lista()
            return
        try:
            res = DatabaseManager.buscar_productos_like(texto, limit=50)
            # Solo mostrar productos con stock > 0
            res = [r for r in res if float(r[2]) > 0] if res else []
        except Exception:
            res = []
        self._resultados = res
        if res:
            self._abrir_lista(res)
        else:
            self._cerrar_lista()

    def _abrir_lista(self, res: list):
        """
        Lista de sugerencias como Frame colocado sobre _filas_frame.
        Al ser hijo del mismo Frame del Canvas, tiene el z-order correcto
        y no se ve afectado por grab_set() de la ventana principal.
        """
        self._cerrar_lista()
        parent = self.kw._filas_frame
        parent.update_idletasks()

        # Coordenadas relativas a _filas_frame
        ex = self.entry_prod.winfo_rootx() - parent.winfo_rootx()
        ey = (self.entry_prod.winfo_rooty() - parent.winfo_rooty()
              + self.entry_prod.winfo_height())
        ew = max(self.entry_prod.winfo_width(), 580)

        container = Frame(parent, bd=2, relief="solid", bg="white")
        container.place(x=ex, y=ey, width=ew)
        container.lift()

        sb = Scrollbar(container, orient="vertical")
        lb = Listbox(container,
                     font=("Arial", 11),
                     height=min(len(res), 8),
                     yscrollcommand=sb.set,
                     selectbackground="#003B8E",
                     selectforeground="white",
                     bg="white",
                     activestyle="dotbox",
                     exportselection=False)
        sb.config(command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)

        for item in res:
            cod, desc = item[0], item[1]
            try:
                sv = float(item[2]) if item[2] is not None else 0.0
                ss = str(int(sv)) if sv == int(sv) else f"{sv:.4f}"
            except Exception:
                ss = "0"
            lb.insert(END, f"{cod}  ·  {desc}  (Stock: {ss})")

        if lb.size() > 0:
            lb.selection_set(0)
            lb.activate(0)

        lb.bind("<ButtonRelease-1>", lambda e, l=lb: self._seleccionar(l))
        lb.bind("<Return>",          lambda e, l=lb: self._seleccionar(l))
        lb.bind("<Escape>",          lambda e: self._cerrar_lista())

        self._lb_frame = container
        self._lb = lb

    def _cerrar_lista(self):
        if self._lb_frame:
            try:
                self._lb_frame.place_forget()
                self._lb_frame.destroy()
            except Exception:
                pass
        self._lb_frame = None
        self._lb = None

    def _bajar_lista(self, event):
        if not self._lb:
            return
        sel = self._lb.curselection()
        nxt = (sel[0] + 1) if sel else 0
        if nxt < self._lb.size():
            self._lb.selection_clear(0, END)
            self._lb.selection_set(nxt)
            self._lb.activate(nxt)
            self._lb.see(nxt)
        return "break"

    def _subir_lista(self, event):
        if not self._lb:
            return
        sel = self._lb.curselection()
        if sel and sel[0] > 0:
            nxt = sel[0] - 1
            self._lb.selection_clear(0, END)
            self._lb.selection_set(nxt)
            self._lb.activate(nxt)
            self._lb.see(nxt)
        return "break"

    def _seleccionar(self, lb: Listbox | None = None):
        lb = lb or self._lb
        if not lb:
            return
        sel = lb.curselection()
        if not sel:
            return
        codigo = self._resultados[sel[0]][0]
        self._cerrar_lista()
        self._cargar_producto(codigo)
        self.entry_uds.focus()

    def _on_enter_prod(self, event):
        if self._lb:
            self._seleccionar()
        else:
            codigo = self.entry_prod.get().strip()
            if codigo:
                self._cargar_producto(codigo)

    def _cargar_producto(self, codigo: str):
        prod = DatabaseManager.buscar_producto_por_codigo(codigo)
        if not prod:
            rs = DatabaseManager.buscar_productos_like(codigo, limit=1)
            if rs:
                prod = DatabaseManager.buscar_producto_por_codigo(rs[0][0])
        if not prod:
            messagebox.showwarning("No encontrado",
                                   f"Producto '{codigo}' no encontrado.",
                                   parent=self.kw.window)
            return

        self.producto_data = prod

        # Escribir descripción sin activar la búsqueda de sugerencias
        self._cargando = True
        self.entry_prod.delete(0, END)
        self.entry_prod.insert(0, prod["descripcion"])
        self._cargando = False

        try:
            sv = float(prod["cantidad"])
            ss = str(int(sv)) if sv == int(sv) else f"{sv:.4f}"
        except Exception:
            ss = "?"
        self.lbl_stock.config(text=f"Stock: {ss} cajas")

        self._recalc()
        self.kw._actualizar_totales()

    # ── Cálculo inmediato ─────────────────────────────────────────────────────

    def _recalc_and_update(self):
        """Recalcula y actualiza totales. Llamado por KeyRelease."""
        self._recalc()
        self.kw._actualizar_totales()

    def _recalc(self):
        if not self.producto_data:
            self.lbl_desc.config(text="  ← seleccione producto", fg="#888")
            self.lbl_costo.config(text="Costo: $0")
            return

        try:
            uds_raw = self.entry_uds.get().strip().replace(",", ".")
            uds = _to_dec(uds_raw) if uds_raw else Decimal("1")
            if uds <= 0:
                uds = Decimal("1")
        except Exception:
            uds = Decimal("1")
        self.uds_caja = uds

        cant_str = self.entry_cant.get().strip().replace(",", ".")
        if not cant_str:
            self.lbl_desc.config(text="  ← ingrese cantidad", fg="#888")
            self.lbl_costo.config(text="Costo: $0")
            return

        try:
            cant = _to_dec(cant_str)
            if cant <= 0:
                raise ValueError
        except Exception:
            self.lbl_desc.config(text="  ⚠ cantidad inválida", fg="#cc0000")
            self.lbl_costo.config(text="Costo: $0")
            return

        desc      = cant / uds
        stock_act = _to_dec(str(self.producto_data.get("cantidad", 0)))
        ok        = stock_act >= desc
        color     = "#007700" if ok else "#cc0000"
        icono     = "✓" if ok else "✗ INSUF."

        desc_s = f"{desc:.6f}".rstrip("0").rstrip(".")
        self.lbl_desc.config(
            text=f"  Desc: {desc_s} cajas  {icono}", fg=color)

        precio     = _to_dec(str(self.producto_data.get("precio_venta", 0)))
        costo_prop = precio * desc
        self.lbl_costo.config(text=f"Costo: {_fmt(costo_prop)}")

    # ── datos públicos ────────────────────────────────────────────────────────

    def get_descuento(self) -> Decimal | None:
        if not self.producto_data:
            return None
        cant_str = self.entry_cant.get().strip().replace(",", ".")
        if not cant_str:
            return None
        try:
            cant = _to_dec(cant_str)
            if cant <= 0:
                return None
            return cant / self.uds_caja
        except Exception:
            return None

    def get_costo_prop(self) -> Decimal:
        d = self.get_descuento()
        if d is None or not self.producto_data:
            return Decimal("0")
        return _to_dec(str(self.producto_data.get("precio_venta", 0))) * d

    def is_valid(self) -> tuple[bool, str]:
        if not self.producto_data:
            return False, f"Fila #{self.index+1}: Sin producto."
        d = self.get_descuento()
        if d is None:
            return False, f"Fila #{self.index+1}: Cantidad vacía o inválida."
        stock = _to_dec(str(self.producto_data.get("cantidad", 0)))
        if stock < d:
            return (False,
                    f"«{self.producto_data['descripcion']}»\n"
                    f"  Disponible: {float(stock):.4f}  "
                    f"Requerido: {float(d):.6f} cajas")
        return True, ""

    def destroy(self):
        self._cerrar_lista()
        self.outer.destroy()


# ── KitWindow ─────────────────────────────────────────────────────────────────

class KitWindow:

    def __init__(self, parent_venta):
        self.parent = parent_venta
        self.window = Toplevel(parent_venta.window)
        self.window.title("🧪  Armar Kit")
        self.window.geometry("1100x620")
        self.window.resizable(True, True)
        self.window.transient(parent_venta.window)
        self.window.grab_set()

        self._filas: list[KitRow] = []
        self._precio_override: Decimal = Decimal("4000")

        self._build_ui()
        self._nueva_fila()
        self._nueva_fila()
        self._nueva_fila()
        self._actualizar_totales()   # mostrar precio por defecto $4.000 al abrir

        # Cerrar sugerencias al hacer clic fuera
        self.window.bind("<Button-1>", self._click_fuera, add="+")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # encabezado
        hdr = Frame(self.window, bg="#003B8E", pady=8)
        hdr.pack(fill="x")
        Label(hdr, text="🧪  ARMAR KIT PERSONALIZADO",
              font=("Titillium Web", 14, "bold"),
              bg="#003B8E", fg="white").pack()
        Label(hdr,
              text="Busque cada producto · ingrese Uds/caja (cuántas unidades trae la caja) "
                   "· Cant.uds (cuántas usar) · Mínimo 2 productos",
              font=("Arial", 9), bg="#003B8E", fg="#aaddff").pack()

        # ── área de filas (scrollable) ────────────────────────────────────────
        wrap = Frame(self.window)
        wrap.pack(fill="both", expand=True)

        self._canvas = Canvas(wrap, bd=0, highlightthickness=0, bg="#eef2f7")
        vsb = Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._filas_frame = Frame(self._canvas, bg="#eef2f7")
        self._canvas_win  = self._canvas.create_window(
            (0, 0), window=self._filas_frame, anchor="nw")

        self._filas_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(
                self._canvas_win, width=e.width))

        # ── panel inferior ────────────────────────────────────────────────────
        bot = Frame(self.window, bd=1, relief="ridge",
                    pady=8, bg="#dde3ed")
        bot.pack(fill="x", side="bottom")

        tot = Frame(bot, bg="#dde3ed")
        tot.pack()

        Label(tot, text="Costo base:",
              font=("Titillium Web", 11), bg="#dde3ed").grid(
            row=0, column=0, padx=10, sticky="e")
        self.lbl_costo = Label(tot, text="$0",
                               font=("Titillium Web", 13, "bold"),
                               fg="#003B8E", bg="#dde3ed")
        self.lbl_costo.grid(row=0, column=1, padx=4, sticky="w")

        Label(tot, text="Precio venta:",
              font=("Titillium Web", 11), bg="#dde3ed").grid(
            row=0, column=2, padx=10, sticky="e")
        self.lbl_precio = Label(tot, text="$0",
                                font=("Titillium Web", 15, "bold"),
                                fg="#880000", bg="#dde3ed",
                                cursor="hand2", relief="groove", padx=10)
        self.lbl_precio.grid(row=0, column=3, padx=4, sticky="w")
        self.lbl_precio.bind("<Double-1>", self._editar_precio)
        Label(tot, text="(doble clic para editar)",
              font=("Arial", 8), fg="#666", bg="#dde3ed").grid(
            row=1, column=3, sticky="w")

        self.lbl_util = Label(tot, text="Utilidad: $0  (0%)",
                              font=("Arial", 10, "bold"),
                              fg="#007700", bg="#dde3ed")
        self.lbl_util.grid(row=0, column=4, padx=20)

        # botones
        btns = Frame(bot, bg="#dde3ed")
        btns.pack(pady=6)

        Button(btns, text="➕  Agregar Producto",
               font=FONT_STYLE, bg="#1565C0", fg="white", width=20,
               command=self._nueva_fila).pack(side="left", padx=8)

        Button(btns, text="✅  Confirmar Kit",
               font=("Titillium Web", 12, "bold"),
               bg="#2e7d32", fg="white", width=20,
               command=self._confirmar).pack(side="left", padx=8)

        Button(btns, text="✕  Cancelar",
               font=FONT_STYLE, bg="#f44336", fg="white", width=14,
               command=self.window.destroy).pack(side="left", padx=8)

    # ── filas ─────────────────────────────────────────────────────────────────

    def _nueva_fila(self):
        idx  = len(self._filas)
        fila = KitRow(self._filas_frame, idx, self._eliminar_fila, self)
        self._filas.append(fila)
        self.window.after(80, lambda: self._canvas.yview_moveto(1.0))
        fila.entry_prod.focus()

    def _eliminar_fila(self, fila: KitRow):
        if len(self._filas) <= 2:
            messagebox.showwarning("Mínimo 2",
                                   "El kit requiere al menos 2 productos.",
                                   parent=self.window)
            return
        fila.destroy()
        self._filas.remove(fila)
        for i, f in enumerate(self._filas):
            f.index = i
        self._actualizar_totales()

    def _foco_siguiente(self, fila: KitRow):
        try:
            idx = self._filas.index(fila)
        except ValueError:
            return
        if idx + 1 < len(self._filas):
            self._filas[idx + 1].entry_prod.focus()

    def _click_fuera(self, event):
        def _check():
            for f in self._filas:
                if not f._lb_frame:
                    continue
                try:
                    w = event.widget
                    while w is not None:
                        if w is f._lb_frame or w is f.entry_prod:
                            return
                        w = getattr(w, "master", None)
                    f._cerrar_lista()
                except Exception:
                    f._cerrar_lista()
        self.window.after(150, _check)

    # ── totales ───────────────────────────────────────────────────────────────

    def _actualizar_totales(self):
        costo  = sum(f.get_costo_prop() for f in self._filas)
        precio = (self._precio_override
                  if self._precio_override is not None else costo)

        self.lbl_costo.config(text=_fmt(costo))
        self.lbl_precio.config(text=_fmt(precio))

        util  = precio - costo
        pct   = (util / precio * 100) if precio > 0 else Decimal("0")
        color = "#007700" if util >= 0 else "#cc0000"
        self.lbl_util.config(
            text=f"Utilidad: {_fmt(util)}  ({float(pct):.1f}%)",
            fg=color)

    # ── editar precio ─────────────────────────────────────────────────────────

    def _editar_precio(self, event=None):
        top = Toplevel(self.window)
        top.title("Editar precio del kit")
        top.geometry("300x110")
        top.resizable(False, False)
        top.transient(self.window)
        top.grab_set()

        Label(top, text="Precio de venta ($):", font=FONT_STYLE).pack(pady=8)
        ent = Entry(top, font=("Titillium Web", 14, "bold"),
                    justify="center", width=14)
        ent.pack()
        actual = (self._precio_override
                  or sum(f.get_costo_prop() for f in self._filas))
        ent.insert(0, str(int(round(float(actual)))))
        ent.select_range(0, END)
        ent.focus()

        def ok(e=None):
            raw = ent.get().strip().replace(".", "").replace(",", "")
            try:
                v = _to_dec(raw)
                if v < 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Error", "Precio inválido.", parent=top)
                return
            self._precio_override = v
            self._actualizar_totales()
            top.destroy()

        ent.bind("<Return>", ok)
        Button(top, text="✔ Aceptar", font=FONT_STYLE,
               bg="#2e7d32", fg="white", command=ok).pack(pady=6)

    # ── confirmar ─────────────────────────────────────────────────────────────

    def _confirmar(self):
        filas = [f for f in self._filas if f.producto_data]

        if len(filas) < 2:
            messagebox.showerror("Kit incompleto",
                                 "Seleccione al menos 2 productos.",
                                 parent=self.window)
            return

        errores = []
        for f in filas:
            ok, msg = f.is_valid()
            if not ok:
                errores.append(msg)
        if errores:
            messagebox.showerror(
                "Stock insuficiente",
                "\n\n".join(errores),
                parent=self.window)
            return

        costo_total  = sum(f.get_costo_prop() for f in filas)
        precio_final = (self._precio_override
                        if self._precio_override is not None
                        else costo_total)
        utilidad     = precio_final - costo_total
        n            = len(filas)
        util_x_prod  = utilidad / n

        # ── Construir detalles del kit sin tocar la BD ───────────────────────
        # El inventario se descuenta y la venta se registra SOLO cuando el
        # cajero presione "Registrar Venta". Aquí solo preparamos la fila
        # del treeview con toda la información necesaria en kit_data.
        detalles = []
        for f in filas:
            d  = f.get_descuento()
            d6 = float(d.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
            cp = f.get_costo_prop()
            pp = cp + util_x_prod
            detalles.append({
                "codigo":            f.producto_data["codigo_barras"],
                "descripcion":       f.producto_data["descripcion"],
                "unidades_usadas":   float(_to_dec(f.entry_cant.get())),
                "unidades_por_caja": float(f.uds_caja),
                "descuento_cajas":   d6,
                "costo_prop":        round(float(cp), 2),
                "utilidad_asig":     round(float(util_x_prod), 2),
                "precio_interno":    round(float(pp), 2),
            })

        nombres         = " + ".join(d["descripcion"][:18] for d in detalles)
        kit_payload_str = json.dumps(detalles, ensure_ascii=False)

        self.parent.tree.insert("", END, values=(
            "KIT",
            f"🧪 KIT  [{nombres}]",
            1,
            float(precio_final),
            float(precio_final),
            "KIT",
            kit_payload_str))
        self.parent._actualizar_total()

        messagebox.showinfo("Kit agregado ✅",
                            f"Kit agregado a la venta.\n\n"
                            f"Productos: {n}\n"
                            f"Precio venta: {_fmt(precio_final)}\n"
                            f"Costo base:   {_fmt(costo_total)}\n"
                            f"Utilidad:     {_fmt(utilidad)}\n\n"
                            "Presione \"Registrar Venta\" para\n"
                            "confirmar y actualizar el inventario.",
                            parent=self.window)
        self.window.destroy()