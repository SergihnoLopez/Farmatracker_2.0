"""
FarmaTrack - Sistema de gestión para Droguería Irlandesa
✅ MIGRADO A CUSTOMTKINTER

Punto de entrada de la aplicación.
"""
import sys
import logging
from pathlib import Path

# Agregar directorio raíz al path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# ==============================================================================
# ⚠️ IMPORTANTE: INICIALIZAR CUSTOMTKINTER ANTES DE IMPORTAR VENTANAS
# ==============================================================================

import customtkinter as ctk
from ctk_design_system import initialize_customtkinter

# Inicializar CustomTkinter ANTES de crear cualquier ventana
ctk.set_appearance_mode("light")  # Light mode únicamente
ctk.set_default_color_theme("blue")  # Tema azul

# ==============================================================================
# CONFIGURACIÓN DE LOGS
# ==============================================================================

# Crear carpeta de logs si no existe
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    filename=str(LOGS_DIR / 'farmatrack.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Logging a consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)


# ==============================================================================
# VERIFICACIONES
# ==============================================================================

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    dependencias_requeridas = [
        ('PIL', 'pillow'),
        ('fpdf', 'fpdf2'),
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('bcrypt', 'bcrypt'),
        ('customtkinter', 'customtkinter'),  # ✅ NUEVA DEPENDENCIA
    ]

    faltantes = []

    for modulo, paquete in dependencias_requeridas:
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(paquete)

    if faltantes:
        print("\n❌ ERROR: Faltan dependencias requeridas")
        print("\nPor favor, instala los siguientes paquetes:")
        print(f"  pip install {' '.join(faltantes)}")
        print("\nO ejecuta:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)


def verificar_estructura():
    """Verifica que exista la estructura básica de carpetas"""
    carpetas_requeridas = [
        'config',
        'models',
        'controllers',
        'views',
        'utils',
        'resources',
        'logs'
    ]

    for carpeta in carpetas_requeridas:
        carpeta_path = BASE_DIR / carpeta

        if not carpeta_path.exists():
            carpeta_path.mkdir(exist_ok=True)
            logging.info(f"Carpeta '{carpeta}' creada automáticamente")

            # Crear __init__.py si es necesario
            if carpeta not in ['resources', 'logs']:
                init_file = carpeta_path / '__init__.py'
                if not init_file.exists():
                    init_file.touch()

    logging.info("Estructura de carpetas verificada")


def verificar_base_datos():
    """Verifica que exista la base de datos y las tablas necesarias"""
    import sqlite3
    from config.settings import DB_PATH

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Verificar tabla productos
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='productos'
        """)

        if not cursor.fetchone():
            logging.info("Creando tabla 'productos'...")

            cursor.execute("""
                CREATE TABLE productos (
                    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras TEXT UNIQUE NOT NULL,
                    descripcion TEXT,
                    proveedor TEXT,
                    unidad TEXT,
                    cantidad INTEGER DEFAULT 0,
                    precio_compra REAL DEFAULT 0,
                    precio_venta REAL DEFAULT 0,
                    impuesto TEXT,
                    bonificacion REAL DEFAULT 0,
                    grupo TEXT,
                    subgrupo TEXT,
                    fecha_vencimiento TEXT
                )
            """)

            logging.info("Tabla 'productos' creada exitosamente")

        # Verificar tabla ventas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ventas'
        """)

        if not cursor.fetchone():
            logging.info("Creando tabla 'ventas'...")

            cursor.execute("""
                CREATE TABLE ventas (
                    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    total REAL NOT NULL,
                    productos TEXT,
                    cajero TEXT DEFAULT 'Principal'
                )
            """)

            logging.info("Tabla 'ventas' creada exitosamente")

        conn.commit()
        conn.close()

        logging.info("Base de datos verificada correctamente")

    except Exception as e:
        logging.error(f"Error al verificar/crear base de datos: {e}")
        print(f"\n❌ Error al inicializar la base de datos: {e}")
        sys.exit(1)


def inicializar_configuracion():
    """Inicializa archivos de configuración si no existen"""
    from config.settings import RESOURCES_DIR

    RESOURCES_DIR.mkdir(exist_ok=True)


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Función principal"""
    print("=" * 60)
    print(" FarmaTrack - Droguería Irlandesa")
    print(" Sistema de Gestión de Inventario y Ventas")
    print(" ✅ MIGRADO A CUSTOMTKINTER")
    print("=" * 60)
    print()

    try:
        # Verificaciones previas
        print("🔍 Verificando dependencias...")
        verificar_dependencias()
        print("✅ Dependencias OK")

        print("🔍 Verificando estructura de carpetas...")
        verificar_estructura()
        print("✅ Estructura OK")

        print("🔍 Verificando base de datos...")
        verificar_base_datos()
        print("✅ Base de datos OK")

        print("🔍 Inicializando configuración...")
        inicializar_configuracion()
        print("✅ Configuración OK")

        # ✅ Inicializar sistema de diseño CustomTkinter
        print("🎨 Inicializando sistema de diseño...")
        initialize_customtkinter()
        print("✅ Sistema de diseño OK")

        print()
        print("🚀 Iniciando aplicación...")
        print()

        logging.info("=" * 50)
        logging.info("Iniciando FarmaTrack (CustomTkinter)")
        logging.info("=" * 50)

        # Importar y ejecutar aplicación
        from views.main_window import MainWindow

        app = MainWindow()
        app.run()

        logging.info("Aplicación cerrada correctamente")

    except ImportError as e:
        error_msg = f"Error al importar módulos: {e}"
        logging.critical(error_msg, exc_info=True)
        print(f"\n❌ {error_msg}")
        print("\nAsegúrate de que todos los archivos estén en sus carpetas correctas")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Aplicación interrumpida por el usuario")
        logging.warning("Aplicación interrumpida por el usuario (Ctrl+C)")
        sys.exit(0)

    except Exception as e:
        error_msg = f"Error crítico en la aplicación: {e}"
        logging.critical(error_msg, exc_info=True)
        print(f"\n❌ {error_msg}")
        print("\nRevisa el archivo de log para más detalles:")
        print(f"  {LOGS_DIR / 'farmatrack.log'}")

        import traceback
        print("\n" + "=" * 60)
        print("TRACEBACK COMPLETO:")
        print("=" * 60)
        traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    main()