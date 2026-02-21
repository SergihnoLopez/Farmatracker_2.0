"""
FarmaTrack - Sistema de gestión para Droguería Irlandesa
"""
import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# ==============================================================================
# CUSTOMTKINTER
# ==============================================================================
import customtkinter as ctk
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ==============================================================================
# LOGS
# ==============================================================================
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(LOGS_DIR / 'farmatrack.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)


# ==============================================================================
# VERIFICACIONES
# ==============================================================================

def _can_import(mod):
    try: __import__(mod); return True
    except ImportError: return False

def verificar_dependencias():
    deps = [
        ('PIL','pillow'), ('fpdf','fpdf2'), ('pandas','pandas'),
        ('openpyxl','openpyxl'), ('bcrypt','bcrypt'), ('customtkinter','customtkinter'),
    ]
    faltantes = [pkg for mod, pkg in deps if not _can_import(mod)]
    if faltantes:
        print(f"\n❌ Faltan dependencias: pip install {' '.join(faltantes)}")
        sys.exit(1)

def verificar_estructura():
    for carpeta in ['config','models','controllers','views','utils','resources','logs']:
        p = BASE_DIR / carpeta
        p.mkdir(exist_ok=True)
        if carpeta not in ('resources', 'logs'):
            init = p / '__init__.py'
            if not init.exists(): init.touch()


def instalar_tcl_error_filter(tk_root):
    """
    Redefine el handler de errores de Tcl dentro del intérprete Tcl embebido.
    Los mensajes 'invalid command name xxxupdate/check_dpi_scaling' los genera
    Tcl directamente — no pasan por Python. La única forma de silenciarlos es
    sobreescribir 'bgerror' (el handler de errores de fondo de Tcl).
    """
    tcl_script = r"""
proc bgerror {msg} {
    set noise_patterns {
        "invalid command name"
        "check_dpi_scaling"
        "_click_animation"
    }
    foreach pattern $noise_patterns {
        if {[string match *$pattern* $msg]} {
            return
        }
    }
    # Para cualquier otro error real, mostrarlo normalmente
    puts stderr "Error Tcl: $msg"
}
"""
    try:
        tk_root.tk.eval(tcl_script)
    except Exception as e:
        logging.warning(f"No se pudo instalar filtro Tcl: {e}")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    verificar_dependencias()
    verificar_estructura()

    try:
        from ctk_design_system import initialize_customtkinter
        initialize_customtkinter()
    except ImportError:
        pass

    try:
        from views.login_window import LoginWindow, AuthManager
        from views.main_window  import MainWindow, _mostrar_alertas_vencimiento

        AuthManager.inicializar_tabla_usuarios()

        def on_login_success(usuario):
            logging.info(f"Sesión: {usuario.get('username')} ({usuario.get('rol')})")
            app = MainWindow(usuario=usuario)
            # Instalar el filtro Tcl en la ventana principal
            instalar_tcl_error_filter(app.root)
            app.root.after(800, lambda: _mostrar_alertas_vencimiento(app.root))
            app.run()
            logging.info("Ventana principal cerrada")

        login = LoginWindow(on_login_success=on_login_success)
        # Instalar el filtro Tcl también en la ventana de login
        instalar_tcl_error_filter(login.root)
        login.run()
        logging.info("App cerrada")

    except ImportError as e:
        logging.critical(f"ImportError: {e}", exc_info=True)
        print(f"\n❌ {e}"); sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Error crítico: {e}", exc_info=True)
        import traceback; traceback.print_exc(); sys.exit(1)


if __name__ == "__main__":
    main()