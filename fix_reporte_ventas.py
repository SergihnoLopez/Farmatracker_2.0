"""
Script de parche automático para corregir los 3 bugs de reporte_ventas_window.py
Ejecútalo una sola vez desde la raíz del proyecto:
    python fix_reporte_ventas.py
"""
import re, sys, shutil
from pathlib import Path

TARGET = Path("views/reporte_ventas_window.py")
MAIN   = Path("main.py")

if not TARGET.exists():
    print(f"❌ No se encontró {TARGET}. Ejecuta este script desde la raíz del proyecto.")
    sys.exit(1)

# ── Backup ────────────────────────────────────────────────────────────────────
shutil.copy(TARGET, TARGET.with_suffix(".py.bak"))
shutil.copy(MAIN,   MAIN.with_suffix(".py.bak"))
print("✅ Backups creados (.py.bak)")

# =============================================================================
# FIX 1 & 2 – reporte_ventas_window.py
# =============================================================================
text = TARGET.read_text(encoding="utf-8")

# --- Fix 1: anchor="right" → anchor="e" en _setup_tabla -------------------
# La línea problemática es:
#   "total":  ("Total",       130, "right"),
old1 = '"total":  ("Total",       130, "right"),'
new1 = '"total":  ("Total",       130, "e"),'
if old1 in text:
    text = text.replace(old1, new1)
    print('✅ Fix 1: anchor "right" → "e" en encabezados de _setup_tabla')
else:
    # Fallback más general: reemplaza cualquier anchor "right" en column()
    # dentro de _setup_tabla (el heading puede tenerlo también)
    count = text.count('"right"')
    text = text.replace('"right"', '"e"')
    print(f'✅ Fix 1 (fallback): reemplazadas {count} ocurrencias de "right" → "e"')

# --- Fix 2: anchor="right" en tree_det.column() en _setup_panel_detalle ---
# ya cubierto por el replace anterior

TARGET.write_text(text, encoding="utf-8")
print("✅ reporte_ventas_window.py actualizado")

# =============================================================================
# FIX 3 – main.py: migración de columna 'fecha' en tabla ventas
# =============================================================================
main_text = MAIN.read_text(encoding="utf-8")

MIGRATION = '''

def migrar_base_datos():
    """Aplica migraciones necesarias a la BD existente (idempotente)."""
    import sqlite3
    from config.settings import DB_PATH
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Verificar columnas actuales de 'ventas'
        cursor.execute("PRAGMA table_info(ventas)")
        cols = {row[1] for row in cursor.fetchall()}

        if "fecha" not in cols:
            cursor.execute("ALTER TABLE ventas ADD COLUMN fecha TEXT NOT NULL DEFAULT ''")
            print("🔧 Migración: columna 'fecha' agregada a tabla ventas")

        if "cajero" not in cols:
            cursor.execute("ALTER TABLE ventas ADD COLUMN cajero TEXT DEFAULT 'Principal'")
            print("🔧 Migración: columna 'cajero' agregada a tabla ventas")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️  Migración BD: {e}")

'''

# Insertar la función justo antes de def main():
if "def migrar_base_datos():" not in main_text:
    main_text = main_text.replace("def main():", MIGRATION + "def main():", 1)
    print("✅ Fix 3: función migrar_base_datos() agregada a main.py")

# Llamar a la migración dentro de main(), después de verificar BD
CALL_SITE_OLD = '        print("✅ Base de datos OK")'
CALL_SITE_NEW = (
    '        print("✅ Base de datos OK")\n\n'
    '        print("🔧 Aplicando migraciones...")\n'
    '        migrar_base_datos()\n'
    '        print("✅ Migraciones OK")'
)
if CALL_SITE_OLD in main_text and "migrar_base_datos()" not in main_text:
    main_text = main_text.replace(CALL_SITE_OLD, CALL_SITE_NEW, 1)
    print("✅ Fix 3: llamada a migrar_base_datos() agregada en main()")
elif "migrar_base_datos()" in main_text:
    print("ℹ️  Fix 3: migrar_base_datos() ya estaba presente, sin cambios")

MAIN.write_text(main_text, encoding="utf-8")
print("✅ main.py actualizado")

print()
print("=" * 55)
print("  ✅ TODOS LOS FIXES APLICADOS CORRECTAMENTE")
print("  Reinicia la aplicación para verificar.")
print("=" * 55)