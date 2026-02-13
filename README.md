💊 FarmaProStocker

FarmaProStocker es un sistema POS (Point of Sale) desarrollado en Python, diseñado para la gestión de ventas y control de inventario en una droguería.
El proyecto busca facilitar el registro de productos, el manejo de stock y el control de ventas de forma sencilla, eficiente y organizada.
🚀 Funcionalidades

    🧾 Registro de ventas
    📦 Control de inventario de medicamentos
    ➕ Agregar, editar y eliminar productos
    🔍 Consulta rápida de stock disponible
    💰 Cálculo automático del total de la venta
    📉 Actualización automática del inventario tras cada venta
    🖥️ Interfaz clara y fácil de usar

🛠️ Tecnologías utilizadas

    Lenguaje: Python 🐍
    Librerías / módulos:
        tkinter (interfaz gráfica) (si aplica)
        sqlite3 / json (para almacenamiento de datos)
    Herramientas:
        Git
        Visual Studio Code / PyCharm

Farmatracker_2.0/
│
├── 📄 main.py                  # Punto de entrada de la aplicación
├── 📄 requirements.txt         # Dependencias del proyecto
│
├── 📁 config/                  # ⚙️ Configuración general
│   └── settings.py             # Rutas, UI e información de la empresa
│
├── 📁 models/                  # 🗄️ Base de datos
│   └── database.py             # SQLite y operaciones CRUD
│
├── 📁 controllers/             # 🎮 Lógica de negocio
│   ├── inventario.py           # Gestión de inventario
│   ├── pedidos.py              # Gestión de pedidos
│   ├── ventas.py               # Gestión de ventas
│   └── pdf_generator.py        # Generación de facturas en PDF
│
├── 📁 utils/                   # 🔧 Utilidades y helpers
│   ├── validators.py           # Validaciones de datos
│   └── formatters.py           # Formateo de información
│
├── 📁 views/                   # 🖥️ Interfaces gráficas (8 ventanas)
│   ├── main_window.py          # Menú principal
│   ├── venta_window.py         # Ventana de ventas
│   ├── inventario_window.py    # Gestión de inventario
│   ├── pedidos_window.py       # Gestión de pedidos
│   ├── agregar_producto_window.py # Registro de nuevos productos
│   ├── liquidador_window.py    # Liquidación de ventas
│   ├── actualizador_window.py  # Actualización masiva
│   └── verificacion_window.py  # Verificación rápida
│
├── 📁 resources/               # 🎨 Recursos gráficos
│   └── animacion.gif           # Animación de inicio
│
├── 📁 logs/                    # 📋 Registros del sistema (auto-generado)
│   └── farmatrack.log
│
└── 📁 .venv/                   # Entorno virtual (no versionado)
