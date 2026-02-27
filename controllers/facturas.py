"""
Controlador de Programación de Pago de Facturas
FarmaTrack - Droguería Irlandesa

Gestión completa de facturas por pagar:
  - CRUD de facturas
  - Clasificación por estado y vencimiento
  - Proyección de flujo de caja
  - Estadísticas por proveedor
  - Filtros por rango de fechas
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config.settings import DB_PATH


class FacturasController:
    """Controlador de lógica de negocio para facturas por pagar"""

    # ══════════════════════════════════════════════════════════════════════════
    # INICIALIZACIÓN DE TABLA
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def inicializar_tabla():
        """Crea la tabla facturas_pago si no existe. Seguro de llamar múltiples veces."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS facturas_pago (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_factura        TEXT    NOT NULL,
                    proveedor         TEXT    NOT NULL,
                    valor             REAL    NOT NULL DEFAULT 0,
                    fecha_vencimiento TEXT    NOT NULL,
                    estado            TEXT    NOT NULL DEFAULT 'pendiente',
                    metodo_pago       TEXT    DEFAULT '',
                    observaciones     TEXT    DEFAULT '',
                    fecha_creacion    TEXT    DEFAULT '',
                    fecha_pago        TEXT    DEFAULT ''
                )
            """)

            # Migraciones de seguridad
            cur.execute("PRAGMA table_info(facturas_pago)")
            cols = {r[1] for r in cur.fetchall()}
            if "metodo_pago" not in cols:
                cur.execute("ALTER TABLE facturas_pago ADD COLUMN metodo_pago TEXT DEFAULT ''")
            if "observaciones" not in cols:
                cur.execute("ALTER TABLE facturas_pago ADD COLUMN observaciones TEXT DEFAULT ''")
            if "fecha_creacion" not in cols:
                cur.execute("ALTER TABLE facturas_pago ADD COLUMN fecha_creacion TEXT DEFAULT ''")
            if "fecha_pago" not in cols:
                cur.execute("ALTER TABLE facturas_pago ADD COLUMN fecha_pago TEXT DEFAULT ''")

            conn.commit()
            conn.close()
            logging.info("Tabla facturas_pago inicializada correctamente.")
        except Exception as e:
            logging.error(f"Error inicializando tabla facturas_pago: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def agregar_factura(datos: Dict[str, Any]) -> bool:
        """Agrega una nueva factura al sistema."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO facturas_pago
                    (id_factura, proveedor, valor, fecha_vencimiento,
                     estado, metodo_pago, observaciones, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos['id_factura'],
                datos['proveedor'],
                float(datos['valor']),
                datos['fecha_vencimiento'],
                datos.get('estado', 'pendiente'),
                datos.get('metodo_pago', ''),
                datos.get('observaciones', ''),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))
            conn.commit()
            conn.close()
            logging.info(f"Factura agregada: {datos['id_factura']} - {datos['proveedor']}")
            return True
        except Exception as e:
            logging.error(f"Error agregando factura: {e}")
            return False

    @staticmethod
    def eliminar_factura(row_id: int) -> bool:
        """Elimina una factura por su ID interno (rowid)."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("DELETE FROM facturas_pago WHERE id = ?", (row_id,))
            ok = cur.rowcount > 0
            conn.commit()
            conn.close()
            if ok:
                logging.info(f"Factura eliminada: row_id={row_id}")
            return ok
        except Exception as e:
            logging.error(f"Error eliminando factura: {e}")
            return False

    @staticmethod
    def marcar_como_pagada(row_id: int, metodo: str = "") -> bool:
        """Marca una factura como pagada."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("""
                UPDATE facturas_pago
                SET estado = 'pagada',
                    fecha_pago = ?,
                    metodo_pago = CASE WHEN ? != '' THEN ? ELSE metodo_pago END
                WHERE id = ?
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                metodo, metodo,
                row_id,
            ))
            ok = cur.rowcount > 0
            conn.commit()
            conn.close()
            return ok
        except Exception as e:
            logging.error(f"Error marcando factura como pagada: {e}")
            return False

    @staticmethod
    def actualizar_fecha_vencimiento(row_id: int, nueva_fecha: str) -> bool:
        """Actualiza la fecha de vencimiento de una factura."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute(
                "UPDATE facturas_pago SET fecha_vencimiento = ? WHERE id = ?",
                (nueva_fecha, row_id)
            )
            ok = cur.rowcount > 0
            conn.commit()
            conn.close()
            return ok
        except Exception as e:
            logging.error(f"Error actualizando fecha: {e}")
            return False

    @staticmethod
    def actualizar_estado_automatico():
        """
        Revisa todas las facturas pendientes y marca como 'vencida'
        las que ya pasaron su fecha de vencimiento.
        """
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("""
                UPDATE facturas_pago
                SET estado = 'vencida'
                WHERE estado = 'pendiente'
                  AND fecha_vencimiento < ?
            """, (hoy,))
            actualizadas = cur.rowcount
            conn.commit()
            conn.close()
            if actualizadas > 0:
                logging.info(f"Facturas vencidas actualizadas automáticamente: {actualizadas}")
            return actualizadas
        except Exception as e:
            logging.error(f"Error actualizando estados: {e}")
            return 0

    # ══════════════════════════════════════════════════════════════════════════
    # CONSULTAS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def obtener_todas(filtro: str = "todas", fecha_desde: str = "",
                      fecha_hasta: str = "") -> List[Dict[str, Any]]:
        """
        Obtiene facturas con filtros.
        filtro: 'todas', 'hoy', 'semana', 'mes', 'vencidas', 'pendientes', 'pagadas'
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row

            hoy = datetime.now()
            where_clauses = []
            params = []

            if filtro == "hoy":
                where_clauses.append("fecha_vencimiento = ?")
                params.append(hoy.strftime("%Y-%m-%d"))
            elif filtro == "semana":
                inicio = hoy.strftime("%Y-%m-%d")
                fin = (hoy + timedelta(days=7)).strftime("%Y-%m-%d")
                where_clauses.append("fecha_vencimiento BETWEEN ? AND ?")
                params.extend([inicio, fin])
            elif filtro == "mes":
                inicio = hoy.strftime("%Y-%m-%d")
                fin = (hoy + timedelta(days=30)).strftime("%Y-%m-%d")
                where_clauses.append("fecha_vencimiento BETWEEN ? AND ?")
                params.extend([inicio, fin])
            elif filtro == "vencidas":
                where_clauses.append("estado = 'vencida'")
            elif filtro == "pendientes":
                where_clauses.append("estado = 'pendiente'")
            elif filtro == "pagadas":
                where_clauses.append("estado = 'pagada'")
            elif filtro == "rango" and fecha_desde and fecha_hasta:
                where_clauses.append("fecha_vencimiento BETWEEN ? AND ?")
                params.extend([fecha_desde, fecha_hasta])

            sql = "SELECT * FROM facturas_pago"
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            sql += " ORDER BY fecha_vencimiento ASC"

            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            conn.close()

            return [dict(r) for r in rows]
        except Exception as e:
            logging.error(f"Error obteniendo facturas: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════════
    # RESUMEN / KPIs
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def resumen_financiero() -> Dict[str, Any]:
        """Calcula KPIs del mini-dashboard financiero."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            hoy = datetime.now()
            hoy_str = hoy.strftime("%Y-%m-%d")

            # Total pendiente
            r = conn.execute(
                "SELECT COALESCE(SUM(valor), 0) FROM facturas_pago WHERE estado = 'pendiente'"
            ).fetchone()
            total_pendiente = r[0]

            # Total vencido
            r = conn.execute(
                "SELECT COALESCE(SUM(valor), 0) FROM facturas_pago WHERE estado = 'vencida'"
            ).fetchone()
            total_vencido = r[0]

            # Total programado esta semana
            fin_semana = (hoy + timedelta(days=7)).strftime("%Y-%m-%d")
            r = conn.execute("""
                SELECT COALESCE(SUM(valor), 0) FROM facturas_pago
                WHERE estado IN ('pendiente', 'vencida')
                  AND fecha_vencimiento BETWEEN ? AND ?
            """, (hoy_str, fin_semana)).fetchone()
            total_semana = r[0]

            # Total del mes
            fin_mes = (hoy + timedelta(days=30)).strftime("%Y-%m-%d")
            r = conn.execute("""
                SELECT COALESCE(SUM(valor), 0) FROM facturas_pago
                WHERE estado IN ('pendiente', 'vencida')
                  AND fecha_vencimiento BETWEEN ? AND ?
            """, (hoy_str, fin_mes)).fetchone()
            total_mes = r[0]

            conn.close()
            return {
                "total_pendiente": total_pendiente,
                "total_vencido":   total_vencido,
                "total_semana":    total_semana,
                "total_mes":       total_mes,
            }
        except Exception as e:
            logging.error(f"Error calculando resumen financiero: {e}")
            return {
                "total_pendiente": 0, "total_vencido": 0,
                "total_semana": 0, "total_mes": 0,
            }

    # ══════════════════════════════════════════════════════════════════════════
    # PROYECCIÓN DE FLUJO DE CAJA
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def proyeccion_flujo_caja() -> Dict[str, float]:
        """Total a pagar en los próximos 7, 15 y 30 días."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            hoy = datetime.now()
            hoy_str = hoy.strftime("%Y-%m-%d")

            resultado = {}
            for dias, clave in [(7, "7_dias"), (15, "15_dias"), (30, "30_dias")]:
                fin = (hoy + timedelta(days=dias)).strftime("%Y-%m-%d")
                r = conn.execute("""
                    SELECT COALESCE(SUM(valor), 0) FROM facturas_pago
                    WHERE estado IN ('pendiente', 'vencida')
                      AND fecha_vencimiento BETWEEN ? AND ?
                """, (hoy_str, fin)).fetchone()
                resultado[clave] = r[0]

            conn.close()
            return resultado
        except Exception as e:
            logging.error(f"Error proyección flujo caja: {e}")
            return {"7_dias": 0, "15_dias": 0, "30_dias": 0}

    # ══════════════════════════════════════════════════════════════════════════
    # ESTADÍSTICAS POR PROVEEDOR
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def estadisticas_proveedores() -> List[Dict[str, Any]]:
        """
        Retorna estadísticas agrupadas por proveedor:
        - Total acumulado (pendiente + vencido)
        - Cantidad de facturas
        - Promedio por factura
        - Total histórico pagado
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT
                    proveedor,
                    COUNT(*)                                                AS total_facturas,
                    COALESCE(SUM(CASE WHEN estado != 'pagada' THEN valor ELSE 0 END), 0)
                                                                            AS deuda_activa,
                    COALESCE(SUM(CASE WHEN estado  = 'pagada' THEN valor ELSE 0 END), 0)
                                                                            AS total_pagado,
                    COALESCE(AVG(valor), 0)                                 AS promedio_factura,
                    COALESCE(SUM(valor), 0)                                 AS monto_total
                FROM facturas_pago
                GROUP BY proveedor
                ORDER BY deuda_activa DESC
            """).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logging.error(f"Error estadísticas proveedores: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def clasificar_factura(fecha_vencimiento: str, estado: str) -> str:
        """
        Retorna la clasificación visual de la factura:
        'pagada', 'vencida', 'urgente' (≤3 días), 'ok' (>7 días), 'proxima' (4-7 días)
        """
        if estado == "pagada":
            return "pagada"

        try:
            fv = datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
            hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            dias = (fv - hoy).days

            if dias < 0:
                return "vencida"
            elif dias <= 3:
                return "urgente"
            elif dias <= 7:
                return "proxima"
            else:
                return "ok"
        except Exception:
            return "ok"