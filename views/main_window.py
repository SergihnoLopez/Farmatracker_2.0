"""
Ventana principal - FarmaTrack / Droguería Irlandesa
✅ Dashboard operativo en panel central
✅ Usuario activo y rol en sidebar
✅ Botón cerrar sesión
✅ Botón Gestión de Usuarios (solo admin)
✅ Fix correcto de after() callbacks de CTk
"""

import customtkinter as ctk
from ctk_design_system import (
    CTkPrimaryButton,
    Colors,
    Fonts,
    Dimensions,
)
from config.settings import RESOURCES_DIR
import logging
import tkinter as tk

try:
    import cv2
    VIDEO_DISPONIBLE = True
except ImportError:
    VIDEO_DISPONIBLE = False


class MainWindow:
    """Ventana principal del sistema"""

    def __init__(self, usuario: dict = None):
        self.usuario = usuario or {"username": "admin", "nombre": "Administrador", "rol": "admin"}

        self.root = ctk.CTk()
        self.root.title("FarmaProStocker - Droguería Irlandesa")
        self.root.configure(fg_color=Colors.BACKGROUND)

        # ── Fix after() callbacks: aplicar en la instancia CTk, no en la clase ──
        # Esto silencia los "invalid command name xxxupdate / check_dpi_scaling"
        # que CTk genera al destruir una ventana con callbacks pendientes.
        _orig_report = self.root.report_callback_exception
        def _safe_report(exc, val, tb):
            msg = str(val)
            if any(x in msg for x in ("update", "_click_animation", "check_dpi_scaling")):
                return
            _orig_report(exc, val, tb)
        self.root.report_callback_exception = _safe_report

        self._dashboard_panel = None

        self._setup_ui()
        self._mostrar_dashboard()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(10, self._maximizar_ventana)

    # ──────────────────────────────────────────────────────────────────────────
    def _maximizar_ventana(self):
        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                try:
                    w = self.root.winfo_screenwidth()
                    h = self.root.winfo_screenheight()
                    self.root.geometry(f"{w}x{h}+0+0")
                except Exception as exc:
                    logging.error(f"No se pudo maximizar: {exc}")

    # ──────────────────────────────────────────────────────────────────────────
    # LAYOUT
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # ── Sidebar izquierdo ─────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self.root,
            fg_color=Colors.SURFACE,
            corner_radius=0,
            width=265,
            border_width=1,
            border_color=Colors.BORDER,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── Info del usuario logueado ─────────────────────────────────────────
        frame_user = ctk.CTkFrame(self.sidebar, fg_color=Colors.PRIMARY, corner_radius=0)
        frame_user.pack(fill="x")

        rol    = self.usuario.get("rol", "cajero").upper()
        nombre = self.usuario.get("nombre", "Usuario")

        ctk.CTkLabel(
            frame_user, text=f"👤  {nombre}",
            font=(Fonts.FAMILY, 13, "bold"),
            text_color="white", anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            frame_user, text=f"🔑  {rol}",
            font=(Fonts.FAMILY, 11),
            text_color="#a8d4f8", anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 10))

        # ── Logo ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self.sidebar, text="FarmaTrack",
            font=(Fonts.FAMILY, 18, "bold"),
            text_color=Colors.PRIMARY,
        ).pack(pady=(14, 2))

        ctk.CTkLabel(
            self.sidebar, text="Droguería Irlandesa",
            font=(Fonts.FAMILY, 11),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=(0, 8))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=Colors.BORDER).pack(fill="x", padx=10)

        # ── Botones ───────────────────────────────────────────────────────────
        self.frame_botones = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=Colors.PRIMARY,
            scrollbar_button_hover_color=Colors.PRIMARY_HOVER,
        )
        self.frame_botones.pack(fill="both", expand=True, padx=8, pady=8)

        self._create_buttons()

        ctk.CTkFrame(self.sidebar, height=1, fg_color=Colors.BORDER).pack(fill="x", padx=10)

        # Gestión de usuarios (solo admin)
        from views.login_window import AuthManager
        if AuthManager.es_admin():
            ctk.CTkButton(
                self.sidebar, text="👥  Gestión de Usuarios",
                height=36, corner_radius=Dimensions.BUTTON_RADIUS,
                fg_color="transparent", text_color=Colors.PRIMARY,
                hover_color=Colors.BACKGROUND,
                border_width=1, border_color=Colors.PRIMARY,
                font=(Fonts.FAMILY, 12),
                command=self._abrir_gestion_usuarios,
            ).pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkButton(
            self.sidebar, text="🚪  Cerrar Sesión",
            height=36, corner_radius=Dimensions.BUTTON_RADIUS,
            fg_color="transparent", text_color=Colors.ERROR,
            hover_color="#fde8e8",
            border_width=1, border_color=Colors.ERROR,
            font=(Fonts.FAMILY, 12),
            command=self._cerrar_sesion,
        ).pack(fill="x", padx=10, pady=(0, 10))

        # ── Área central ──────────────────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(self.root, fg_color=Colors.BACKGROUND, corner_radius=0)
        self.main_frame.pack(side="right", expand=True, fill="both")

    # ──────────────────────────────────────────────────────────────────────────
    # BOTONES
    # ──────────────────────────────────────────────────────────────────────────

    def _create_buttons(self):
        try:
            from views.backup_window import BackupWindow
            BACKUP_DISPONIBLE = True
        except ImportError:
            BACKUP_DISPONIBLE = False

        from views.venta_window            import VentaWindow
        from views.inventario_window       import InventarioWindow
        from views.pedidos_window          import PedidosWindow
        from views.agregar_producto_window import AgregarProductoWindow
        from views.liquidador_window       import LiquidadorWindow
        from views.actualizador_window     import ActualizadorWindow
        from views.verificacion_window     import VerificacionWindow
        from views.tension_window          import TensionWindow
        from views.pedido_centro_window    import PedidoCentroWindow
        from views.reporte_ventas_window   import ReporteVentasWindow

        botones = [
            ("🏠  Dashboard",              self._mostrar_dashboard),
            ("💰  Registrar Venta",        lambda: self._abrir_modulo(VentaWindow)),
            ("📦  Ver Inventario",          lambda: self._abrir_modulo(InventarioWindow)),
            ("➕  Agregar Producto",         lambda: self._abrir_modulo(AgregarProductoWindow)),
            ("📋  Módulo de Pedidos",       lambda: self._abrir_modulo(PedidosWindow)),
            ("💵  Liquidador",              lambda: self._abrir_modulo(LiquidadorWindow)),
            ("🔄  Actualizar Inventario",   lambda: self._abrir_modulo(ActualizadorWindow)),
            ("✅  Verificación Rápida",     lambda: self._abrir_modulo(VerificacionWindow)),
            ("💾  Backups",
             (lambda: self._abrir_modulo(BackupWindow)) if BACKUP_DISPONIBLE else (lambda: None)),
            ("🩺  Toma de Tensión",         lambda: self._abrir_modulo(TensionWindow)),
            ("🏬  Pedido Centro",           lambda: self._abrir_modulo(PedidoCentroWindow)),
            ("📊  Reporte de Ventas",       lambda: self._abrir_modulo(ReporteVentasWindow)),
        ]

        for idx, (texto, comando) in enumerate(botones):
            btn = CTkPrimaryButton(
                self.frame_botones, text=texto, command=comando,
                width=238, height=Dimensions.BUTTON_HEIGHT, anchor="w",
            )
            btn.configure(
                fg_color=Colors.SUCCESS if idx == 0 else Colors.PRIMARY,
                hover_color="#0a6b0a" if idx == 0 else Colors.PRIMARY_HOVER,
            )
            btn.pack(fill="x", pady=(0, 6), padx=2)

    # ──────────────────────────────────────────────────────────────────────────
    # NAVEGACIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _limpiar_main_frame(self):
        if self._dashboard_panel:
            try:
                self._dashboard_panel.destruir()
            except Exception:
                pass
            self._dashboard_panel = None

        for widget in self.main_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

    def _mostrar_dashboard(self):
        self._limpiar_main_frame()
        try:
            from views.dashboard_panel import DashboardPanel
            self._dashboard_panel = DashboardPanel(self.main_frame)
            self._dashboard_panel.pack(fill="both", expand=True)
        except Exception as e:
            logging.error(f"Error cargando dashboard: {e}")
            ctk.CTkLabel(
                self.main_frame,
                text="Dashboard no disponible",
                font=(Fonts.FAMILY, 18),
                text_color=Colors.TEXT_SECONDARY,
            ).pack(expand=True)

    def _abrir_modulo(self, WindowClass):
        try:
            WindowClass(self.root)
        except Exception as e:
            logging.error(f"Error abriendo módulo {WindowClass.__name__}: {e}")
            import tkinter.messagebox as mb
            mb.showerror("Error", f"No se pudo abrir el módulo:\n{e}")

    # ──────────────────────────────────────────────────────────────────────────
    # SESIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _abrir_gestion_usuarios(self):
        try:
            from views.login_window import GestionUsuariosWindow
            GestionUsuariosWindow(self.root)
        except Exception as e:
            logging.error(f"Error en gestión de usuarios: {e}")

    def _cerrar_sesion(self):
        import tkinter.messagebox as mb
        if mb.askyesno("Cerrar sesión",
                       f"¿Deseas cerrar la sesión de {self.usuario.get('nombre', '')}?"):
            try:
                from views.login_window import AuthManager
                AuthManager.cerrar_sesion()
            except Exception:
                pass
            self._limpiar_main_frame()
            self.root.withdraw()
            self.root.after(80, self._finalizar_cierre_sesion)

    def _finalizar_cierre_sesion(self):
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        _iniciar_con_login()

    def _on_close(self):
        self._limpiar_main_frame()
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


