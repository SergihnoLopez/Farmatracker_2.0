#!/usr/bin/env python3
"""
Script de prueba para validar correcciones del módulo de inventario
FarmaTrack v2.1
"""
import pandas as pd
import sys
from pathlib import Path


def crear_excel_prueba():
    """
    Crea un archivo Excel de prueba con casos variados
    """
    print("=" * 60)
    print("  Generador de Excel de Prueba")
    print("=" * 60)
    print()

    # Datos de prueba con casos variados
    datos = [
        # Productos para ACTUALIZAR (deben existir en BD)
        {
            'EAN': '7702155020010',
            'Denominación': 'ACETAMINOFEN 500MG TAB (ACTUALIZADO)',
            'Cantidad': 150,
            'Venta Real': '200',
            'Proveedor': 'TECNOQUIMICAS',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'ANALGESICOS',
            'SubGrupo': 'ACETAMINOFEN',
            '% Boni': '5'
        },
        {
            'EAN': '7702155020027',
            'Denominación': 'IBUPROFENO 400MG TAB (ACTUALIZADO)',
            'Cantidad': 100,
            'Venta Real': '350',
            'Proveedor': 'TECNOQUIMICAS',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'ANALGESICOS',
            'SubGrupo': 'IBUPROFENO',
            '% Boni': '5'
        },

        # Productos NUEVOS para insertar
        {
            'EAN': '7891234567890',
            'Denominación': 'PRODUCTO NUEVO TEST 1',
            'Cantidad': 50,
            'Venta Real': '1500',
            'Proveedor': 'PROVEEDOR TEST',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'TEST',
            'SubGrupo': 'PRUEBAS',
            '% Boni': '10'
        },
        {
            'EAN': '7891234567891',
            'Denominación': 'PRODUCTO NUEVO TEST 2',
            'Cantidad': 75,
            'Venta Real': '2500',
            'Proveedor': 'PROVEEDOR TEST',
            'UND': 'CAJ',
            'Impuesto': '5% IVA',
            'Grupo': 'TEST',
            'SubGrupo': 'PRUEBAS',
            '% Boni': '15'
        },

        # Productos con formato de precio variado (para probar parse_precio_text)
        {
            'EAN': '7891234567892',
            'Denominación': 'PRODUCTO CON PRECIO FORMATO 1',
            'Cantidad': 10,
            'Venta Real': '1.234',  # Formato con punto como separador de miles
            'Proveedor': 'PROVEEDOR TEST',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'TEST',
            'SubGrupo': 'PRECIOS',
            '% Boni': '0'
        },
        {
            'EAN': '7891234567893',
            'Denominación': 'PRODUCTO CON PRECIO FORMATO 2',
            'Cantidad': 20,
            'Venta Real': '1,234.56',  # Formato americano
            'Proveedor': 'PROVEEDOR TEST',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'TEST',
            'SubGrupo': 'PRECIOS',
            '% Boni': '0'
        },

        # Casos de ERROR (para probar manejo)
        {
            'EAN': '',  # EAN vacío - debe ignorarse
            'Denominación': 'PRODUCTO SIN EAN',
            'Cantidad': 10,
            'Venta Real': '1000',
            'Proveedor': 'ERROR',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'ERROR',
            'SubGrupo': 'ERROR',
            '% Boni': '0'
        },
        {
            'EAN': '123',  # EAN muy corto - debe ignorarse
            'Denominación': 'PRODUCTO CON EAN INVALIDO',
            'Cantidad': 10,
            'Venta Real': '1000',
            'Proveedor': 'ERROR',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'ERROR',
            'SubGrupo': 'ERROR',
            '% Boni': '0'
        },
        {
            'EAN': '7891234567894',
            'Denominación': 'PRODUCTO CON PRECIO INVALIDO',
            'Cantidad': 10,
            'Venta Real': 'INVALIDO',  # Precio no numérico - debe ignorarse
            'Proveedor': 'ERROR',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'ERROR',
            'SubGrupo': 'ERROR',
            '% Boni': '0'
        },

        # Producto duplicado (mantener primero)
        {
            'EAN': '7891234567895',
            'Denominación': 'PRODUCTO DUPLICADO - PRIMERA VERSION',
            'Cantidad': 100,
            'Venta Real': '1000',
            'Proveedor': 'PROVEEDOR 1',
            'UND': 'UN',
            'Impuesto': '19% IVA',
            'Grupo': 'TEST',
            'SubGrupo': 'DUPLICADOS',
            '% Boni': '5'
        },
        {
            'EAN': '7891234567895',  # Mismo EAN
            'Denominación': 'PRODUCTO DUPLICADO - SEGUNDA VERSION',
            'Cantidad': 200,
            'Venta Real': '2000',
            'Proveedor': 'PROVEEDOR 2',
            'UND': 'CAJ',
            'Impuesto': '5% IVA',
            'Grupo': 'TEST',
            'SubGrupo': 'DUPLICADOS',
            '% Boni': '10'
        },
    ]

    # Crear DataFrame
    df = pd.DataFrame(datos)

    # Agregar columnas ignoradas (para probar que se ignoran correctamente)
    df['Centro'] = 'CENTRO_TEST'
    df['Material'] = 'MAT001'
    df['Lote'] = 'LOTE123'
    df['Venta Cte'] = '1500'
    df['$Marcado'] = '500'
    df['Fecha Creación'] = '2026-02-15'
    df['Catalogo'] = 'CAT001'
    df['Plazo 2'] = '30'
    df['Plazo 3'] = '60'

    # Guardar
    archivo = Path('excel_prueba_inventario.xlsx')
    df.to_excel(archivo, index=False)

    print(f"✅ Archivo creado: {archivo}")
    print(f"\n📊 Resumen:")
    print(f"  • Total filas: {len(datos)}")
    print(f"  • Para actualizar: 2")
    print(f"  • Para insertar: 5")
    print(f"  • Con errores: 4")
    print(f"  • Duplicado: 1 (debe mantener primero)")
    print()
    print("📝 Casos de prueba incluidos:")
    print("  ✅ Productos existentes (actualizar)")
    print("  ✅ Productos nuevos (insertar)")
    print("  ✅ Diferentes formatos de precio")
    print("  ✅ EAN vacío (debe ignorarse)")
    print("  ✅ EAN inválido (debe ignorarse)")
    print("  ✅ Precio inválido (debe ignorarse)")
    print("  ✅ EAN duplicado (debe mantener primero)")
    print("  ✅ Columnas a ignorar")
    print()
    print("🔍 Resultado esperado al cargar:")
    print("  • Actualizados: 2 (si existen en BD)")
    print("  • Insertados: 5")
    print("  • Errores: 4")
    print("  • Total procesado: 7")
    print()


