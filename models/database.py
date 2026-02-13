"""
Capa de acceso a datos con gestión segura de conexiones
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple, Dict, Any
from config.settings import DB_PATH

# Configurar logging
logging.basicConfig(
    filename='logs/farmatrack.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
                return cursor.fetchall()
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
                return cursor.fetchall()
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
        """Resetea todo el stock a 0 (requiere confirmación externa)"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE productos SET cantidad = 0")
                return True
        except sqlite3.Error as e:
            logging.error(f"Error al resetear stock: {e}")
            return False

    @staticmethod
    def actualizar_precios_desde_lista(actualizaciones: List[Tuple[str, float, float]]) -> Tuple[int, int]:
        """
        Actualiza precios de múltiples productos desde una lista
        Returns: (actualizados, insertados)
        """
        actualizados = 0
        insertados = 0

        try:
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

                return (actualizados, insertados)
        except sqlite3.Error as e:
            logging.error(f"Error en actualización masiva: {e}")
            return (0, 0)


# Función de compatibilidad con código antiguo
def conectar_db():
    """Función legacy - usar get_db_connection() en su lugar"""
    return sqlite3.connect(str(DB_PATH))