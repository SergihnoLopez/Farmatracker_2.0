"""
Configuración de fixtures para tests
Crea base de datos de prueba y fixtures comunes
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime


@pytest.fixture(scope="session")
def test_db_path():
    """Crea una base de datos temporal para tests"""
    # Crear archivo temporal
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    yield Path(path)
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture(scope="function")
def clean_db(test_db_path):
    """
    Proporciona una base de datos limpia para cada test
    Crea las tablas y limpia después de cada test
    """
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    
    # Crear tabla productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
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
    
    # Crear tabla ventas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            total REAL NOT NULL,
            productos TEXT,
            cajero TEXT DEFAULT 'Principal'
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield test_db_path
    
    # Limpiar después del test
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos")
    cursor.execute("DELETE FROM ventas")
    cursor.execute("DELETE FROM sqlite_sequence")  # Resetear autoincrement
    conn.commit()
    conn.close()


@pytest.fixture
def sample_productos():
    """Fixture con datos de productos de ejemplo"""
    return [
        {
            'codigo_barras': '7501234567890',
            'descripcion': 'ACETAMINOFEN 500MG X 20 TABS',
            'proveedor': 'GENFAR',
            'unidad': 'CAJA',
            'cantidad': 100,
            'precio_compra': 5000.0,
            'precio_venta': 7000.0,
            'impuesto': '',
            'bonificacion': 0.0,
            'grupo': 'ANALGESICOS',
            'subgrupo': 'ANTIPIRÉTICOS',
            'fecha_vencimiento': '2026-12-31'
        },
        {
            'codigo_barras': '7501234567891',
            'descripcion': 'IBUPROFENO 400MG X 10 TABS',
            'proveedor': 'MK',
            'unidad': 'CAJA',
            'cantidad': 50,
            'precio_compra': 8000.0,
            'precio_venta': 11900.0,
            'impuesto': '19% IVA',
            'bonificacion': 0.0,
            'grupo': 'ANALGESICOS',
            'subgrupo': 'ANTIINFLAMATORIOS',
            'fecha_vencimiento': '2027-06-30'
        },
        {
            'codigo_barras': '7501234567892',
            'descripcion': 'LORATADINA 10MG X 10 TABS',
            'proveedor': 'LAFRANCOL',
            'unidad': 'CAJA',
            'cantidad': 5,  # Stock bajo
            'precio_compra': 3000.0,
            'precio_venta': 4500.0,
            'impuesto': '',
            'bonificacion': 500.0,
            'grupo': 'ANTIALERGICOS',
            'subgrupo': 'ANTIHISTAMINICOS',
            'fecha_vencimiento': '2026-03-15'
        }
    ]


@pytest.fixture
def db_con_productos(clean_db, sample_productos):
    """Base de datos con productos precargados"""
    conn = sqlite3.connect(str(clean_db))
    cursor = conn.cursor()
    
    for prod in sample_productos:
        cursor.execute("""
            INSERT INTO productos 
            (codigo_barras, descripcion, proveedor, unidad, cantidad,
             precio_compra, precio_venta, impuesto, bonificacion, 
             grupo, subgrupo, fecha_vencimiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prod['codigo_barras'],
            prod['descripcion'],
            prod['proveedor'],
            prod['unidad'],
            prod['cantidad'],
            prod['precio_compra'],
            prod['precio_venta'],
            prod['impuesto'],
            prod['bonificacion'],
            prod['grupo'],
            prod['subgrupo'],
            prod['fecha_vencimiento']
        ))
    
    conn.commit()
    conn.close()
    
    return clean_db


@pytest.fixture
def mock_db_path(monkeypatch, test_db_path):
    """Mockea la ruta de la base de datos para usar la de test"""
    from config import settings
    monkeypatch.setattr(settings, 'DB_PATH', test_db_path)
    return test_db_path


# ============================================================
# FIXTURES DE MOCK PARA TKINTER
# ============================================================

class MockTreeview:
    """Mock de Tkinter Treeview para tests"""
    
    def __init__(self):
        self._items = []
        self._next_id = 1
    
    def get_children(self):
        return [item['id'] for item in self._items]
    
    def insert(self, parent, index, values=None, **kwargs):
        item_id = f"I{self._next_id:03d}"
        self._next_id += 1
        self._items.append({
            'id': item_id,
            'values': values or []
        })
        return item_id
    
    def item(self, item_id, **kwargs):
        for item in self._items:
            if item['id'] == item_id:
                if 'values' in kwargs:
                    item['values'] = kwargs['values']
                return item
        return None
    
    def delete(self, *items):
        self._items = [item for item in self._items if item['id'] not in items]


class MockEntry:
    """Mock de Tkinter Entry para tests"""
    
    def __init__(self, initial_value=""):
        self._value = initial_value
    
    def get(self):
        return self._value
    
    def delete(self, start, end):
        self._value = ""
    
    def insert(self, index, text):
        self._value = text
    
    def set_value(self, value):
        """Helper para tests"""
        self._value = value


@pytest.fixture
def mock_tree():
    """Fixture de Treeview mockeado"""
    return MockTreeview()


@pytest.fixture
def mock_entry():
    """Fixture de Entry mockeado"""
    return MockEntry()


# ============================================================
# FIXTURES DE UTILIDAD
# ============================================================

@pytest.fixture
def captura_logs(caplog):
    """Fixture para capturar logs en tests"""
    import logging
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def fecha_actual():
    """Fecha actual en formato estándar"""
    return datetime.now().strftime('%Y-%m-%d')


@pytest.fixture
def fecha_vencida():
    """Fecha vencida para tests"""
    return '2020-01-01'


@pytest.fixture
def fecha_proxima_vencer():
    """Fecha próxima a vencer (30 días)"""
    from datetime import timedelta
    fecha = datetime.now() + timedelta(days=30)
    return fecha.strftime('%Y-%m-%d')