def verificar_orden_columnas():
    """
    Verifica que el orden de columnas sea consistente
    """
    print("=" * 60)
    print("  Verificador de Orden de Columnas")
    print("=" * 60)
    print()

    # Orden esperado
    orden_esperado = [
        "id_producto",
        "codigo_barras",
        "descripcion",
        "cantidad",
        "proveedor",
        "precio_compra",
        "precio_venta",
        "unidad",
        "impuesto",
        "bonificacion",
        "grupo",
        "subgrupo",
        "fecha_vencimiento"
    ]

    print("✅ Orden esperado de columnas:")
    for i, col in enumerate(orden_esperado, 1):
        print(f"  {i:2d}. {col}")

    print()
    print("📋 Puntos a verificar en el código:")
    print("  1. Definición de columnas en Treeview")
    print("  2. SELECT de la base de datos")
    print("  3. Inserción de valores en tree.insert()")
    print()
    print("⚠️  IMPORTANTE:")
    print("  Los 3 puntos deben tener el MISMO orden")
    print()


def instrucciones_prueba():
    """
    Muestra instrucciones para probar las correcciones
    """
    print("=" * 60)
    print("  Instrucciones de Prueba")
    print("=" * 60)
    print()

    print("📝 PRUEBA 1: Actualización desde Excel")
    print("-" * 60)
    print("1. Ejecutar: python script_prueba.py crear")
    print("2. Se creará: excel_prueba_inventario.xlsx")
    print("3. Abrir FarmaTrack → Ventana Inventario")
    print("4. Click '📥 Actualizar Excel'")
    print("5. Seleccionar excel_prueba_inventario.xlsx")
    print("6. Verificar resumen:")
    print("   ✅ Actualizados: 2")
    print("   ✅ Insertados: 5")
    print("   ✅ Errores: 4")
    print()

    print("📝 PRUEBA 2: Verificación de Columnas")
    print("-" * 60)
    print("1. Abrir FarmaTrack → Ventana Inventario")
    print("2. Observar tabla")
    print("3. Verificar que cada columna muestre datos correctos:")
    print("   ✅ Código → Códigos de barras")
    print("   ✅ Descripción → Nombres de productos")
    print("   ✅ Cantidad → Números")
    print("   ✅ Proveedor → Nombres de proveedores")
    print("   ✅ P. Compra → Precios")
    print("   ✅ P. Venta → Precios")
    print("   ✅ UND → Unidades (UN, CAJ, etc)")
    print()

    print("📝 PRUEBA 3: Edición Inline")
    print("-" * 60)
    print("1. Doble click en una celda")
    print("2. Modificar valor")
    print("3. Presionar Enter")
    print("4. Verificar que se guarda correctamente")
    print()

    print("📝 PRUEBA 4: Logs")
    print("-" * 60)
    print("1. Revisar: logs/farmatrack.log")
    print("2. Buscar:")
    print("   • INFO - Columnas encontradas en Excel")
    print("   • INFO - Filas válidas a procesar")
    print("   • DEBUG - Actualizado: ...")
    print("   • DEBUG - Insertado: ...")
    print("   • INFO - Resumen actualización Excel")
    print()


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python script_prueba.py crear      # Crea Excel de prueba")
        print("  python script_prueba.py verificar  # Verifica orden de columnas")
        print("  python script_prueba.py ayuda     # Muestra instrucciones")
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == 'crear':
        crear_excel_prueba()
    elif comando == 'verificar':
        verificar_orden_columnas()
    elif comando == 'ayuda':
        instrucciones_prueba()
    else:
        print(f"❌ Comando desconocido: {comando}")
        print("\nComandos disponibles: crear, verificar, ayuda")
        sys.exit(1)


if __name__ == "__main__":
    main()