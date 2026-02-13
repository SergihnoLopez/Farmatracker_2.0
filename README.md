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

📂 Estructura del proyecto

/mnt/project/ │ ├── 📄 main.py # Punto de entrada ├── 📄 requirements.txt # Dependencias │ ├── 📁 config/ # ⚙️ Configuración │ └── settings.py # Rutas, UI, info empresa │ ├── 📁 models/ # 🗄️ Base de datos │ └── database.py # SQLite + operaciones CRUD │ ├── 📁 controllers/ # 🎮 Lógica de negocio │ ├── inventario.py # Gestión inventario │ ├── pedidos.py # Gestión pedidos │ ├── ventas.py # Gestión ventas │ └── pdf_generator.py # Facturas PDF │ ├── 📁 utils/ # 🔧 Herramientas │ ├── validators.py # Validaciones │ └── formatters.py # Formateo datos │ ├── 📁 views/ # 🖥️ Interfaces (8 ventanas) │ ├── main_window.py # Menú principal │ ├── venta_window.py # Ventas │ ├── inventario_window.py # Inventario │ ├── pedidos_window.py # Pedidos │ ├── agregar_producto_window.py # Nuevo producto │ ├── liquidador_window.py # Liquidación │ ├── actualizador_window.py # Actualización masiva │ └── verificacion_window.py # Verificación rápida │ ├── 📁 resources/ # 🎨 Recursos │ └── animacion.gif # Animación inicio │ └── 📁 logs/ # 📋 Logs (auto-generado) └── farmatrack.log
