"""
Ventana de Login - FarmaTrack
Fondo blanco, video MP4 debajo del label, layout dos paneles
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import bcrypt, sqlite3, logging
from pathlib import Path

try:
    from ctk_design_system import Colors, Fonts, Dimensions
except ImportError:
    class Colors:
        PRIMARY="#0f6cbd"; PRIMARY_HOVER="#0c5aa6"; SURFACE="#ffffff"
        BACKGROUND="#f4f6f8"; TEXT_PRIMARY="#1a1a1a"; TEXT_SECONDARY="#616161"
        SUCCESS="#107c10"; ERROR="#d13438"; BORDER="#e3e6ea"
    class Fonts:
        FAMILY="Segoe UI"; BODY=("Segoe UI",14); BUTTON=("Segoe UI",14,"bold")
    class Dimensions:
        BUTTON_HEIGHT=46; BUTTON_RADIUS=8; INPUT_HEIGHT=40

try:
    import cv2; CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    from PIL import Image, ImageTk; PIL_OK = True
except ImportError:
    PIL_OK = False


# ==============================================================================
# AUTH MANAGER
# ==============================================================================

class AuthManager:
    _usuario_actual = None

    @staticmethod
    def _get_db_path():
        try:
            from config.settings import DB_PATH; return DB_PATH
        except ImportError:
            return Path("farma_pro_stocker.db")

    @classmethod
    def inicializar_tabla_usuarios(cls):
        COLS_REQ = {"id","username","password_hash","nombre","rol","activo","creado"}
        try:
            conn = sqlite3.connect(str(cls._get_db_path()))
            cur  = conn.cursor()

            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
            existe = cur.fetchone() is not None

            if existe:
                cur.execute("PRAGMA table_info(usuarios)")
                cols_act = {r[1] for r in cur.fetchall()}
                if not COLS_REQ.issubset(cols_act):
                    faltantes   = COLS_REQ - cols_act
                    cols_comunes= list(cols_act & COLS_REQ)
                    logging.warning(f"Migrando tabla usuarios. Faltantes: {faltantes}")
                    filas = []
                    if cols_comunes:
                        try:
                            cur.execute(f"SELECT {','.join(cols_comunes)} FROM usuarios")
                            filas = cur.fetchall()
                        except Exception: pass
                    cur.execute("DROP TABLE IF EXISTS usuarios")
                    cls._crear_tabla(cur); conn.commit()
                    for f in filas:
                        try:
                            ph = ",".join("?"*len(cols_comunes))
                            cn = ",".join(cols_comunes)
                            cur.execute(f"INSERT OR IGNORE INTO usuarios ({cn}) VALUES ({ph})", f)
                        except Exception: pass
                    conn.commit()
            else:
                cls._crear_tabla(cur); conn.commit()

            cur.execute("SELECT COUNT(*) FROM usuarios")
            if cur.fetchone()[0] == 0:
                for user,pw,nom,rol in [
                    ("admin",   "admin123",  "Administrador",    "admin"),
                    ("cajero",  "cajero123", "Cajero Principal", "cajero"),
                ]:
                    h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
                    cur.execute(
                        "INSERT INTO usuarios (username,password_hash,nombre,rol) VALUES (?,?,?,?)",
                        (user, h, nom, rol)
                    )
                conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error inicializando usuarios: {e}")

    @staticmethod
    def _crear_tabla(cursor):
        cursor.execute("""
            CREATE TABLE usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre        TEXT NOT NULL,
                rol           TEXT NOT NULL DEFAULT 'cajero',
                activo        INTEGER DEFAULT 1,
                creado        TEXT DEFAULT CURRENT_TIMESTAMP
            )""")

    @classmethod
    def autenticar(cls, username, password):
        try:
            with sqlite3.connect(str(cls._get_db_path())) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM usuarios WHERE username=? AND activo=1",
                    (username.strip().lower(),)
                ).fetchone()
                if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
                    cls._usuario_actual = dict(row)
                    logging.info(f"Login: {username}")
                    return cls._usuario_actual
        except Exception as e:
            logging.error(f"Auth error: {e}")
        return None

    @classmethod
    def usuario_actual(cls): return cls._usuario_actual

    @classmethod
    def cerrar_sesion(cls):
        logging.info(f"Logout: {cls._usuario_actual}")
        cls._usuario_actual = None

    @classmethod
    def es_admin(cls):
        return cls._usuario_actual and cls._usuario_actual.get("rol") == "admin"

    @classmethod
    def obtener_usuarios(cls):
        try:
            with sqlite3.connect(str(cls._get_db_path())) as conn:
                conn.row_factory = sqlite3.Row
                return [dict(r) for r in conn.execute(
                    "SELECT id,username,nombre,rol,activo,creado FROM usuarios ORDER BY id"
                ).fetchall()]
        except Exception as e:
            logging.error(e); return []

    @classmethod
    def crear_usuario(cls, username, password, nombre, rol="cajero"):
        try:
            h = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            with sqlite3.connect(str(cls._get_db_path())) as conn:
                conn.execute(
                    "INSERT INTO usuarios (username,password_hash,nombre,rol) VALUES (?,?,?,?)",
                    (username.strip().lower(), h, nombre, rol)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError: return False
        except Exception as e: logging.error(e); return False

    @classmethod
    def cambiar_password(cls, username, nueva):
        try:
            h = bcrypt.hashpw(nueva.encode(), bcrypt.gensalt()).decode()
            with sqlite3.connect(str(cls._get_db_path())) as conn:
                conn.execute("UPDATE usuarios SET password_hash=? WHERE username=?", (h, username))
                conn.commit()
            return True
        except Exception as e: logging.error(e); return False

    @classmethod
    def toggle_usuario(cls, uid, activo):
        try:
            with sqlite3.connect(str(cls._get_db_path())) as conn:
                conn.execute("UPDATE usuarios SET activo=? WHERE id=?", (activo, uid))
                conn.commit()
            return True
        except Exception as e: logging.error(e); return False


# ==============================================================================
# HELPER DE VIDEO — reutilizable en login Y dashboard
# ==============================================================================

class VideoPlayer:
    """
    Reproduce un video MP4 en loop dentro de un tk.Label.
    Uso:
        player = VideoPlayer(label_widget, video_path)
        player.start()
        player.stop()   # llamar antes de destroy()
    """
    def __init__(self, label: tk.Label, path, bg_color="#ffffff"):
        self.label     = label
        self.path      = str(path)
        self.bg_color  = bg_color
        self._cap      = None
        self._after_id = None
        self._running  = False

    def start(self):
        if not CV2_OK or not PIL_OK:
            return
        try:
            self._cap = cv2.VideoCapture(self.path)
            if not self._cap.isOpened():
                logging.warning(f"No se pudo abrir video: {self.path}")
                return
            self._running = True
            self._tick()
        except Exception as e:
            logging.warning(f"VideoPlayer.start error: {e}")

    def stop(self):
        self._running = False
        if self._after_id:
            try:
                self.label.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def _tick(self):
        if not self._running or not self._cap:
            return
        # Verificar que el widget todavía existe
        try:
            if not self.label.winfo_exists():
                self.stop(); return
        except Exception:
            self.stop(); return

        ret, frame = self._cap.read()
        if not ret:                         # fin del video → loop
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
            if not ret:
                self.stop(); return

        try:
            w = max(self.label.winfo_width(),  10)
            h = max(self.label.winfo_height(), 10)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((w, h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.label.configure(image=photo, bg=self.bg_color)
            self.label.image = photo        # evitar GC
        except Exception:
            pass

        fps   = self._cap.get(cv2.CAP_PROP_FPS) or 30
        delay = max(20, int(1000 / fps))
        self._after_id = self.label.after(delay, self._tick)


def _get_video_path():
    """Devuelve la ruta del MP4 si existe, o None."""
    try:
        from config.settings import RESOURCES_DIR
        p = RESOURCES_DIR / "escudo_vector_farmacia_tecnologia.mp4"
    except ImportError:
        p = Path("resources") / "escudo_vector_farmacia_tecnologia.mp4"
    return p if p.exists() else None


# ==============================================================================
# VENTANA DE LOGIN
# ==============================================================================

class LoginWindow:
    """
    Pantalla de inicio de sesión.
    Layout: panel izquierdo blanco con branding + video | panel derecho formulario.
    """

    def __init__(self, on_login_success):
        self.on_login_success    = on_login_success
        self._usuario_autenticado = None
        self._video_player        = None

        AuthManager.inicializar_tabla_usuarios()

        self.root = ctk.CTk()
        self.root.title("FarmaTrack – Iniciar Sesión")
        self.root.resizable(False, False)
        self.root.configure(fg_color="#ffffff")   # fondo blanco

        self._setup_ui()
        self._iniciar_video()

        self.root.update_idletasks()
        w = max(self.root.winfo_reqwidth(), 860)
        h = max(self.root.winfo_reqheight(), 540)
        x = (self.root.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # ── Panel izquierdo: BLANCO con branding + video ──────────────────────
        self.panel_left = ctk.CTkFrame(
            self.root, fg_color="#ffffff",
            corner_radius=0, width=400,
        )
        self.panel_left.pack(side="left", fill="both")
        self.panel_left.pack_propagate(False)

        # Barra azul superior en el panel izquierdo
        barra = ctk.CTkFrame(self.panel_left, fg_color=Colors.PRIMARY,
                             corner_radius=0, height=6)
        barra.pack(fill="x")

        ctk.CTkFrame(self.panel_left, fg_color="transparent", height=30).pack()

        ctk.CTkLabel(
            self.panel_left, text="💊",
            font=("Segoe UI", 52),
        ).pack()

        ctk.CTkLabel(
            self.panel_left, text="FarmaTrack",
            font=(Fonts.FAMILY, 28, "bold"),
            text_color=Colors.PRIMARY,
        ).pack(pady=(6, 2))

        ctk.CTkLabel(
            self.panel_left, text="Droguería Irlandesa",
            font=(Fonts.FAMILY, 13),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=(0, 16))

        # ── Contenedor del video (debajo del label) ───────────────────────────
        self.video_frame = ctk.CTkFrame(
            self.panel_left, fg_color="#ffffff",
            corner_radius=10,
            border_width=1, border_color=Colors.BORDER,
        )
        self.video_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # tk.Label nativo para mostrar los frames
        self.video_label = tk.Label(
            self.video_frame, bg="#ffffff", bd=0, cursor="none",
        )
        self.video_label.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(
            self.panel_left,
            text="v2.0  •  Sistema POS",
            font=(Fonts.FAMILY, 10),
            text_color="#aaaaaa",
        ).pack(pady=(0, 14))

        # ── Divisor vertical ──────────────────────────────────────────────────
        ctk.CTkFrame(
            self.root, fg_color=Colors.BORDER,
            corner_radius=0, width=1,
        ).pack(side="left", fill="y")

        # ── Panel derecho: formulario ─────────────────────────────────────────
        panel_right = ctk.CTkFrame(
            self.root, fg_color="#f4f6f8",
            corner_radius=0, width=460,
        )
        panel_right.pack(side="right", fill="both", expand=True)
        panel_right.pack_propagate(False)

        card = ctk.CTkFrame(
            panel_right, fg_color="#ffffff",
            corner_radius=16,
            border_width=1, border_color=Colors.BORDER,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.84, relheight=0.74)

        ctk.CTkLabel(
            card, text="Iniciar Sesión",
            font=(Fonts.FAMILY, 22, "bold"),
            text_color=Colors.PRIMARY,
        ).pack(pady=(32, 4))

        ctk.CTkLabel(
            card, text="Ingresa tus credenciales para continuar",
            font=(Fonts.FAMILY, 12),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=(0, 28))

        ctk.CTkLabel(card, text="Usuario", font=(Fonts.FAMILY, 12),
                     text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", padx=36)
        self.entry_user = ctk.CTkEntry(
            card, placeholder_text="nombre de usuario",
            height=Dimensions.INPUT_HEIGHT, corner_radius=8,
            border_color=Colors.BORDER, font=Fonts.BODY,
        )
        self.entry_user.pack(fill="x", padx=36, pady=(4, 16))
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus())

        ctk.CTkLabel(card, text="Contraseña", font=(Fonts.FAMILY, 12),
                     text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", padx=36)
        self.entry_pass = ctk.CTkEntry(
            card, placeholder_text="••••••••", show="•",
            height=Dimensions.INPUT_HEIGHT, corner_radius=8,
            border_color=Colors.BORDER, font=Fonts.BODY,
        )
        self.entry_pass.pack(fill="x", padx=36, pady=(4, 24))
        self.entry_pass.bind("<Return>", lambda e: self._intentar_login())

        self.btn_login = ctk.CTkButton(
            card, text="Iniciar Sesión",
            height=Dimensions.BUTTON_HEIGHT,
            corner_radius=Dimensions.BUTTON_RADIUS,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            font=(Fonts.FAMILY, 15, "bold"),
            command=self._intentar_login,
        )
        self.btn_login.pack(fill="x", padx=36, pady=(0, 10))

        self.lbl_error = ctk.CTkLabel(
            card, text="", font=(Fonts.FAMILY, 12), text_color=Colors.ERROR,
        )
        self.lbl_error.pack()

        ctk.CTkLabel(
            card, text="Por defecto: admin / admin123",
            font=(Fonts.FAMILY, 11), text_color="#bbbbbb",
        ).pack(pady=(12, 0))

        self.entry_user.focus()

    # ── Video ─────────────────────────────────────────────────────────────────

    def _iniciar_video(self):
        path = _get_video_path()
        if not path:
            # Sin video: mostrar placeholder de color
            self.video_label.configure(bg=Colors.BACKGROUND,
                                       text="🎬", font=("Segoe UI", 32))
            return
        self._video_player = VideoPlayer(self.video_label, path, bg_color="#ffffff")
        # Esperar a que el frame esté dibujado antes de arrancar
        self.root.after(200, self._video_player.start)

    # ── Login ─────────────────────────────────────────────────────────────────

    def _intentar_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        if not username or not password:
            self.lbl_error.configure(text="⚠  Ingresa usuario y contraseña")
            return

        self.btn_login.configure(text="Verificando...", state="disabled")
        self.root.update()

        usuario = AuthManager.autenticar(username, password)

        if usuario:
            self._usuario_autenticado = usuario
            # 1) Detener video (cancela su after())
            if self._video_player:
                self._video_player.stop()
            # 2) Ocultar ventana
            self.root.withdraw()
            # 3) Dar 100 ms para que CTk limpie sus propios after()
            self.root.after(100, self._finalizar_login)
        else:
            self.lbl_error.configure(text="✗  Usuario o contraseña incorrectos")
            self.btn_login.configure(text="Iniciar Sesión", state="normal")
            self.entry_pass.delete(0, "end")
            self.entry_pass.focus()

    def _finalizar_login(self):
        usuario = self._usuario_autenticado
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        self.on_login_success(usuario)

    def run(self):
        self.root.mainloop()


# ==============================================================================
# GESTIÓN DE USUARIOS (solo admin)
# ==============================================================================

class GestionUsuariosWindow:
    def __init__(self, parent):
        if not AuthManager.es_admin():
            messagebox.showerror("Acceso denegado", "Solo el administrador puede gestionar usuarios.")
            return
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Gestión de Usuarios")
        self.window.geometry("700x500")
        self.window.grab_set()
        self._setup_ui()
        self._cargar_usuarios()

    def _setup_ui(self):
        ctk.CTkLabel(self.window, text="👥  Gestión de Usuarios",
                     font=(Fonts.FAMILY, 20, "bold"),
                     text_color=Colors.PRIMARY).pack(pady=(20, 10))

        fb = ctk.CTkFrame(self.window, fg_color="transparent")
        fb.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkButton(fb, text="➕  Nuevo Usuario",
                      fg_color=Colors.SUCCESS, hover_color="#0a6b0a",
                      command=self._nuevo_usuario, height=36, corner_radius=8,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(fb, text="🔑  Cambiar Contraseña",
                      fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
                      command=self._cambiar_pass, height=36, corner_radius=8,
        ).pack(side="left")

        import tkinter.ttk as ttk
        style = ttk.Style()
        style.configure("GU.Treeview", font=("Segoe UI",12), rowheight=28)
        style.configure("GU.Treeview.Heading", font=("Segoe UI",12,"bold"))

        ft = tk.Frame(self.window)
        ft.pack(fill="both", expand=True, padx=20, pady=(0,10))
        cols = ("ID","Usuario","Nombre","Rol","Estado")
        self.tree = ttk.Treeview(ft, columns=cols, show="headings",
                                  style="GU.Treeview", height=12)
        for col, w in zip(cols, [40,120,200,80,80]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)

        ctk.CTkButton(self.window, text="⏸  Activar / Desactivar seleccionado",
                      fg_color="#e65100", hover_color="#bf360c",
                      command=self._toggle_usuario, height=36, corner_radius=8,
        ).pack(pady=(0,20))

    def _cargar_usuarios(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for u in AuthManager.obtener_usuarios():
            self.tree.insert("","end", values=(
                u["id"], u["username"], u["nombre"],
                u["rol"].capitalize(),
                "✅ Activo" if u["activo"] else "⛔ Inactivo"
            ))

    def _nuevo_usuario(self):
        dlg = ctk.CTkToplevel(self.window)
        dlg.title("Nuevo Usuario"); dlg.geometry("380x330"); dlg.grab_set()
        entries = {}
        for lbl in ("Usuario","Nombre completo","Contraseña"):
            ctk.CTkLabel(dlg, text=lbl, font=Fonts.BODY, anchor="w").pack(fill="x", padx=30, pady=(10,2))
            e = ctk.CTkEntry(dlg, height=36, show="•" if lbl=="Contraseña" else "")
            e.pack(fill="x", padx=30); entries[lbl] = e
        ctk.CTkLabel(dlg, text="Rol", font=Fonts.BODY, anchor="w").pack(fill="x", padx=30, pady=(10,2))
        rol_var = tk.StringVar(value="cajero")
        ctk.CTkOptionMenu(dlg, values=["cajero","admin"], variable=rol_var, height=36).pack(fill="x", padx=30)
        def guardar():
            u,n,p = entries["Usuario"].get().strip(), entries["Nombre completo"].get().strip(), entries["Contraseña"].get()
            if not all([u,n,p]):
                messagebox.showerror("Error","Todos los campos son obligatorios",parent=dlg); return
            if len(p)<6:
                messagebox.showerror("Error","Mínimo 6 caracteres",parent=dlg); return
            if AuthManager.crear_usuario(u,p,n,rol_var.get()):
                dlg.destroy(); self._cargar_usuarios()
                messagebox.showinfo("Éxito",f"Usuario '{u}' creado")
            else:
                messagebox.showerror("Error",f"El usuario '{u}' ya existe")
        ctk.CTkButton(dlg, text="Crear Usuario", command=guardar,
                      fg_color=Colors.SUCCESS, height=40, corner_radius=8
        ).pack(pady=16, padx=30, fill="x")

    def _cambiar_pass(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Atención","Selecciona un usuario"); return
        username = self.tree.item(sel[0],"values")[1]
        dlg = ctk.CTkToplevel(self.window)
        dlg.title(f"Cambiar contraseña – {username}"); dlg.geometry("350x220"); dlg.grab_set()
        ctk.CTkLabel(dlg, text="Nueva contraseña:", font=Fonts.BODY).pack(pady=(20,4))
        p1 = ctk.CTkEntry(dlg, show="•", height=36); p1.pack(padx=30, fill="x")
        ctk.CTkLabel(dlg, text="Confirmar:", font=Fonts.BODY).pack(pady=(12,4))
        p2 = ctk.CTkEntry(dlg, show="•", height=36); p2.pack(padx=30, fill="x")
        def guardar():
            a,b = p1.get(), p2.get()
            if a!=b: messagebox.showerror("Error","No coinciden",parent=dlg); return
            if len(a)<6: messagebox.showerror("Error","Mínimo 6 caracteres",parent=dlg); return
            if AuthManager.cambiar_password(username,a):
                dlg.destroy(); messagebox.showinfo("Éxito",f"Contraseña de '{username}' actualizada")
        ctk.CTkButton(dlg, text="Guardar", command=guardar,
                      fg_color=Colors.PRIMARY, height=40, corner_radius=8
        ).pack(pady=16, padx=30, fill="x")

    def _toggle_usuario(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Atención","Selecciona un usuario"); return
        vals = self.tree.item(sel[0],"values")
        uid, username, activo_actual = vals[0], vals[1], "Activo" in vals[4]
        if username == AuthManager.usuario_actual().get("username"):
            messagebox.showerror("Error","No puedes desactivar tu propio usuario"); return
        if AuthManager.toggle_usuario(uid, 0 if activo_actual else 1):
            self._cargar_usuarios()