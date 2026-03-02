"""
Sistema de respaldo automático de base de datos
Gestiona backups manuales, automáticos y restauración
"""
import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from config.settings import DB_PATH, BASE_DIR


class BackupManager:
    """Gestor de respaldos de base de datos"""

    # Directorio de backups
    BACKUP_DIR = BASE_DIR / "backups"

    # Número máximo de backups a mantener
    MAX_BACKUPS = 10

    # Tipos de backup
    MANUAL = "manual"
    AUTO = "auto"
    PRE_OPERATION = "pre_op"

    def __init__(self):
        """Inicializa el gestor de backups"""
        self._crear_directorio_backups()

    def _crear_directorio_backups(self):
        """Crea el directorio de backups si no existe"""
        self.BACKUP_DIR.mkdir(exist_ok=True)
        logging.info(f"Directorio de backups: {self.BACKUP_DIR}")

    def crear_backup(self, tipo: str = MANUAL, descripcion: str = "") -> Optional[Path]:
        """
        Crea un respaldo de la base de datos
        
        Args:
            tipo: Tipo de backup (manual, auto, pre_op)
            descripcion: Descripción del backup
            
        Returns:
            Path del archivo de backup creado o None si falla
        """
        try:
            # Verificar que existe la BD
            if not DB_PATH.exists():
                logging.error(f"Base de datos no encontrada: {DB_PATH}")
                return None

            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            desc_sanitized = descripcion.replace(" ", "_")[:30] if descripcion else ""

            if desc_sanitized:
                nombre_backup = f"backup_{tipo}_{timestamp}_{desc_sanitized}.db"
            else:
                nombre_backup = f"backup_{tipo}_{timestamp}.db"

            ruta_backup = self.BACKUP_DIR / nombre_backup

            # Realizar backup usando SQLite backup API (más seguro que shutil.copy)
            self._backup_sqlite(DB_PATH, ruta_backup)

            # Verificar integridad del backup
            if self._verificar_integridad(ruta_backup):
                logging.info(f"Backup creado exitosamente: {ruta_backup}")

                # Limpiar backups antiguos
                self._limpiar_backups_antiguos()

                return ruta_backup
            else:
                logging.error("El backup creado no pasó la verificación de integridad")
                ruta_backup.unlink()  # Eliminar backup corrupto
                return None

        except Exception as e:
            logging.error(f"Error al crear backup: {e}", exc_info=True)
            return None

    def _backup_sqlite(self, origen: Path, destino: Path):
        """
        Realiza backup usando la API de SQLite (método seguro)
        Permite backup incluso con la BD en uso
        """
        # Conexión a BD origen
        conn_origen = sqlite3.connect(str(origen))

        # Conexión a BD destino
        conn_destino = sqlite3.connect(str(destino))

        try:
            # Usar API de backup de SQLite
            with conn_destino:
                conn_origen.backup(conn_destino)

            logging.info(f"Backup SQLite completado: {origen} -> {destino}")

        finally:
            conn_origen.close()
            conn_destino.close()

    def _verificar_integridad(self, ruta_backup: Path) -> bool:
        """
        Verifica la integridad del archivo de backup
        
        Args:
            ruta_backup: Ruta del archivo a verificar
            
        Returns:
            True si el backup es válido, False en caso contrario
        """
        try:
            conn = sqlite3.connect(str(ruta_backup))
            cursor = conn.cursor()

            # Verificar integridad
            cursor.execute("PRAGMA integrity_check")
            resultado = cursor.fetchone()

            conn.close()

            return resultado[0] == 'ok'

        except Exception as e:
            logging.error(f"Error al verificar integridad: {e}")
            return False

    def _limpiar_backups_antiguos(self):
        """Mantiene solo los últimos MAX_BACKUPS archivos"""
        try:
            backups = sorted(
                self.BACKUP_DIR.glob("backup_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Eliminar backups excedentes
            for backup in backups[self.MAX_BACKUPS:]:
                backup.unlink()
                logging.info(f"Backup antiguo eliminado: {backup.name}")

        except Exception as e:
            logging.error(f"Error al limpiar backups: {e}")

    def listar_backups(self) -> List[dict]:
        """
        Lista todos los backups disponibles
        
        Returns:
            Lista de diccionarios con información de cada backup
        """
        backups = []

        try:
            for archivo in sorted(
                    self.BACKUP_DIR.glob("backup_*.db"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
            ):
                stat = archivo.stat()

                # Parsear nombre del archivo
                partes = archivo.stem.split("_")
                tipo = partes[1] if len(partes) > 1 else "unknown"
                timestamp_str = partes[2] if len(partes) > 2 else ""
                descripcion = "_".join(partes[3:]) if len(partes) > 3 else ""

                # Parsear fecha
                try:
                    fecha = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                    fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    fecha_str = "Fecha desconocida"

                backups.append({
                    'archivo': archivo.name,
                    'ruta': archivo,
                    'tipo': tipo,
                    'fecha': fecha_str,
                    'descripcion': descripcion.replace("_", " "),
                    'tamaño': self._formatear_tamaño(stat.st_size)
                })

        except Exception as e:
            logging.error(f"Error al listar backups: {e}")

        return backups

    def _formatear_tamaño(self, bytes: int) -> str:
        """Formatea tamaño en bytes a formato legible"""
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unidad}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    def restaurar_backup(self, ruta_backup: Path) -> bool:
        """
        Restaura un backup específico
        CREA UN BACKUP DE SEGURIDAD ANTES DE RESTAURAR
        
        Args:
            ruta_backup: Ruta del backup a restaurar
            
        Returns:
            True si la restauración fue exitosa
        """
        try:
            # Verificar que el backup existe
            if not ruta_backup.exists():
                logging.error(f"Backup no encontrado: {ruta_backup}")
                return False

            # Verificar integridad del backup
            if not self._verificar_integridad(ruta_backup):
                logging.error("El backup a restaurar está corrupto")
                return False

            # CRÍTICO: Crear backup de la BD actual antes de restaurar
            backup_seguridad = self.crear_backup(
                tipo=self.PRE_OPERATION,
                descripcion="antes_restaurar"
            )

            if not backup_seguridad:
                logging.error("No se pudo crear backup de seguridad, restauración cancelada")
                return False

            # Cerrar todas las conexiones a la BD
            # (El usuario debe asegurarse de que no hay operaciones en curso)

            # Restaurar backup
            shutil.copy2(ruta_backup, DB_PATH)

            # Verificar que la restauración fue exitosa
            if self._verificar_integridad(DB_PATH):
                logging.info(f"Backup restaurado exitosamente: {ruta_backup}")
                return True
            else:
                logging.error("Error en la restauración, revirtiendo cambios")
                # Revertir a backup de seguridad
                shutil.copy2(backup_seguridad, DB_PATH)
                return False

        except Exception as e:
            logging.error(f"Error al restaurar backup: {e}", exc_info=True)
            return False

    def eliminar_backup(self, ruta_backup: Path) -> bool:
        """
        Elimina un backup específico
        
        Args:
            ruta_backup: Ruta del backup a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            if ruta_backup.exists():
                ruta_backup.unlink()
                logging.info(f"Backup eliminado: {ruta_backup}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error al eliminar backup: {e}")
            return False


# Funciones de conveniencia para uso rápido

def backup_antes_operacion_critica(descripcion: str) -> Optional[Path]:
    """
    Crea un backup antes de una operación crítica
    
    Args:
        descripcion: Descripción de la operación (ej: "reseteo_stock")
        
    Returns:
        Path del backup creado o None si falla
    """
    manager = BackupManager()
    return manager.crear_backup(
        tipo=BackupManager.PRE_OPERATION,
        descripcion=descripcion
    )


def backup_manual(descripcion: str = "") -> Optional[Path]:
    """
    Crea un backup manual
    
    Args:
        descripcion: Descripción opcional del backup
        
    Returns:
        Path del backup creado o None si falla
    """
    manager = BackupManager()
    return manager.crear_backup(
        tipo=BackupManager.MANUAL,
        descripcion=descripcion
    )


def listar_backups_disponibles() -> List[dict]:
    """
    Lista todos los backups disponibles
    
    Returns:
        Lista de diccionarios con información de cada backup
    """
    manager = BackupManager()
    return manager.listar_backups()
