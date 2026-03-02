"""
Extractor de datos de facturas SIP Asociados
Integrado al sistema FarmaTrack
"""
import pdfplumber
import pandas as pd
import re
import logging
from typing import List, Dict, Optional


class SIPExtractor:
    """Extrae datos de facturas PDF de SIP Asociados"""

    @staticmethod
    def extraer_desde_pdf(pdf_path: str) -> List[Dict[str, str]]:
        """
        Extrae productos desde una factura PDF de SIP Asociados

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Lista de diccionarios con 'Cantidad' y 'Código de Barras'
        """
        extracted_data = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()

                    if not text:
                        logging.warning(f"Página {page_num} sin texto extraíble")
                        continue

                    lines = text.split('\n')

                    for line_num, line in enumerate(lines, 1):
                        tokens = line.strip().split()

                        # Buscar código de barras (último número de 12-13 dígitos)
                        codigos = [t for t in tokens if re.fullmatch(r'\d{12,13}', t)]

                        if not codigos:
                            continue

                        codigo = codigos[-1]

                        # Buscar el índice del primer valor con $
                        try:
                            precio_index = next(i for i, t in enumerate(tokens) if "$" in t)
                        except StopIteration:
                            precio_index = len(tokens)

                        # Buscar cantidad antes del precio
                        cantidad = None
                        for token in tokens[:precio_index]:
                            if re.fullmatch(r'\d{1,3}', token):
                                cantidad = token
                                break

                        if cantidad:
                            extracted_data.append({
                                'Cantidad': cantidad,
                                'Código de Barras': codigo
                            })

                            logging.debug(
                                f"Página {page_num}, Línea {line_num}: "
                                f"Cantidad={cantidad}, Código={codigo}"
                            )

            logging.info(f"Extracción completada: {len(extracted_data)} productos encontrados")

        except FileNotFoundError:
            logging.error(f"Archivo no encontrado: {pdf_path}")
            raise
        except Exception as e:
            logging.error(f"Error al procesar PDF: {e}", exc_info=True)
            raise

        return extracted_data

    @staticmethod
    def exportar_a_excel(datos: List[Dict[str, str]], output_path: str) -> bool:
        """
        Exporta datos extraídos a Excel

        Args:
            datos: Lista de productos extraídos
            output_path: Ruta del archivo de salida

        Returns:
            True si la exportación fue exitosa
        """
        try:
            if not datos:
                logging.warning("No hay datos para exportar")
                return False

            df = pd.DataFrame(datos)
            columns_order = ['Cantidad', 'Código de Barras']
            df = df[[col for col in columns_order if col in df.columns]]

            df.to_excel(output_path, index=False)
            logging.info(f"Datos exportados a: {output_path}")

            return True

        except Exception as e:
            logging.error(f"Error al exportar a Excel: {e}")
            return False

    @staticmethod
    def validar_pdf_sip(pdf_path: str) -> bool:
        """
        Valida que el PDF sea una factura de SIP Asociados

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            True si parece ser una factura SIP válida
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False

                # Extraer texto de la primera página
                first_page_text = pdf.pages[0].extract_text()

                if not first_page_text:
                    return False

                # Buscar indicadores de SIP Asociados
                texto_normalizado = first_page_text.lower()

                indicadores = [
                    'sip',
                    'asociados',
                    'código de barras',
                    'factura'
                ]

                coincidencias = sum(1 for ind in indicadores if ind in texto_normalizado)

                # Si tiene al menos 2 indicadores, probablemente es SIP
                return coincidencias >= 2

        except Exception as e:
            logging.error(f"Error al validar PDF: {e}")
            return False

    @staticmethod
    def generar_reporte_extraccion(datos: List[Dict[str, str]]) -> str:
        """
        Genera un reporte de texto de la extracción

        Args:
            datos: Lista de productos extraídos

        Returns:
            String con el reporte formateado
        """
        if not datos:
            return "No se encontraron productos en el PDF"

        lineas = [
            "=" * 50,
            f"REPORTE DE EXTRACCIÓN SIP ASOCIADOS",
            "=" * 50,
            f"Total de productos: {len(datos)}",
            "",
            "CANT.  CÓDIGO DE BARRAS",
            "-" * 40
        ]

        for item in datos[:20]:  # Mostrar primeros 20
            linea = f"{item['Cantidad']:>4}  {item['Código de Barras']}"
            lineas.append(linea)

        if len(datos) > 20:
            lineas.append(f"\n... y {len(datos)-20} productos más")

        return "\n".join(lineas)