"""
establecer_stock_50.py — FarmaTrack
Coloca cantidad = 50 en TODOS los productos del inventario.
Ejecutar desde la raiz del proyecto: python establecer_stock_50.py
"""
import sqlite3
import shutil
from datetime import datetime

# Importar DB_PATH igual que el resto del proyecto
from config.settings import DB_PATH

# ── Backup automático ─────────────────────────────────────────────────────────
ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB_PATH.with_name(DB_PATH.stem + f".bak_{ts}.db")
shutil.copy2(DB_PATH, bak)
print(f"💾  Backup: {bak.name}")

# ── Actualizar stock ──────────────────────────────────────────────────────────
conn = sqlite3.connect(str(DB_PATH))
cur  = conn.cursor()

cur.execute("UPDATE productos SET cantidad = 50")
n = cur.rowcount
conn.commit()
conn.close()

print(f"✅  {n} productos actualizados a stock = 50")