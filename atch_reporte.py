"""
patch_reporte.py — Parche para views/reporte_ventas_window.py
═══════════════════════════════════════════════════════════════
Cambios que aplica:

  1. Panel derecho de detalle: ancho 380 → 600 px
  2. Columnas del treeview de detalle: anchos ampliados
  3. _calcular_costo_venta: int(cantidad) → float(cantidad)
     ► Corrige la utilidad 100% al vender fracciones de CJ
  4. _mostrar_detalle: cantidades decimales visibles, descripción 30→40 chars

Ejecutar desde la raíz del proyecto:
    python patch_reporte.py
"""
import shutil, sys
from pathlib import Path

TARGET = Path("views/reporte_ventas_window.py")

if not TARGET.exists():
    print(f"❌  No se encontró {TARGET}")
    print("    Ejecuta este script desde la raíz del proyecto.")
    sys.exit(1)

shutil.copy(TARGET, TARGET.with_suffix(".py.bak"))
print("✅  Backup creado:", TARGET.with_suffix(".py.bak"))
print()

text = TARGET.read_text(encoding="utf-8")
errores = []

# ── Parche 1: ancho panel detalle 380 → 600 ──────────────────────────────────
old1 = 'frame = tk.Frame(parent, bg=Colors.SURFACE,\n                         relief="flat", bd=1, width=380)'
new1 = 'frame = tk.Frame(parent, bg=Colors.SURFACE,\n                         relief="flat", bd=1, width=600)'
if old1 in text:
    text = text.replace(old1, new1, 1)
    print("✅  Parche 1: panel detalle 380 → 600 px")
else:
    errores.append("PARCHE 1: en _setup_panel_detalle cambia  width=380  a  width=600")
    print("⚠️   Parche 1 no encontrado")

# ── Parche 2: columnas del detalle más anchas ─────────────────────────────────
old2 = ('        self.tree_det.column("descripcion", width=170, anchor="w")\n'
        '        self.tree_det.column("cant",        width=45,  anchor="center")\n'
        '        self.tree_det.column("precio",      width=78,  anchor="e")\n'
        '        self.tree_det.column("subtotal",    width=80,  anchor="e")')
new2 = ('        self.tree_det.column("descripcion", width=280, anchor="w")\n'
        '        self.tree_det.column("cant",        width=60,  anchor="center")\n'
        '        self.tree_det.column("precio",      width=110, anchor="e")\n'
        '        self.tree_det.column("subtotal",    width=110, anchor="e")')
if old2 in text:
    text = text.replace(old2, new2, 1)
    print("✅  Parche 2: columnas detalle 170/45/78/80 → 280/60/110/110")
else:
    errores.append("PARCHE 2: cambia los anchos de tree_det.column a 280, 60, 110, 110")
    print("⚠️   Parche 2 no encontrado")

# ── Parche 3: float(cantidad) en _calcular_costo_venta ───────────────────────
old3 = '                cantidad = int(prod.get("cantidad", 0))'
new3 = '                cantidad = float(prod.get("cantidad", 0))  # float: respeta fracciones CJ'
if old3 in text:
    text = text.replace(old3, new3, 1)
    print("✅  Parche 3: costo usa float(cantidad) — utilidad correcta con fracciones")
else:
    errores.append('PARCHE 3: en _calcular_costo_venta cambia  int(prod.get("cantidad",0))  a  float(...)')
    print("⚠️   Parche 3 no encontrado")

# ── Parche 4: mostrar decimales en el panel de detalle ───────────────────────
old4 = ('            self.tree_det.insert("", "end", values=(\n'
        '                str(prod.get("descripcion", ""))[:30],\n'
        '                prod.get("cantidad", 0),\n'
        '                _fmt(prod.get("precio_unitario", 0)),\n'
        '                _fmt(prod.get("subtotal", 0)),\n'
        '            ))')
new4 = ('            cant_raw = prod.get("cantidad", 0)\n'
        '            try:\n'
        '                cant_val = float(cant_raw)\n'
        '                cant_display = (\n'
        '                    str(int(cant_val)) if cant_val == int(cant_val)\n'
        '                    else f"{cant_val:.4f}".rstrip("0")\n'
        '                )\n'
        '            except Exception:\n'
        '                cant_display = str(cant_raw)\n'
        '            self.tree_det.insert("", "end", values=(\n'
        '                str(prod.get("descripcion", ""))[:40],\n'
        '                cant_display,\n'
        '                _fmt(prod.get("precio_unitario", 0)),\n'
        '                _fmt(prod.get("subtotal", 0)),\n'
        '            ))')
if old4 in text:
    text = text.replace(old4, new4, 1)
    print("✅  Parche 4: cantidad fraccionada visible en detalle")
else:
    errores.append("PARCHE 4: en _mostrar_detalle reemplaza el bloque tree_det.insert con la versión que usa cant_display")
    print("⚠️   Parche 4 no encontrado")

TARGET.write_text(text, encoding="utf-8")
print()
if errores:
    print("═"*60)
    print("  ⚠️  Aplica estos cambios manualmente:")
    print("═"*60)
    for i, e in enumerate(errores, 1):
        print(f"\n[{i}] {e}")
else:
    print("✅  Todos los parches aplicados. Reinicia FarmaTrack.")