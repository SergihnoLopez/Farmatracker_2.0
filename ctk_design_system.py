"""
🎨 SISTEMA DE DISEÑO CUSTOMTKINTER - FARMATRACK
================================================

Sistema de diseño completo usando CustomTkinter.
Elimina TOTALMENTE Tkinter clásico.

IMPORTANTE: Este archivo debe importarse ANTES de crear cualquier ventana.
"""

import customtkinter as ctk
from typing import Optional, Callable

# ==============================================================================
# 🎨 INICIALIZACIÓN OBLIGATORIA
# ==============================================================================

def initialize_customtkinter():
    """
    Inicializa CustomTkinter con configuración obligatoria.
    Debe llamarse UNA VEZ al inicio de la aplicación.
    """
    # Light mode únicamente
    ctk.set_appearance_mode("light")

    # Tema azul base
    ctk.set_default_color_theme("blue")

    # Configuración de widgets por defecto
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)


# ==============================================================================
# 🎨 COLORES - SISTEMA OBLIGATORIO
# ==============================================================================

class Colors:
    """
    Paleta de colores centralizada.
    Windows 11 Light Mode únicamente.
    """
    # Fondos
    BACKGROUND = "#f4f6f8"          # Fondo principal
    SURFACE = "#ffffff"             # Cards, superficies

    # Azul principal
    PRIMARY = "#0f6cbd"             # Azul principal
    PRIMARY_HOVER = "#0c5aa6"       # Hover estado

    # Textos
    TEXT_PRIMARY = "#1a1a1a"        # Texto principal
    TEXT_SECONDARY = "#616161"      # Texto secundario

    # Estados
    SUCCESS = "#107c10"             # Verde
    ERROR = "#d13438"               # Rojo
    WARNING = "#f7630c"             # Naranja

    # Bordes
    BORDER = "#e3e6ea"              # Borde sutil


# ==============================================================================
# 📝 TIPOGRAFÍA
# ==============================================================================

class Fonts:
    """Sistema tipográfico"""
    FAMILY = "Segoe UI"

    TITLE_SIZE = 28
    SUBTITLE_SIZE = 14
    BODY_SIZE = 14
    BUTTON_SIZE = 16  # ✅ AUMENTADO DE 14 A 16
    SMALL_SIZE = 12

    # Tuplas para usar con CustomTkinter
    TITLE = (FAMILY, TITLE_SIZE, "bold")
    SUBTITLE = (FAMILY, SUBTITLE_SIZE)
    BODY = (FAMILY, BODY_SIZE)
    BUTTON = (FAMILY, BUTTON_SIZE, "bold")
    SMALL = (FAMILY, SMALL_SIZE)


# ==============================================================================
# 📐 DIMENSIONES
# ==============================================================================

class Dimensions:
    """Espaciado y dimensiones"""
    # Espaciado
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24

    # Bordes redondeados
    BUTTON_RADIUS = 8
    CARD_RADIUS = 10
    INPUT_RADIUS = 6

    # Alturas
    BUTTON_HEIGHT = 46
    INPUT_HEIGHT = 40


# ==============================================================================
# 🧱 COMPONENTES BASE
# ==============================================================================

class CTkPrimaryButton(ctk.CTkButton):
    """
    Botón principal azul.
    Uso: CTkPrimaryButton(parent, text="Guardar", command=callback)
    """
    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable] = None,
        width: int = 140,
        **kwargs
    ):
        # Configuración por defecto
        default_config = {
            'text': text,
            'command': command,
            'width': width,
            'height': Dimensions.BUTTON_HEIGHT,
            'corner_radius': Dimensions.BUTTON_RADIUS,
            'fg_color': Colors.PRIMARY,
            'hover_color': Colors.PRIMARY_HOVER,
            'text_color': Colors.SURFACE,
            'font': Fonts.BUTTON,
            'cursor': 'hand2',
        }

        # Permitir override
        default_config.update(kwargs)

        super().__init__(master, **default_config)


