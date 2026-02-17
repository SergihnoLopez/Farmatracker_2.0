import customtkinter as ctk

# ==============================
# DESIGN SYSTEM (INTEGRADO)
# ==============================

class Colors:
    BACKGROUND = "#f4f6f8"
    SURFACE = "#ffffff"
    PANEL = "#fafafa"
    BORDER = "#e3e6ea"

    PRIMARY = "#0f6cbd"
    PRIMARY_HOVER = "#0c5aa6"

    TEXT_PRIMARY = "#1a1a1a"
    TEXT_SECONDARY = "#616161"


class Typography:
    TITLE = ("Segoe UI", 28, "bold")
    SUBTITLE = ("Segoe UI", 14)
    BODY = ("Segoe UI", 14)
    BUTTON = ("Segoe UI", 14, "bold")


class Radius:
    CARD = 10
    BUTTON = 8


class Spacing:
    XL = 50
    LG = 30
    MD = 20
    SM = 10


# ==============================
# COMPONENTES
# ==============================

class PrimaryButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None):
        super().__init__(
            parent,
            text=text,
            command=command,
            height=46,
            corner_radius=Radius.BUTTON,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color="white",
            font=Typography.BUTTON
        )


class SidebarButton(ctk.CTkButton):
    def __init__(self, parent, text, active=False):
        super().__init__(
            parent,
            text=text,
            height=42,
            corner_radius=Radius.BUTTON,
            fg_color=Colors.PRIMARY if active else "transparent",
            hover_color="#e8f2fb",
            text_color="white" if active else Colors.TEXT_SECONDARY,
            anchor="w",
            font=Typography.BODY
        )


class Card(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=Colors.SURFACE,
            corner_radius=Radius.CARD
        )


# ==============================
# APP PREVIEW
# ==============================

ctk.set_appearance_mode("light")

root = ctk.CTk()
root.geometry("1200x700")
root.title("Farmatracker – Preview Profesional")
root.configure(fg_color=Colors.BACKGROUND)

# ===== SIDEBAR =====
sidebar = ctk.CTkFrame(root, width=240, fg_color=Colors.SURFACE, corner_radius=0)
sidebar.pack(side="left", fill="y")

ctk.CTkLabel(
    sidebar,
    text="Farmatracker",
    font=("Segoe UI", 22, "bold"),
    text_color=Colors.TEXT_PRIMARY
).pack(pady=(Spacing.XL, Spacing.XL))

SidebarButton(sidebar, "Dashboard", active=True).pack(fill="x", padx=25, pady=6)
SidebarButton(sidebar, "Inventario").pack(fill="x", padx=25, pady=6)
SidebarButton(sidebar, "Ventas").pack(fill="x", padx=25, pady=6)
SidebarButton(sidebar, "Reportes").pack(fill="x", padx=25, pady=6)
SidebarButton(sidebar, "Configuración").pack(fill="x", padx=25, pady=6)

# ===== MAIN =====
main = ctk.CTkFrame(root, fg_color=Colors.BACKGROUND, corner_radius=0)
main.pack(side="right", expand=True, fill="both")

ctk.CTkLabel(
    main,
    text="Dashboard",
    font=Typography.TITLE,
    text_color=Colors.TEXT_PRIMARY
).pack(pady=(Spacing.XL, Spacing.LG), padx=60, anchor="w")

# ===== CARD 1 =====
card1 = Card(main)
card1.pack(padx=60, pady=Spacing.MD, fill="x")

ctk.CTkLabel(
    card1,
    text="Ventas del día",
    font=Typography.SUBTITLE,
    text_color=Colors.TEXT_SECONDARY
).pack(anchor="w", padx=30, pady=(Spacing.LG, 5))

ctk.CTkLabel(
    card1,
    text="$12,540",
    font=("Segoe UI", 30, "bold"),
    text_color=Colors.TEXT_PRIMARY
).pack(anchor="w", padx=30, pady=(0, Spacing.LG))

# ===== CARD 2 =====
card2 = Card(main)
card2.pack(padx=60, pady=Spacing.MD, fill="x")

ctk.CTkLabel(
    card2,
    text="Productos con stock bajo",
    font=Typography.SUBTITLE,
    text_color=Colors.TEXT_SECONDARY
).pack(anchor="w", padx=30, pady=(Spacing.LG, 5))

ctk.CTkLabel(
    card2,
    text="8 productos requieren reposición",
    font=Typography.BODY,
    text_color=Colors.TEXT_PRIMARY
).pack(anchor="w", padx=30, pady=(0, Spacing.LG))

# ===== BOTÓN PRINCIPAL =====
PrimaryButton(main, "Registrar Nueva Venta").pack(
    padx=60,
    pady=Spacing.LG,
    anchor="w"
)

root.mainloop()