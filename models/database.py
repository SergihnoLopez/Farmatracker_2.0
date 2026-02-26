"""
Capa de acceso a datos con gestión segura de conexiones
MEJORADO: Incluye sistema de backups automáticos antes de operaciones críticas
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple, Dict, Any
from config.settings import DB_PATH

# Configurar logging
import os
import logging

# 📌 Ruta base del proyecto (carpeta raíz)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 📌 Carpeta logs en la raíz
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 📌 Crear carpeta logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "farmatrack.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones a la base de datos"""
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logging.error(f"Error de base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()


class DatabaseManager:
    """Gestor centralizado de operaciones de base de datos"""

    @staticmethod
    def inicializar_tablas():
        """
        Crea todas las tablas necesarias si no existen.
        Seguro de llamar en cada arranque: no borra datos existentes.
        """
        import sqlite3 as _sq3
        try:
            conn = _sq3.connect(str(DB_PATH))
            cur  = conn.cursor()

            # ── Tabla productos ───────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id_producto      INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras    TEXT UNIQUE NOT NULL,
                    descripcion      TEXT,
                    proveedor        TEXT,
                    unidad           TEXT,
                    cantidad         REAL    DEFAULT 0,
                    precio_compra    REAL    DEFAULT 0,
                    precio_venta     REAL    DEFAULT 0,
                    impuesto         TEXT,
                    bonificacion     REAL    DEFAULT 0,
                    grupo            TEXT,
                    subgrupo         TEXT,
                    fecha_vencimiento TEXT
                )
            """)

            # ── Tabla ventas ──────────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id_venta  INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha     TEXT    NOT NULL DEFAULT '',
                    total     REAL    NOT NULL DEFAULT 0,
                    productos TEXT,
                    cajero    TEXT    DEFAULT 'Principal'
                )
            """)

            # ── Migraciones de seguridad (columnas faltantes) ─────────────
            cur.execute("PRAGMA table_info(ventas)")
            cols_ventas = {r[1] for r in cur.fetchall()}
            if "fecha"  not in cols_ventas:
                cur.execute("ALTER TABLE ventas ADD COLUMN fecha TEXT NOT NULL DEFAULT ''")
                logging.info("Migración: columna 'fecha' agregada a ventas")
            if "cajero" not in cols_ventas:
                cur.execute("ALTER TABLE ventas ADD COLUMN cajero TEXT DEFAULT 'Principal'")
                logging.info("Migración: columna 'cajero' agregada a ventas")

            cur.execute("PRAGMA table_info(productos)")
            cols_prod = {r[1] for r in cur.fetchall()}
            if "unidad" not in cols_prod:
                cur.execute("ALTER TABLE productos ADD COLUMN unidad TEXT")
                logging.info("Migración: columna 'unidad' agregada a productos")
            if "bonificacion" not in cols_prod:
                cur.execute("ALTER TABLE productos ADD COLUMN bonificacion REAL DEFAULT 0")
                logging.info("Migración: columna 'bonificacion' agregada a productos")
            if "grupo" not in cols_prod:
                cur.execute("ALTER TABLE productos ADD COLUMN grupo TEXT")
                logging.info("Migración: columna 'grupo' agregada a productos")
            if "subgrupo" not in cols_prod:
                cur.execute("ALTER TABLE productos ADD COLUMN subgrupo TEXT")
                logging.info("Migración: columna 'subgrupo' agregada a productos")

            conn.commit()
            conn.close()
            logging.info("Base de datos inicializada correctamente.")

        except Exception as e:
            logging.error(f"Error al inicializar tablas: {e}", exc_info=True)

    @staticmethod
    def buscar_producto_por_codigo(codigo: str) -> Optional[Dict[str, Any]]:
        """Busca un producto por código de barras"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT id_producto, codigo_barras, descripcion, cantidad, 
                       precio_compra, precio_venta, impuesto, fecha_vencimiento
                       FROM productos WHERE codigo_barras = ?""",
                    (codigo,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Error al buscar producto: {e}")
            return None

    @staticmethod
    def buscar_productos_like(texto: str, limit: int = 80) -> List[Tuple]:
        """Busca productos por coincidencia parcial"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT codigo_barras, descripcion 
                       FROM productos 
                       WHERE descripcion LIKE ? OR codigo_barras LIKE ? 
                       LIMIT ?""",
                    (f"%{texto}%", f"%{texto}%", limit)
                )
                # Convertir Row objects a tuplas simples
                rows = cursor.fetchall()
                return [tuple(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error en búsqueda: {e}")
            return []

    @staticmethod
    def actualizar_cantidad(id_producto: int, nueva_cantidad: int) -> bool:
        """Actualiza la cantidad de un producto"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE productos SET cantidad = ? WHERE id_producto = ?",
                    (nueva_cantidad, id_producto)
                )
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al actualizar cantidad: {e}")
            return False

    @staticmethod
    def insertar_producto(datos: Dict[str, Any]) -> bool:
        """Inserta un nuevo producto"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO productos 
                    (codigo_barras, descripcion, proveedor, unidad, cantidad,
                     precio_compra, precio_venta, impuesto, bonificacion, 
                     grupo, subgrupo, fecha_vencimiento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datos['codigo_barras'],
                    datos['descripcion'],
                    datos.get('proveedor', ''),
                    datos.get('unidad', ''),
                    datos.get('cantidad', 0),
                    datos.get('precio_compra', 0),
                    datos.get('precio_venta', 0),
                    datos.get('impuesto', ''),
                    datos.get('bonificacion', 0),
                    datos.get('grupo', ''),
                    datos.get('subgrupo', ''),
                    datos.get('fecha_vencimiento', '')
                ))
                return True
        except sqlite3.Error as e:
            logging.error(f"Error al insertar producto: {e}")
            return False

    @staticmethod
    def actualizar_campo_producto(id_producto: int, campo: str, valor: Any) -> bool:
        """Actualiza un campo específico de un producto (con validación)"""
        from utils.validators import sanitize_sql_column

        campo_seguro = sanitize_sql_column(campo)
        if not campo_seguro:
            logging.warning(f"Intento de actualizar columna no permitida: {campo}")
            return False

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = f"UPDATE productos SET {campo_seguro} = ? WHERE id_producto = ?"
                cursor.execute(query, (valor, id_producto))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al actualizar campo: {e}")
            return False

    @staticmethod
    def eliminar_producto(id_producto: int) -> bool:
        """Elimina un producto"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM productos WHERE id_producto = ?", (id_producto,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al eliminar producto: {e}")
            return False

    @staticmethod
    def obtener_todos_productos() -> List[Tuple]:
        """Obtiene todos los productos (usar con paginación en producción)"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM productos")
                # Convertir Row objects a tuplas simples
                rows = cursor.fetchall()
                return [tuple(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error al obtener productos: {e}")
            return []

    @staticmethod
    def calcular_valor_inventario() -> float:
        """Calcula el valor total del inventario"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cantidad, precio_compra, impuesto 
                    FROM productos
                """)

                total = 0.0
                for row in cursor.fetchall():
                    cantidad = row[0] or 0
                    precio = row[1] or 0
                    impuesto = row[2] or ""

                    # Aplicar IVA si corresponde
                    if "19" in str(impuesto).lower() and "iva" in str(impuesto).lower():
                        precio *= 1.19

                    total += cantidad * precio

                return total
        except sqlite3.Error as e:
            logging.error(f"Error al calcular inventario: {e}")
            return 0.0

    @staticmethod
    def resetear_stock() -> bool:
        """
        Resetea todo el stock a 0 (requiere confirmación externa)
        ✅ MEJORADO: Crea backup automático antes de ejecutar
        """
        try:
            # 🔒 BACKUP AUTOMÁTICO ANTES DE OPERACIÓN CRÍTICA
            from utils.backup import backup_antes_operacion_critica

            backup_path = backup_antes_operacion_critica("reseteo_stock")

            if not backup_path:
                logging.error("No se pudo crear backup, operación cancelada")
                return False

            logging.info(f"Backup creado antes de reseteo: {backup_path}")

            # Ejecutar operación
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE productos SET cantidad = 0")

            logging.info("Stock reseteado exitosamente")
            return True

        except sqlite3.Error as e:
            logging.error(f"Error al resetear stock: {e}")
            return False

    @staticmethod
    def actualizar_precios_desde_lista(actualizaciones: List[Tuple[str, float, float]]) -> Tuple[int, int]:
        """
        Actualiza precios de múltiples productos desde una lista
        ✅ MEJORADO: Crea backup automático antes de actualización masiva
        Returns: (actualizados, insertados)
        """
        actualizados = 0
        insertados = 0

        try:
            # 🔒 BACKUP AUTOMÁTICO ANTES DE OPERACIÓN MASIVA
            from utils.backup import backup_antes_operacion_critica

            backup_path = backup_antes_operacion_critica("actualizacion_masiva_precios")

            if not backup_path:
                logging.warning("No se pudo crear backup, continuando con precaución")
            else:
                logging.info(f"Backup creado antes de actualización masiva: {backup_path}")

            # Ejecutar actualización
            with get_db_connection() as conn:
                cursor = conn.cursor()

                for codigo, precio_compra, bonificacion in actualizaciones:
                    cursor.execute(
                        "SELECT id_producto FROM productos WHERE codigo_barras = ?",
                        (codigo,)
                    )

                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE productos SET precio_compra = ?, bonificacion = ? WHERE codigo_barras = ?",
                            (precio_compra, bonificacion, codigo)
                        )
                        actualizados += 1
                    else:
                        cursor.execute("""
                            INSERT INTO productos 
                            (codigo_barras, cantidad, precio_compra, bonificacion)
                            VALUES (?, 0, ?, ?)
                        """, (codigo, precio_compra, bonificacion))
                        insertados += 1

                logging.info(f"Actualización masiva completada: {actualizados} actualizados, {insertados} insertados")
                return (actualizados, insertados)

        except sqlite3.Error as e:
            logging.error(f"Error en actualización masiva: {e}")
            return (0, 0)


# Función de compatibilidad con código antiguo
def conectar_db():
    """Función legacy - usar get_db_connection() en su lugar"""
    return sqlite3.connect(str(DB_PATH))