class CTkSecondaryButton(ctk.CTkButton):
    """
    Botón secundario con borde.
    Uso: CTkSecondaryButton(parent, text="Cancelar", command=callback)
    """
    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable] = None,
        width: int = 140,
        **kwargs
    ):
        default_config = {
            'text': text,
            'command': command,
            'width': width,
            'height': Dimensions.BUTTON_HEIGHT,
            'corner_radius': Dimensions.BUTTON_RADIUS,
            'fg_color': Colors.SURFACE,
            'hover_color': Colors.BACKGROUND,
            'text_color': Colors.PRIMARY,
            'border_width': 2,
            'border_color': Colors.PRIMARY,
            'font': Fonts.BUTTON,
            'cursor': 'hand2',
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkSuccessButton(ctk.CTkButton):
    """
    Botón de acción positiva (guardar).
    Uso: CTkSuccessButton(parent, text="Guardar", command=callback)
    """
    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable] = None,
        width: int = 140,
        **kwargs
    ):
        default_config = {
            'text': text,
            'command': command,
            'width': width,
            'height': Dimensions.BUTTON_HEIGHT,
            'corner_radius': Dimensions.BUTTON_RADIUS,
            'fg_color': Colors.SUCCESS,
            'hover_color': "#0e6b0e",
            'text_color': Colors.SURFACE,
            'font': Fonts.BUTTON,
            'cursor': 'hand2',
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkDangerButton(ctk.CTkButton):
    """
    Botón de acción destructiva (eliminar).
    Uso: CTkDangerButton(parent, text="Eliminar", command=callback)
    """
    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable] = None,
        width: int = 140,
        **kwargs
    ):
        default_config = {
            'text': text,
            'command': command,
            'width': width,
            'height': Dimensions.BUTTON_HEIGHT,
            'corner_radius': Dimensions.BUTTON_RADIUS,
            'fg_color': Colors.ERROR,
            'hover_color': "#b11116",
            'text_color': Colors.SURFACE,
            'font': Fonts.BUTTON,
            'cursor': 'hand2',
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkSidebarButton(ctk.CTkButton):
    """
    Botón para sidebar/navegación.
    Uso: CTkSidebarButton(parent, text="Inventario", icon="📦", command=callback)
    """
    def __init__(
        self,
        master,
        text: str = "",
        icon: str = "",
        command: Optional[Callable] = None,
        **kwargs
    ):
        display_text = f"{icon} {text}" if icon else text

        default_config = {
            'text': display_text,
            'command': command,
            'width': 200,
            'height': 40,
            'corner_radius': Dimensions.BUTTON_RADIUS,
            'fg_color': Colors.SURFACE,
            'hover_color': Colors.BACKGROUND,
            'text_color': Colors.TEXT_PRIMARY,
            'font': Fonts.BODY,
            'cursor': 'hand2',
            'anchor': 'w',
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkCard(ctk.CTkFrame):
    """
    Tarjeta elevada con fondo blanco.
    Uso: card = CTkCard(parent); label = ctk.CTkLabel(card, text="Contenido")
    """
    def __init__(self, master, **kwargs):
        default_config = {
            'fg_color': Colors.SURFACE,
            'corner_radius': Dimensions.CARD_RADIUS,
            'border_width': 1,
            'border_color': Colors.BORDER,
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkStyledEntry(ctk.CTkEntry):
    """
    Campo de entrada estilizado.
    Uso: CTkStyledEntry(parent, placeholder_text="Escribe aquí...")
    """
    def __init__(
        self,
        master,
        placeholder_text: str = "",
        **kwargs
    ):
        default_config = {
            'placeholder_text': placeholder_text,
            'height': Dimensions.INPUT_HEIGHT,
            'corner_radius': Dimensions.INPUT_RADIUS,
            'border_width': 1,
            'border_color': Colors.BORDER,
            'fg_color': Colors.SURFACE,
            'text_color': Colors.TEXT_PRIMARY,
            'placeholder_text_color': Colors.TEXT_SECONDARY,
            'font': Fonts.BODY,
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkLabelTitle(ctk.CTkLabel):
    """
    Etiqueta de título.
    Uso: CTkLabelTitle(parent, text="Mi Título")
    """
    def __init__(self, master, text: str = "", **kwargs):
        default_config = {
            'text': text,
            'font': Fonts.TITLE,
            'text_color': Colors.TEXT_PRIMARY,
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


class CTkLabelSubtitle(ctk.CTkLabel):
    """
    Etiqueta de subtítulo.
    Uso: CTkLabelSubtitle(parent, text="Mi subtítulo")
    """
    def __init__(self, master, text: str = "", **kwargs):
        default_config = {
            'text': text,
            'font': Fonts.SUBTITLE,
            'text_color': Colors.TEXT_SECONDARY,
        }

        default_config.update(kwargs)
        super().__init__(master, **default_config)


# ==============================================================================
# 🎨 UTILIDADES
# ==============================================================================

def create_sidebar(master) -> ctk.CTkFrame:
    """
    Crea un sidebar estándar.
    Returns: CTkFrame configurado como sidebar
    """
    sidebar = ctk.CTkFrame(
        master,
        fg_color=Colors.SURFACE,
        corner_radius=0,
        border_width=1,
        border_color=Colors.BORDER,
    )
    return sidebar


def create_main_content(master) -> ctk.CTkFrame:
    """
    Crea el área de contenido principal.
    Returns: CTkFrame configurado para contenido
    """
    content = ctk.CTkFrame(
        master,
        fg_color=Colors.BACKGROUND,
        corner_radius=0,
    )
    return content


def configure_treeview_style():
    """
    Configura el estilo de ttk.Treeview para que sea coherente.
    Nota: ttk.Treeview se mantiene porque no hay alternativa en CustomTkinter.
    """
    from tkinter import ttk

    style = ttk.Style()
    style.theme_use('clam')

    # Configurar Treeview sin bordes 3D
    style.configure(
        "Treeview",
        background=Colors.SURFACE,
        foreground=Colors.TEXT_PRIMARY,
        fieldbackground=Colors.SURFACE,
        borderwidth=0,
        relief='flat',
        font=Fonts.BODY,
        rowheight=30
    )

    # Encabezados
    style.configure(
        "Treeview.Heading",
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        relief='flat',
        font=Fonts.BUTTON
    )

    # Hover
    style.map(
        "Treeview.Heading",
        background=[('active', Colors.BORDER)]
    )

    # Selección
    style.map(
        "Treeview",
        background=[('selected', Colors.PRIMARY)],
        foreground=[('selected', Colors.SURFACE)]
    )


# ==============================================================================
# 📋 COMPATIBILIDAD CON CÓDIGO EXISTENTE
# ==============================================================================

# Alias para compatibilidad temporal durante migración
FONT_STYLE = Fonts.BODY
BTN_COLOR = Colors.PRIMARY
BTN_FG = Colors.SURFACE
BG_COLOR = Colors.BACKGROUND


# ==============================================================================
# ✅ EXPORTAR TODO
# ==============================================================================

__all__ = [
    # Funciones
    'initialize_customtkinter',
    'create_sidebar',
    'create_main_content',
    'configure_treeview_style',

    # Clases de diseño
    'Colors',
    'Fonts',
    'Dimensions',

    # Componentes
    'CTkPrimaryButton',
    'CTkSecondaryButton',
    'CTkSuccessButton',
    'CTkDangerButton',
    'CTkSidebarButton',
    'CTkCard',
    'CTkStyledEntry',
    'CTkLabelTitle',
    'CTkLabelSubtitle',

    # Compatibilidad
    'FONT_STYLE',
    'BTN_COLOR',
    'BTN_FG',
    'BG_COLOR',
]