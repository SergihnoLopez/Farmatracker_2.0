"""
Ventana de gestión de backups
Permite crear, restaurar, listar y eliminar respaldos de la base de datos
"""
from tkinter import (Toplevel, Frame, Label, Button, Entry, messagebox,
                     Scrollbar, BOTH, LEFT, RIGHT, Y, VERTICAL, W, END)
from tkinter import ttk
from config.settings import FONT_STYLE, BTN_COLOR, BTN_FG
from utils.backup import BackupManager
import logging


class BackupWindow:
    """Ventana para gestión de backups"""

    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Gestión de Respaldos")
        self.window.geometry("900x600")

        self.backup_manager = BackupManager()

        self._setup_ui()
        self._cargar_backups()

    def _setup_ui(self):
        """Configura la interfaz de usuario"""

        # ============================================================
        # FRAME SUPERIOR - INFORMACIÓN Y BOTÓN CREAR BACKUP
        # ============================================================
        frame_superior = Frame(self.window)
        frame_superior.pack(fill='x', padx=10, pady=10)

        Label(
            frame_superior,
            text="💾 Sistema de Respaldos de Base de Datos",
            font=("Titillium Web", 16, "bold"),
            fg="#2196F3"
        ).pack(pady=(0, 10))

        Label(
            frame_superior,
            text="Los respaldos se crean automáticamente antes de operaciones críticas.\n"
                 "También puedes crear respaldos manuales aquí.",
            font=("Arial", 10),
            fg="#666666"
        ).pack()

        # Frame para crear backup manual
        frame_crear = Frame(frame_superior)
        frame_crear.pack(pady=10)

        Label(
            frame_crear,
            text="Descripción (opcional):",
            font=FONT_STYLE
        ).pack(side=LEFT, padx=5)

        self.entry_descripcion = Entry(frame_crear, font=FONT_STYLE, width=30)
        self.entry_descripcion.pack(side=LEFT, padx=5)

        Button(
            frame_crear,
            text="🔒 Crear Backup Manual",
            font=FONT_STYLE,
            bg="#4CAF50",
            fg="white",
            command=self._crear_backup_manual,
            width=20
        ).pack(side=LEFT, padx=5)

        Button(
            frame_crear,
            text="🔄 Actualizar Lista",
            font=FONT_STYLE,
            bg="#2196F3",
            fg="white",
            command=self._cargar_backups,
            width=15
        ).pack(side=LEFT, padx=5)

        # ============================================================
        # FRAME TABLA DE BACKUPS
        # ============================================================
        Label(
            self.window,
            text="📋 Respaldos Disponibles",
            font=("Titillium Web", 12, "bold")
        ).pack(pady=(10, 5))

        frame_tabla = Frame(self.window)
        frame_tabla.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Columnas
        columnas = ("Tipo", "Fecha", "Descripción", "Tamaño", "Archivo")

        # Crear Treeview
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)

        # Configurar encabezados
        anchos = {
            "Tipo": 100,
            "Fecha": 150,
            "Descripción": 200,
            "Tamaño": 100,
            "Archivo": 250
        }

        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=anchos[col], anchor='w')

        # Scrollbar
        scrollbar = Scrollbar(frame_tabla, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Posicionar
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # ============================================================
        # FRAME BOTONES DE ACCIÓN
        # ============================================================
        frame_botones = Frame(self.window)
        frame_botones.pack(pady=10)

        Button(
            frame_botones,
            text="♻️ Restaurar Seleccionado",
            font=FONT_STYLE,
            bg="#FF9800",
            fg="white",
            command=self._restaurar_backup,
            width=20
        ).pack(side=LEFT, padx=5)

        Button(
            frame_botones,
            text="🗑️ Eliminar Seleccionado",
            font=FONT_STYLE,
            bg="#f44336",
            fg="white",
            command=self._eliminar_backup,
            width=20
        ).pack(side=LEFT, padx=5)

        # ============================================================
        # FRAME INFORMACIÓN
        # ============================================================
        frame_info = Frame(self.window, bg="#E3F2FD", relief="ridge", bd=2)
        frame_info.pack(fill='x', padx=10, pady=5)

        info_text = (
            "ℹ️ IMPORTANTE:\n"
            "• Los backups automáticos se crean antes de: Reseteo de stock, Actualizaciones masivas\n"
            "• Se mantienen los últimos 10 backups automáticamente\n"
            "• RESTAURAR un backup reemplazará la base de datos actual (se crea backup de seguridad)"
        )

        Label(
            frame_info,
            text=info_text,
            font=("Arial", 9),
            bg="#E3F2FD",
            fg="#1976D2",
            justify=LEFT,
            anchor=W
        ).pack(padx=10, pady=5, fill='x')

        # Doble clic para restaurar
        self.tree.bind("<Double-1>", lambda e: self._restaurar_backup())

    def _cargar_backups(self):
        """Carga la lista de backups en el treeview"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Obtener backups
        backups = self.backup_manager.listar_backups()

        if not backups:
            messagebox.showinfo(
                "Sin backups",
                "No hay backups disponibles.\n\nCrea un backup manual para empezar."
            )
            return

        # Mapeo de tipos para visualización
        tipo_map = {
            "manual": "📝 Manual",
            "auto": "⚙️ Auto",
            "pre_op": "🔒 Pre-Op"
        }

        # Insertar backups
        for backup in backups:
            tipo_display = tipo_map.get(backup['tipo'], backup['tipo'])

            self.tree.insert("", "end", values=(
                tipo_display,
                backup['fecha'],
                backup['descripcion'],
                backup['tamaño'],
                backup['archivo']
            ), tags=(str(backup['ruta']),))  # Guardar ruta en tags

    def _crear_backup_manual(self):
        """Crea un backup manual"""
        descripcion = self.entry_descripcion.get().strip()

        # Confirmar
        mensaje = "¿Crear backup manual de la base de datos?"
        if descripcion:
            mensaje += f"\n\nDescripción: {descripcion}"

        if not messagebox.askyesno("Confirmar", mensaje):
            return

        # Crear backup
        backup_path = self.backup_manager.crear_backup(
            tipo=BackupManager.MANUAL,
            descripcion=descripcion
        )

        if backup_path:
            messagebox.showinfo(
                "✅ Backup Creado",
                f"Backup creado exitosamente:\n\n{backup_path.name}"
            )

            # Limpiar entrada y recargar lista
            self.entry_descripcion.delete(0, END)
            self._cargar_backups()
        else:
            messagebox.showerror(
                "❌ Error",
                "No se pudo crear el backup.\n\nRevisa el archivo de log para más detalles."
            )

    def _restaurar_backup(self):
        """Restaura el backup seleccionado"""
        # Verificar selección
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un backup para restaurar")
            return

        # Obtener ruta del backup
        item = selected[0]
        ruta_str = self.tree.item(item, 'tags')[0]

        from pathlib import Path
        ruta_backup = Path(ruta_str)

        # Advertencia crítica
        confirmacion = messagebox.askyesno(
            "⚠️ ADVERTENCIA CRÍTICA",
            "RESTAURAR UN BACKUP:\n\n"
            "• Reemplazará TODA la base de datos actual\n"
            "• Se creará un backup de seguridad antes de restaurar\n"
            "• Todas las ventanas deben estar cerradas\n"
            "• Todas las operaciones deben estar completadas\n\n"
            f"Backup a restaurar:\n{ruta_backup.name}\n\n"
            "¿Está SEGURO de continuar?",
            icon='warning'
        )

        if not confirmacion:
            return

        # Segunda confirmación
        confirmacion2 = messagebox.askyesno(
            "Confirmación Final",
            "Esta es su última oportunidad para cancelar.\n\n"
            "¿Proceder con la restauración?",
            icon='warning'
        )

        if not confirmacion2:
            return

        # Restaurar
        if self.backup_manager.restaurar_backup(ruta_backup):
            messagebox.showinfo(
                "✅ Restauración Exitosa",
                "El backup se restauró correctamente.\n\n"
                "Se recomienda REINICIAR la aplicación para evitar problemas."
            )
            self._cargar_backups()
        else:
            messagebox.showerror(
                "❌ Error en Restauración",
                "No se pudo restaurar el backup.\n\n"
                "La base de datos actual permanece sin cambios.\n"
                "Revisa el archivo de log para más detalles."
            )

    def _eliminar_backup(self):
        """Elimina el backup seleccionado"""
        # Verificar selección
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un backup para eliminar")
            return

        # Obtener información
        item = selected[0]
        ruta_str = self.tree.item(item, 'tags')[0]
        valores = self.tree.item(item, 'values')

        from pathlib import Path
        ruta_backup = Path(ruta_str)

        # Confirmar
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Eliminar este backup?\n\n"
            f"Tipo: {valores[0]}\n"
            f"Fecha: {valores[1]}\n"
            f"Archivo: {valores[4]}\n\n"
            "Esta acción NO se puede deshacer."
        )

        if not confirmacion:
            return

        # Eliminar
        if self.backup_manager.eliminar_backup(ruta_backup):
            messagebox.showinfo("✅ Eliminado", "Backup eliminado correctamente")
            self._cargar_backups()
        else:
            messagebox.showerror("❌ Error", "No se pudo eliminar el backup")