# ==============================================================================
# ARRANQUE CON LOGIN
# ==============================================================================

def _iniciar_con_login():
    from views.login_window import LoginWindow

    def on_login(usuario):
        app = MainWindow(usuario=usuario)
        app.root.after(800, lambda: _mostrar_alertas_vencimiento(app.root))
        app.run()

    login = LoginWindow(on_login_success=on_login)
    login.run()


def _mostrar_alertas_vencimiento(parent):
    try:
        from controllers.dashboard import DashboardController
        por_vencer = DashboardController.productos_por_vencer()
        vencidos = [p for p in por_vencer if p.get("estado") == "vencido"]
        criticos = [p for p in por_vencer if p.get("estado") == "critico"]

        if not vencidos and not criticos:
            return

        msg_lines = []
        if vencidos:
            msg_lines.append(f"🔴  {len(vencidos)} producto(s) VENCIDOS:")
            for p in vencidos[:5]:
                msg_lines.append(f"    • {p['descripcion'][:40]}  ({p['fecha_vencimiento']})")
            if len(vencidos) > 5:
                msg_lines.append(f"    ... y {len(vencidos)-5} más")
        if criticos:
            msg_lines.append(f"\n🟠  {len(criticos)} producto(s) vencen en ≤ 7 días:")
            for p in criticos[:5]:
                msg_lines.append(f"    • {p['descripcion'][:40]}  ({p['dias_restantes']}d)")
            if len(criticos) > 5:
                msg_lines.append(f"    ... y {len(criticos)-5} más")
        msg_lines.append("\n⚠  Revisa el Dashboard para el detalle completo.")

        import tkinter.messagebox as mb
        mb.showwarning("⚠  Alerta de Vencimientos", "\n".join(msg_lines), parent=parent)
    except Exception as e:
        logging.error(f"Error en alerta de vencimientos: {e}")