#!/usr/bin/env python3
"""
Script para ejecutar tests con diferentes configuraciones
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print("\n" + "=" * 70)
    print(f"📋 {description}")
    print("=" * 70)
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ Error ejecutando: {description}")
        return False
    
    print(f"\n✅ {description} - Completado")
    return True


def main():
    """Función principal"""
    
    # Verificar que estamos en el directorio correcto
    if not Path("tests").exists():
        print("❌ Error: No se encuentra el directorio 'tests'")
        print("   Ejecuta este script desde la raíz del proyecto")
        sys.exit(1)
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         🧪 FarmaProStocker - Sistema de Tests                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar instalación de pytest
    print("🔍 Verificando dependencias...")
    result = subprocess.run(
        "python -m pytest --version",
        shell=True,
        capture_output=True
    )
    
    if result.returncode != 0:
        print("\n❌ Pytest no está instalado")
        print("\nInstala las dependencias con:")
        print("  pip install pytest pytest-cov pytest-mock")
        sys.exit(1)
    
    print("✅ Pytest instalado correctamente\n")
    
    # Menú de opciones
    print("Selecciona una opción:")
    print("  1. Ejecutar todos los tests")
    print("  2. Ejecutar tests con cobertura")
    print("  3. Ejecutar tests de validators")
    print("  4. Ejecutar tests de formatters")
    print("  5. Ejecutar tests de database")
    print("  6. Ejecutar tests de ventas")
    print("  7. Generar reporte HTML de cobertura")
    print("  8. Ejecutar suite completa (tests + cobertura + reporte)")
    print("  0. Salir\n")
    
    try:
        opcion = input("Opción: ").strip()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado por el usuario")
        sys.exit(0)
    
    # Ejecutar según opción
    commands = {
        "1": (
            "python -m pytest tests/ -v",
            "Todos los tests"
        ),
        "2": (
            "python -m pytest tests/ --cov=controllers --cov=models --cov=utils --cov-report=term-missing",
            "Tests con cobertura"
        ),
        "3": (
            "python -m pytest tests/test_validators.py -v",
            "Tests de validators"
        ),
        "4": (
            "python -m pytest tests/test_formatters.py -v",
            "Tests de formatters"
        ),
        "5": (
            "python -m pytest tests/test_database.py -v",
            "Tests de database"
        ),
        "6": (
            "python -m pytest tests/test_ventas.py -v",
            "Tests de ventas"
        ),
        "7": (
            "python -m pytest tests/ --cov=controllers --cov=models --cov=utils --cov-report=html",
            "Reporte HTML de cobertura"
        ),
        "8": None,  # Suite completa
        "0": None   # Salir
    }
    
    if opcion == "0":
        print("\n👋 Hasta luego!")
        sys.exit(0)
    
    if opcion == "8":
        # Suite completa
        print("\n🚀 Ejecutando suite completa de tests...\n")
        
        success = True
        
        # 1. Tests básicos
        success = success and run_command(
            "python -m pytest tests/ -v",
            "Ejecutando todos los tests"
        )
        
        # 2. Tests con cobertura
        if success:
            success = success and run_command(
                "python -m pytest tests/ --cov=controllers --cov=models --cov=utils --cov-report=term-missing",
                "Generando reporte de cobertura"
            )
        
        # 3. Reporte HTML
        if success:
            success = success and run_command(
                "python -m pytest tests/ --cov=controllers --cov=models --cov=utils --cov-report=html",
                "Generando reporte HTML"
            )
        
        if success:
            print("\n" + "=" * 70)
            print("🎉 Suite completa ejecutada exitosamente!")
            print("=" * 70)
            print("\n📊 Reporte HTML disponible en: htmlcov/index.html")
            print("\nPara ver el reporte:")
            print("  - Linux:   xdg-open htmlcov/index.html")
            print("  - macOS:   open htmlcov/index.html")
            print("  - Windows: start htmlcov/index.html")
        else:
            print("\n❌ Algunos tests fallaron")
            sys.exit(1)
    
    elif opcion in commands:
        cmd, desc = commands[opcion]
        success = run_command(cmd, desc)
        
        if opcion == "7" and success:
            print("\n📊 Reporte HTML generado en: htmlcov/index.html")
        
        sys.exit(0 if success else 1)
    
    else:
        print("\n❌ Opción inválida")
        sys.exit(1)


if __name__ == "__main__":
    main()
