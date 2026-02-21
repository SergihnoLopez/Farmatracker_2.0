"""
Controller del Dashboard - FarmaTrack
Provee todas las métricas para el dashboard principal
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

try:
    from config.settings import DB_PATH
except ImportError:
    from pathlib import Path
    DB_PATH = Path("farma_pro_stocker.db")


class DashboardController:
    """Consultas optimizadas para el dashboard"""

    # Umbral de stock bajo
    STOCK_BAJO_UMBRAL = 5
    # Días para alertar vencimiento próximo
    DIAS_VENCIMIENTO_PROXIMO = 30

    @classmethod
    def ventas_hoy(cls) -> Dict[str, Any]:
        """Retorna total y cantidad de ventas del día"""
        hoy = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total), 0)
                    FROM ventas
                    WHERE fecha LIKE ?
                """, (f"{hoy}%",))
                count, total = cursor.fetchone()
                return {"cantidad": count or 0, "total": total or 0.0}
        except Exception as e:
            logging.error(f"Error ventas_hoy: {e}")
            return {"cantidad": 0, "total": 0.0}

    @classmethod
    def ventas_semana(cls) -> List[Dict]:
        """Ventas de los últimos 7 días (para mini gráfico)"""
        try:
            resultados = []
            with sqlite3.connect(str(DB_PATH)) as conn:
                for i in range(6, -1, -1):
                    dia = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                    cursor = conn.execute(
                        "SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha LIKE ?",
                        (f"{dia}%",)
                    )
                    total = cursor.fetchone()[0]
                    resultados.append({
                        "dia": (datetime.now() - timedelta(days=i)).strftime("%a"),
                        "total": total
                    })
            return resultados
        except Exception as e:
            logging.error(f"Error ventas_semana: {e}")
            return []

    @classmethod
    def productos_stock_bajo(cls) -> List[Dict]:
        """Productos con cantidad <= umbral"""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT codigo_barras, descripcion, cantidad, proveedor
                    FROM productos
                    WHERE cantidad <= ? AND cantidad >= 0
                    ORDER BY cantidad ASC
                    LIMIT 50
                """, (cls.STOCK_BAJO_UMBRAL,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logging.error(f"Error productos_stock_bajo: {e}")
            return []

    @classmethod
    def productos_por_vencer(cls) -> List[Dict]:
        """Productos que vencen en los próximos N días o ya vencidos"""
        hoy = datetime.now().date()
        limite = (hoy + timedelta(days=cls.DIAS_VENCIMIENTO_PROXIMO)).strftime("%Y-%m-%d")
        hoy_str = hoy.strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT codigo_barras, descripcion, cantidad,
                           fecha_vencimiento, proveedor
                    FROM productos
                    WHERE fecha_vencimiento IS NOT NULL
                      AND fecha_vencimiento != ''
                      AND fecha_vencimiento <= ?
                    ORDER BY fecha_vencimiento ASC
                    LIMIT 50
                """, (limite,)).fetchall()

                resultado = []
                for r in rows:
                    d = dict(r)
                    try:
                        fv = datetime.strptime(d["fecha_vencimiento"], "%Y-%m-%d").date()
                        dias_rest = (fv - hoy).days
                        d["dias_restantes"] = dias_rest
                        d["estado"] = (
                            "vencido" if dias_rest < 0
                            else "critico" if dias_rest <= 7
                            else "proximo"
                        )
                    except Exception:
                        d["dias_restantes"] = None
                        d["estado"] = "desconocido"
                    resultado.append(d)
                return resultado
        except Exception as e:
            logging.error(f"Error productos_por_vencer: {e}")
            return []

    @classmethod
    def valor_total_inventario(cls) -> Dict[str, float]:
        """Valor de compra y venta del inventario completo"""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute("""
                    SELECT
                        COALESCE(SUM(cantidad * precio_compra), 0),
                        COALESCE(SUM(cantidad * precio_venta), 0),
                        COUNT(*)
                    FROM productos
                    WHERE cantidad > 0
                """)
                costo, venta, total_prod = cursor.fetchone()
                return {
                    "valor_costo": costo,
                    "valor_venta": venta,
                    "ganancia_potencial": venta - costo,
                    "total_productos": total_prod,
                }
        except Exception as e:
            logging.error(f"Error valor_inventario: {e}")
            return {"valor_costo": 0, "valor_venta": 0, "ganancia_potencial": 0, "total_productos": 0}

    @classmethod
    def resumen_completo(cls) -> Dict[str, Any]:
        """Llama todos los métodos en una sola función para cargar el dashboard"""
        return {
            "ventas_hoy": cls.ventas_hoy(),
            "ventas_semana": cls.ventas_semana(),
            "stock_bajo": cls.productos_stock_bajo(),
            "por_vencer": cls.productos_por_vencer(),
            "inventario": cls.valor_total_inventario(),
        }