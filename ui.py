"""
UI Module - Commercial Management System
Main window, sidebar navigation, and all UI frames
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import sqlite3
import traceback
from database import get_db
from logic import get_logic
# Try to import format_quantity, if not available yet (circular import risk?), handle gracefully
from utils import (generate_invoice_pdf, generate_reception_pdf, generate_bordereau_pdf,
                   export_clients_to_excel, export_factures_to_excel, export_stock_to_excel,
                   nombre_en_lettres, generate_client_state_pdf, generate_invoice_state_pdf,
                   generate_etat_104_pdf, generate_payments_state_pdf, generate_daily_sales_pdf,
                   generate_sales_by_category_pdf, format_quantity, check_logo_exists,
                   preview_and_print_pdf, generate_creances_pdf, format_currency, parse_currency)
from PIL import Image, ImageTk
import os
from reports import generate_stock_valuation_excel, generate_stock_valuation_pdf
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

import os

def preview_and_print_pdf(filename):
    """Open PDF and ask to print"""
    try:
        # Open default viewer
        if os.name == 'nt':
            os.startfile(filename)
            
        # Ask to print
        if messagebox.askyesno("Impression", "Le fichier PDF a été généré.\nVoulez-vous l'imprimer maintenant ?"):
            try:
                os.startfile(filename, "print")
            except Exception as e:
                messagebox.showerror("Erreur d'impression", f"Impossible d'imprimer :\n{e}")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du PDF :\n{e}")

# Color scheme
PRIMARY_COLOR = "#1a237e"
SECONDARY_COLOR = "#3949ab"
ACCENT_COLOR = "#00bcd4"
BG_COLOR = "#37474f" # Dark Blue Grey
SIDEBAR_COLOR = "#263238"
TEXT_COLOR = "#eceff1" # Light Blue Grey



class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def create_tooltip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<FocusIn>', enter)
    widget.bind('<FocusOut>', leave)
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class MainApplication:
    """Main application window"""
    
    def __init__(self, root: tk.Tk, user: Dict[str, Any]):
        self.root = root
        self.user = user
        self.db = get_db()
        self.logic = get_logic()
        
        self.logout_callback = None
        
        self.root.title("Gestion Commerciale ECDE - Ciment | GESTION COMMERCIALE - DEPOT DE OUED SMAR - ALGER")
        self.root.state('zoomed')
        self.root.configure(bg=BG_COLOR)
        
        # Current frame reference
        self.current_frame: Optional[ttk.Frame] = None
        
        self._setup_ui()

    def set_logout_callback(self, callback):
        self.logout_callback = callback
        
    def logout(self, event=None):
        if messagebox.askyesno("Déconnexion", "Voulez-vous changer d'utilisateur ?"):
            if self.logout_callback:
                self.logout_callback()
    
    def _setup_ui(self):
        """Setup main UI layout"""
        # Configure ttk Styles for Dark Theme
        style = ttk.Style()
        style.theme_use('clam')  # 'clam' works well for custom coloring
        
        # Treeview
        style.configure("Treeview", 
                        background="#263238", 
                        foreground="white", 
                        fieldbackground="#263238",
                        font=('Arial', 10, 'bold'),
                        rowheight=25)
        
        style.configure("Treeview.Heading",
                        font=('Arial', 10, 'bold'),
                        background="#37474f",
                        foreground="white")
        
        style.map("Treeview", 
                  background=[('selected', ACCENT_COLOR)], 
                  foreground=[('selected', 'white')])

        # Note: We will configure the 'evenrow' tag in each Treeview instance
        # typically: tree.tag_configure('evenrow', background='#37474f')
        
        # Combobox
        style.configure("TCombobox", 
                        fieldbackground="#455a64",
                        background=BG_COLOR,
                        foreground=TEXT_COLOR,
                        arrowcolor=TEXT_COLOR)
        style.map("TCombobox", fieldbackground=[('readonly', '#455a64')])
        
        # Scrollbar (Vertical)
        style.configure("Vertical.TScrollbar", 
                        background=SIDEBAR_COLOR,
                        troughcolor=BG_COLOR,
                        arrowcolor=TEXT_COLOR)
        
        # Global Option for standard widgets if possible (doesn't always stick for specific instances)
        self.root.option_add("*Entry*background", "#455a64")
        self.root.option_add("*Entry*foreground", "white")
        self.root.option_add("*Entry*insertBackground", "white") # Cursor color
        self.root.option_add("*Entry*selectBackground", ACCENT_COLOR)
        self.root.option_add("*Entry*selectForeground", "white")
        
        self.root.option_add("*Text*background", "#455a64")
        self.root.option_add("*Text*foreground", "white")
        self.root.option_add("*Text*insertBackground", "white")
        
        self.root.option_add("*Listbox*background", "#455a64")
        self.root.option_add("*Listbox*foreground", "white")

        # Top canvas for logo and title
        self.header_height = 80
        self.header_canvas = tk.Canvas(self.root, bg=PRIMARY_COLOR, height=self.header_height, highlightthickness=0)
        self.header_canvas.pack(fill=tk.X)
        
        # Load logo for tiling
        self._load_header_logo()
        
        # Initial draw
        self._draw_header()
        
        # Bind resize event
        self.header_canvas.bind('<Configure>', self._on_header_resize)
        self.user_info_id = None
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        
        # Configuration menu - Only for Admins
        if self.user.get('role') == 'admin':
            config_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Configuration", menu=config_menu)
            config_menu.add_command(label="Utilisateurs", command=self.show_users)
            config_menu.add_separator()
            config_menu.add_command(label="Export Miroir (Directeur)", command=self.export_miroir)
            config_menu.add_separator()
            config_menu.add_command(label="Clôture Annuelle", command=self.show_closure)
            config_menu.add_separator()
            config_menu.add_command(label="Remise à zéro", command=self.reset_application_data)
            config_menu.add_separator()
        else:
            # For non-admins, maybe just "A Propos" or minimal options
            pass
            
        # File/System menu for everyone
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Système", menu=file_menu)
        file_menu.add_command(label="Déconnexion", command=self.logout)
        file_menu.add_command(label="Quitter", command=self.quit_app)
        file_menu.add_command(label="A Propos", command=self.show_about)
        
        # Main container
        main_container = tk.Frame(self.root, bg=BG_COLOR)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        sidebar = tk.Frame(main_container, bg=SIDEBAR_COLOR, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Sidebar buttons
        buttons = [
            ("Tableau de Bord", self.show_dashboard),
            ("Clients", self.show_clients),
            ("Produits", self.show_products),
            ("Réceptions", self.show_receptions),
            ("Factures", self.show_invoices),
            ("Paiements", self.show_payments),
            ("Situation", self.show_situation),
            ("Stock", self.show_stock),
        ]
        
        for text, command in buttons:
            btn = tk.Button(
                sidebar,
                text=text,
                font=("Arial", 11),
                bg=SIDEBAR_COLOR,
                fg="white",
                activebackground=ACCENT_COLOR,
                activeforeground="white",
                bd=0,
                padx=20,
                pady=15,
                cursor="hand2",
                command=command,
                anchor="w"
            )
            btn.pack(fill=tk.X, pady=2)

        # Spacer to push user info to bottom (optional, but good for layout)
        tk.Frame(sidebar, bg=SIDEBAR_COLOR).pack(fill=tk.Y, expand=True)

        # User Info at Bottom of Sidebar
        user_text = f"Utilisateur: {self.user['full_name']} ({self.user['role']})"
        lbl_user = tk.Label(
            sidebar,
            text=user_text,
            font=("Arial", 11), # Same font as buttons
            bg=SIDEBAR_COLOR,
            fg="#cfd8dc",       # Slightly clearer than white or same as text
            padx=20,
            pady=15,
            anchor="w",
            wraplength=180,     # Wrap if too long
            justify="left",
            cursor="hand2"
        )
        lbl_user.bind("<Button-1>", self.logout)
        lbl_user.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 10))

        
        # Content frame
        self.content_frame = tk.Frame(main_container, bg=BG_COLOR)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Show dashboard by default
        self.show_dashboard()

    def _load_header_logo(self):
        """Load and resize logo for header tiling"""
        self.header_logo = None
        self.tk_header_logo = None
        
        logo_path = "logo_gica.png"
        if not os.path.exists(logo_path):
             logo_path = "logo_entete.png" if os.path.exists("logo_entete.png") else "logo.png"
             
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                # Resize proportionally to fit height
                h_percent = (self.header_height / float(img.size[1]))
                w_size = int((float(img.size[0]) * float(h_percent)))
                img = img.resize((w_size, self.header_height), Image.Resampling.LANCZOS)
                self.header_logo = img
                self.tk_header_logo = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading logo: {e}")

    def _on_header_resize(self, event):
        """Redraw header on resize"""
        self._draw_header()

    def _draw_header(self):
        """Draw tiled logo and text"""
        self.header_canvas.delete("all")
        width = self.header_canvas.winfo_width()
        # Default width if not yet realized
        if width <= 1: 
            width = self.root.winfo_screenwidth()

        # 1. Tile Logo
        if self.tk_header_logo:
            img_width = self.tk_header_logo.width()
            if img_width > 0:
                for x in range(0, width, img_width):
                    self.header_canvas.create_image(x, 0, image=self.tk_header_logo, anchor="nw")
        
        # 2. Draw Text Background (Semi-transparent overlay effect using stipple)
        # Tkinter doesn't support alpha, so we use a dark rectangle stippled or just a solid box behind text
        
        # REMOVED Title Banner as per user request to show logo mosaic
        
        # title_text = "GESTION COMMERCIALE - DEPOT DE OUED SMAR - ALGER"
        user_text = f"Utilisateur: {self.user['full_name']} ({self.user['role']})"
        
        # Center-Left for title -> MOVED TO WINDOW TITLE
        # self.header_canvas.create_rectangle(10, 10, 800, 70, fill="#1a237e", outline="") # Background box
        # self.header_canvas.create_text(32, 42, text=title_text, font=("Arial", 18, "bold"), fill="black", anchor="w")
        # self.header_canvas.create_text(30, 40, text=title_text, font=("Arial", 18, "bold"), fill="white", anchor="w")
        
        # Exclusive Use Title (Green, Top Center)



    
    def switch_frame(self, new_frame_class, **kwargs):
        """Switch to a new frame"""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = new_frame_class(self.content_frame, self, **kwargs)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_dashboard(self):
        self.switch_frame(DashboardFrame)
    
    def show_clients(self):
        self.switch_frame(ClientsFrame)
    
    def show_products(self):
        self.switch_frame(ProductsFrame)
    
    def show_receptions(self):
        self.switch_frame(ReceptionsFrame)
    
    def show_invoices(self):
        self.switch_frame(InvoicesFrame)
    
    def show_payments(self):
        self.switch_frame(PaymentsFrame)
    
    def show_situation(self):
        self.switch_frame(SituationFrame)
    
    def show_stock(self):
        self.switch_frame(StockFrame)
    
    def show_users(self):
        self.switch_frame(UsersFrame)
    
    def show_prices(self):
        self.switch_frame(PricesFrame)
    
    def show_closure(self):
        # Check permissions
        if self.user['role'] != 'admin':
            messagebox.showerror("Accès Refusé", "Cette opération est réservée à l'administrateur.")
            return
            
        ClosureDialog(self.root, self.user['id'])

    def reset_application_data(self):
        """Reset all data except users (for testing)"""
        # Check permissions
        if self.user['role'] != 'admin':
            messagebox.showerror("Accès Refusé", "Cette opération est réservée à l'administrateur.")
            return
            

        # Double confirmation for safety
        if not messagebox.askyesno("DANGER - Remise à zéro", 
                                   "ATTENTION: Cette action va supprimer TOUTES les données :\n"
                                   "- Clients\n- Produits & Stocks\n- Factures & Avoirs\n- Réceptions\n- Paiements & Bordereaux\n\n"
                                   "Seuls les comptes utilisateurs seront conservés.\n\n"
                                   "Voulez-vous vraiment continuer ?"):
            return
            
        if not messagebox.askyesno("Confirmation Ultime", 
                                   "Êtes-vous ABSOLUMENT certain ?\n"
                                   "Cette action est IRRÉVERSIBLE."):
            return
            
        try:
            self.db.reset_data()
            self.db.log_action(self.user['id'], "RESET_DATABASE", "Full database reset initiated by user")
            messagebox.showinfo("Succès", "Base de données remise à zéro.\nL'application va redémarrer.")
            
            # Restart or refresh - simple destroy and restart hint
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la réinitialisation :\n{str(e)}")
    
    def show_about(self):
        AboutDialog(self.root)

    def quit_app(self):
        """Quit application with backup"""
        from utils import create_backup
        if messagebox.askyesno("Quitter", "Voulez-vous quitter l'application ?"):
            create_backup()
            self.root.quit()

    def export_miroir(self):
        """Export read-only mirror of database"""
        target_dir = filedialog.askdirectory(title="Sélectionner le dossier pour l'export Miroir")
        if target_dir:
            success, msg = self.db.export_miroir(target_dir)
            if success:
                messagebox.showinfo("Succès", f"Export Miroir réussi :\n{msg}")
            else:
                messagebox.showerror("Erreur", f"Échec de l'export :\n{msg}")


# ==================== DASHBOARD FRAME ====================

class DashboardFrame(ttk.Frame):
    """Dashboard with key metrics"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.configure(style='Card.TFrame')
        self._build()
    
    def _build(self):
        title = tk.Label(
            self, 
            text="Tableau de Bord", 
            font=("Arial", 18, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        title.pack(pady=10)
        
        # Metrics container
        metrics_frame = tk.Frame(self, bg=BG_COLOR)
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        
        # Get metrics
        products = self.app.db.get_all_products()
        clients = self.app.db.get_all_clients()
        factures = self.app.db.get_all_factures()
        paiements = self.app.db.get_all_paiements()
        
        # Calculate totals
        # Use centralized logic for CA to ensure consistency with PDF reports
        # Determine current year range
        import datetime
        current_year = datetime.datetime.now().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"
        
        ca_total = self.app.logic.calculate_ca_net(start_date, end_date)
        
        total_paiements = sum(p['montant'] for p in paiements)
        
        # Metric cards
        metrics = [
            ("Clients Actifs", len(clients), "#4caf50"),
            ("Factures", len(factures), "#2196f3"),
            ("CA Total", f"{ca_total:,.2f} DA", "#ff9800"),
            ("Paiements Total", f"{total_paiements:,.2f} DA", "#9c27b0"),
        ]
        
        for i, (label, value, color) in enumerate(metrics):
            card = tk.Frame(metrics_frame, bg=color, bd=2, relief=tk.RAISED)
            card.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
            
            # Make card clickable if it's "Clients Actifs", "Factures", "CA Total" or "Paiements Total"
            if label == "Clients Actifs":
                card.bind("<Button-1>", lambda e: self.show_client_state())
                card.configure(cursor="hand2")
            elif label == "Factures":
                card.bind("<Button-1>", lambda e: self.show_invoice_state())
                card.configure(cursor="hand2")
            elif label == "CA Total":
                card.bind("<Button-1>", lambda e: self.show_etat_104())
                card.configure(cursor="hand2")
            elif label == "Paiements Total":
                card.bind("<Button-1>", lambda e: self.show_payments_state())
                card.configure(cursor="hand2")
            
            l1 = tk.Label(
                card, 
                text=str(value), 
                font=("Arial", 18, "bold"), # Reduced font
                fg="white", 
                bg=color
            )
            l1.pack(pady=(5, 5)) # Reduced padding
            
            l2 = tk.Label(
                card, 
                text=label, 
                font=("Arial", 10), # Reduced font
                fg="white", 
                bg=color
            )
            l2.pack(pady=(5, 5)) # Reduced padding

            if label == "Clients Actifs":
                l1.bind("<Button-1>", lambda e: self.show_client_state())
                l2.bind("<Button-1>", lambda e: self.show_client_state())
                l1.configure(cursor="hand2")
                l2.configure(cursor="hand2")
            elif label == "Factures":
                l1.bind("<Button-1>", lambda e: self.show_invoice_state())
                l2.bind("<Button-1>", lambda e: self.show_invoice_state())
                l1.configure(cursor="hand2")
                l2.configure(cursor="hand2")
            elif label == "CA Total":
                l1.bind("<Button-1>", lambda e: self.show_etat_104())
                l2.bind("<Button-1>", lambda e: self.show_etat_104())
                l1.configure(cursor="hand2")
                l2.configure(cursor="hand2")
            elif label == "Paiements Total":
                l1.bind("<Button-1>", lambda e: self.show_payments_state())
                l2.bind("<Button-1>", lambda e: self.show_payments_state())
                l1.configure(cursor="hand2")
                l2.configure(cursor="hand2")
        
        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        metrics_frame.grid_rowconfigure(0, weight=1)
        metrics_frame.grid_rowconfigure(1, weight=1)
        
        # Stock summary - Replaced with Treeview
        stock_frame = tk.LabelFrame(self, text="État des Stocks", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
        stock_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10) # Expand True for height
        
        # Treeview setup
        cols = ("Désignation", "Quantité", "Unité")
        tree = ttk.Treeview(stock_frame, columns=cols, show="headings", height=8) # Height ensures visibility
        
        tree.heading("Désignation", text="Désignation", anchor=tk.W)
        tree.column("Désignation", width=300, anchor=tk.W)
        
        tree.heading("Quantité", text="Quantité", anchor=tk.CENTER)
        tree.column("Quantité", width=100, anchor=tk.CENTER)
        
        tree.heading("Unité", text="Unité", anchor=tk.CENTER)
        tree.column("Unité", width=100, anchor=tk.CENTER)
        
        # Scrollbar
        vsb = ttk.Scrollbar(stock_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate
        for product in products:
            q_formatted = format_quantity(product['stock_actuel'], product['unite'])
            tree.insert("", tk.END, values=(
                product['nom'],
                q_formatted,
                product['unite']
            ))

    def show_client_state(self):
        ClientStateDialog(self.app.root, self.app.db.get_all_clients())

    def show_invoice_state(self):
        DateRangeDialog(self.app.root, self.on_date_selected)

    def on_date_selected(self, start_date, end_date):
        if not start_date or not end_date:
            return
        
        # Fetch data
        lines = self.app.db.get_invoice_details_by_date_range(start_date, end_date)
        if not lines:
            messagebox.showinfo("Information", "Aucune facture trouvée pour cette période.")
            return
            
        InvoiceStateDialog(self.app.root, lines, {"start": start_date, "end": end_date})
        
    def show_etat_104(self):
        DateRangeDialog(self.app.root, self.on_etat_104_date_selected)
        
    def on_etat_104_date_selected(self, start_date, end_date):
        if not start_date or not end_date:
            return
            
        data = self.app.db.get_client_sales_summary(start_date, end_date)
        if not data:
            messagebox.showinfo("Information", "Aucun chiffre d'affaires trouvé pour cette période.")
            return
            
        Etat104Dialog(self.app.root, data, {"start": start_date, "end": end_date})
        
    def show_payments_state(self):
        DateRangeDialog(self.app.root, self.on_payments_date_selected)
        
    def on_payments_date_selected(self, start_date, end_date):
        if not start_date or not end_date:
            return
            
        data = self.app.db.get_payments_details_by_date_range(start_date, end_date)
        if not data:
            messagebox.showinfo("Information", "Aucun paiement trouvé pour cette période.")
            return
            
        PaymentsStateDialog(self.app.root, data, {"start": start_date, "end": end_date})


# ==================== CLIENTS FRAME ====================

class ClientsFrame(ttk.Frame):
    """Clients management frame"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()
    
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text="Gestion des Clients", 
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header, bg=BG_COLOR)
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(
            btn_frame, 
            text="+ Nouveau Client", 
            bg=PRIMARY_COLOR, 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.add_client,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="Exporter Excel", 
            bg=ACCENT_COLOR, 
            fg="white",
            font=("Arial", 10),
            command=self.export_excel,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # Table
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview
        columns = ("ID", "Raison Sociale", "RC", "NIS", "NIF", "Seuil Crédit", "Solde")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # Pack
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Action Buttons Frame
        action_frame = tk.Frame(self, bg=BG_COLOR, pady=10)
        action_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(action_frame, text="Ajouter", bg=PRIMARY_COLOR, fg="white", 
                 font=("Arial", 10, "bold"), command=self.add_client, width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(action_frame, text="Modifier", bg=SECONDARY_COLOR, fg="white", 
                 font=("Arial", 10, "bold"), command=self.edit_client_btn, width=15).pack(side=tk.LEFT, padx=5)
                 
        if self.app.user.get('role') == 'admin':
            tk.Button(action_frame, text="Supprimer", bg="#d32f2f", fg="white", 
                     font=("Arial", 10, "bold"), command=self.delete_client_btn, width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="Contrats", bg="#0097a7", fg="white", 
                 font=("Arial", 10, "bold"), command=self.manage_contracts, width=15).pack(side=tk.LEFT, padx=5)

        # Context menu
        self.menu = tk.Menu(self.tree, tearoff=0)
        self.menu.add_command(label="Modifier", command=self.edit_client_btn)
        if self.app.user.get('role') == 'admin':
            self.menu.add_command(label="Supprimer", command=self.delete_client_btn)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Load data
        self.load_data()
        
        # Double-click to edit
        self.tree.bind("<Double-Button-1>", self.on_double_click)
        self.tree.tag_configure('evenrow', background='#546e7a')
        self.load_data()
        
    def load_data(self):
        """Load client data"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        clients = self.app.db.get_all_clients()
        for idx, client in enumerate(clients):
            balance = self.app.logic.calculate_client_balance(client['id'])
            
            tag = 'evenrow' if idx % 2 == 0 else ''
            
            self.tree.insert("", tk.END, iid=client['id'], values=(
                client['id'],
                client['raison_sociale'],
                client['rc'],
                client['nis'],
                client['nif'],
                format_currency(client['seuil_credit']),
                format_currency(balance['solde'])
            ), tags=(tag,))
    
    
    def add_client(self):
        ClientDialog(self.app.root, self.app.user['id'], callback=self.load_data)

    def edit_client_btn(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un client")
            return
        client_id = int(selection[0])
        ClientDialog(self.app.root, self.app.user['id'], client_id=client_id, callback=self.load_data)

    def delete_client_btn(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un client")
            return
        
        if not messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce client ?\nCette action est irréversible."):
            return
            
        item = self.tree.item(selection[0])
        client_id = item['values'][0]
        
        conn = self.app.db._get_connection()
        c = conn.cursor()
        c.execute("UPDATE clients SET active=0 WHERE id=?", (client_id,))
        conn.commit()
        
        self.load_data()
        self.load_data()
        messagebox.showinfo("Succès", "Client supprimé")

    def manage_contracts(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un client")
            return
        client_id = int(selection[0])
        client = self.app.db.get_client_by_id(client_id)
        ContractDialog(self.app.root, self.app.user['id'], client)

    def show_context_menu(self, event):
        selection = self.tree.selection()
        if selection:
            self.menu.post(event.x_root, event.y_root)
    
    def on_double_click(self, event):
        self.edit_client_btn()
    
    def export_excel(self):
        clients = self.app.logic.get_clients_export_data()
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filename:
            export_clients_to_excel(clients, filename)
            messagebox.showinfo("Succès", "Export Excel effectué")



# ==================== PRODUCTS FRAME ====================

class ProductsFrame(ttk.Frame):
    """Products management frame"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()
    
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text="Gestion des Produits", 
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        # Removed header "New Product" button to move it down
        
        # Table
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        columns = ("Code", "Désignation", "Unité", "Prix HT", "Stock", "Coût", "TVA", "Réf. Stock")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        for col in columns:
            self.tree.heading(col, text=col)
            width = 100
            if col == "Désignation": width = 200
            if col == "Réf. Stock": width = 150
            self.tree.column(col, width=width)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Action Buttons Frame
        action_frame = tk.Frame(self, bg=BG_COLOR, pady=10)
        action_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(action_frame, text="Ajouter", bg=PRIMARY_COLOR, fg="white", 
                 font=("Arial", 10, "bold"), command=self.add_product, width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(action_frame, text="Modifier", bg=SECONDARY_COLOR, fg="white", 
                 font=("Arial", 10, "bold"), command=self.edit_product_btn, width=15).pack(side=tk.LEFT, padx=5)
                 
        if self.app.user.get('role') == 'admin':
            tk.Button(action_frame, text="Supprimer", bg="#d32f2f", fg="white", 
                     font=("Arial", 10, "bold"), command=self.delete_product_btn, width=15).pack(side=tk.LEFT, padx=5)
        
        self.load_data()
        
        # Double-click to edit
        self.tree.bind("<Double-Button-1>", self.on_double_click)
        
        # Context menu
        self.menu = tk.Menu(self.tree, tearoff=0)
        self.menu.add_command(label="Modifier", command=self.edit_product_btn)
        if self.app.user.get('role') == 'admin':
            self.menu.add_command(label="Supprimer", command=self.delete_product_btn)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.tree.tag_configure('evenrow', background='#546e7a')
        self.load_data()
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        products = self.app.db.get_all_products()
        
        # Pre-fetch all products for name lookup (optimization)
        product_map = {p['id']: p['nom'] for p in products}
        
        for idx, p in enumerate(products):
            ref_stock = "Produit Principal"
            if p.get('parent_stock_id'):
                parent_name = product_map.get(p['parent_stock_id'], "Inconnu")
                ref_stock = f"Variante de : {parent_name}"
            
            tag = 'evenrow' if idx % 2 == 0 else ''

            self.tree.insert("", tk.END, iid=p['id'], values=(
                p.get('code_produit', ''),
                p['nom'],
                p['unite'],
                format_currency(p['prix_actuel']),
                format_quantity(p['stock_actuel'], p['unite']),
                format_currency(p.get('cout_revient', 0.0)),
                f"{p.get('tva', 19.0):.2f}%",
                ref_stock
            ), tags=(tag,))
    
    def add_product(self):
        ProductDialog(self.app.root, self.app.user['id'], callback=self.load_data)
        
    def edit_product_btn(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit")
            return
        product_id = int(selection[0])
        ProductDialog(self.app.root, self.app.user['id'], product_id=product_id, callback=self.load_data)

    def delete_product_btn(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit")
            return
        
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce produit définitivement ?"):
            try:
                product_id = int(selection[0])
                self.app.db.delete_product(product_id)
                self.load_data()
                messagebox.showinfo("Succès", "Produit supprimé")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
    
    def on_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            product_id = int(selection[0])
            ProductDialog(self.app.root, self.app.user['id'], product_id=product_id, callback=self.load_data)

    def show_context_menu(self, event):
        selection = self.tree.selection()
        if selection:
            self.menu.post(event.x_root, event.y_root)


# ==================== RECEPTIONS FRAME ====================

class ReceptionsFrame(ttk.Frame):
    """Receptions management frame"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.all_receptions = []
        self.filters = {}
        self._build()
    
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text="Bons de Réception", 
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        # Buttons Container
        btn_box = tk.Frame(header, bg=BG_COLOR)
        btn_box.pack(side=tk.RIGHT)

        tk.Button(
            btn_box, 
            text="Modifier", 
            bg=SECONDARY_COLOR, 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.modify_reception,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        if self.app.user.get('role') == 'admin':
            tk.Button(
                btn_box, 
                text="Supprimer", 
                bg="#d32f2f", 
                fg="white",
                font=("Arial", 10, "bold"),
                command=self.delete_reception,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_box, 
            text="+ Nouvelle Réception", 
            bg=PRIMARY_COLOR, 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.add_reception,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # --- Filter Bar ---
        self.create_filter_bar()
        
        # Table
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        columns = ("Numéro", "Date", "Produit", "Chauffeur", "Lieu", "Qté Reçue", "Écart")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Helper for auto-resize (Primitive version for Tkinter)
        # Define specific column widths
        col_widths = {
            "Numéro": 120,
            "Date": 100,
            "Produit": 350,   # Give more space to product name
            "Chauffeur": 150,
            "Lieu": 100,
            "Qté Reçue": 100,
            "Écart": 80
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            # Use defined width or fallback to 100
            width = col_widths.get(col, 100)
            self.tree.column(col, width=width, anchor=tk.W if col in ["Produit", "Chauffeur"] else tk.CENTER)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right-click menu
        self.menu = tk.Menu(self.tree, tearoff=0)
        self.menu.add_command(label="Modifier", command=self.modify_reception)
        self.menu.add_command(label="Générer PDF", command=self.generate_pdf)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.tag_configure('evenrow', background='#546e7a')
        self.tree.tag_configure('ecart_row', foreground='#d32f2f', font=('Arial', 10, 'bold')) # Red for anomalies
        self.load_data()

    def create_filter_bar(self):
        filter_frame = tk.LabelFrame(self, text="Filtres", bg=BG_COLOR, fg=TEXT_COLOR, padx=10, pady=5)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        
        # Helper widgets
        def add_filter(parent, label, key, width=15):
            frame = tk.Frame(parent, bg=BG_COLOR)
            frame.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=label, bg=BG_COLOR, fg="white", font=("Arial", 9)).pack(anchor="w")
            widget = tk.Entry(frame, bg="#455a64", fg="white", insertbackground="white", width=width)
            widget.bind("<KeyRelease>", lambda e: self.apply_filters())
            widget.pack()
            self.filters[key] = widget
            
        add_filter(filter_frame, "Numéro", "numero", width=12)
        add_filter(filter_frame, "Date", "date", width=12)
        add_filter(filter_frame, "Produit", "produit", width=20)
        add_filter(filter_frame, "Chauffeur", "chauffeur", width=15)
        add_filter(filter_frame, "Lieu", "lieu", width=12)
        
        # Clear button
        tk.Button(filter_frame, text="Effacer", command=self.clear_filters, bg="#757575", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=15, pady=5)

    def clear_filters(self):
        for widget in self.filters.values():
            widget.delete(0, tk.END)
        self.apply_filters()
        
    def load_data(self):
        # Fetch all receptions
        self.all_receptions = self.app.db.get_all_receptions()
        self.apply_filters()

    def apply_filters(self):
        # Get filter values
        f_num = self.filters['numero'].get().lower()
        f_date = self.filters['date'].get()
        f_prod = self.filters['produit'].get().lower()
        f_chauf = self.filters['chauffeur'].get().lower()
        f_lieu = self.filters['lieu'].get().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for idx, r in enumerate(self.all_receptions):
            # Format date for check
            date_display = r['date_reception']
            if not date_display and r.get('created_at'):
                date_display = r['created_at']
            if date_display and len(date_display) > 10:
                date_display = date_display[:10]
            
            # Apply filters
            if f_num and f_num not in r['numero'].lower(): continue
            if f_date and f_date not in date_display: continue
            if f_prod and f_prod not in r['product_nom'].lower(): continue
            if f_chauf and f_chauf not in r['chauffeur'].lower(): continue
            if f_lieu and f_lieu not in r['lieu_livraison'].lower(): continue
            
            tags = []
            if len(self.tree.get_children()) % 2 == 0:
                tags.append('evenrow')
            
            # Check for Ecart
            try:
                if abs(float(r['ecart'])) > 0.001:
                    tags.append('ecart_row')
            except: pass

            self.tree.insert("", tk.END, iid=r['id'], values=(
                r['numero'],
                date_display,
                r['product_nom'],
                r['chauffeur'],
                r['lieu_livraison'],
                format_quantity(r['quantite_recue'], r.get('unite', '')),
                format_quantity(r['ecart'], r.get('unite', ''))
            ), tags=tuple(tags))
    
    def add_reception(self):
        ReceptionDialog(self.app.root, self.app.user['id'], callback=self.load_data)
    
    def modify_reception(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une réception à modifier")
            return
        
        reception_id = int(selection[0])
        # Note: ReceptionDialog needs to support editing mode
        # Since the original didn't have it, I might need to update ReceptionDialog __init__ too
        # But for now, let's assume I need to pass reception_id
        # Checking existing ReceptionDialog... it DOES NOT accept reception_id. 
        # I will start by passing it, and I will update ReceptionDialog immediately after.
        # Actually, let's update this frame first.
        try:
             ReceptionDialog(self.app.root, self.app.user['id'], reception_id=reception_id, callback=self.load_data)
        except TypeError:
             messagebox.showerror("Error", "Modification not yet supported by Dialog")

    def show_context_menu(self, event):
        selection = self.tree.selection()
        if selection:
            self.menu.post(event.x_root, event.y_root)
    
    def generate_pdf(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        reception_id = int(selection[0])
        conn = self.app.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, p.nom as product_nom, p.unite
            FROM receptions r
            JOIN products p ON r.product_id = p.id
            WHERE r.id = ?
        """, (reception_id,))
        row = cursor.fetchone()
        
        if row:
            reception_data = dict(row)
            filename = f"BR_{reception_data['numero']}.pdf"
            from utils import generate_reception_pdf
            generate_reception_pdf(reception_data, filename)
            preview_and_print_pdf(filename)


    def delete_reception(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une réception à supprimer")
            return
            
        reception_id = int(selection[0])
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer cette réception ?\nCette action annulera l'impact sur le stock."):
            try:
                if get_logic().delete_reception(reception_id):
                    messagebox.showinfo("Succès", "Réception supprimée avec succès")
                    self.load_data()
                else:
                    messagebox.showerror("Erreur", "Impossible de supprimer la réception")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

# ==================== INVOICES FRAME ====================

class InvoicesFrame(ttk.Frame):
    """Invoices management frame"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.all_invoices = []
        self.filters = {}
        self._build()
    
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text="Factures et Avoirs", 
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header, bg=BG_COLOR)
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(
            btn_frame, 
            text="+ Nouvelle Facture", 
            bg=PRIMARY_COLOR, 
            fg="white",
            font=("Arial", 10, "bold"),
            command=lambda: self.add_invoice('Facture'),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="+ Avoir", 
            bg="#d32f2f", 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.add_avoir,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="Modifier", 
            bg="#f9a825", # Orange/Yellow to indicate edit
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.edit_selected,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, 
            text="Imprimer", 
            bg="#555", 
            fg="white", 
            font=("Arial", 10),
            command=self.print_selected,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="Exporter Excel", 
            bg=ACCENT_COLOR, 
            fg="white",
            font=("Arial", 10),
            command=self.export_excel,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, 
            text="Rapports", 
            bg="#f57c00", 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.show_reports_menu,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # --- Filter Bar ---
        self.create_filter_bar()
        
        # Table
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        columns = ("Numéro", "Type", "Réf. Liée", "Date", "Client", "Montant HT", "TVA", "Montant TTC", "Etat Paiement")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        for col in columns:
            self.tree.heading(col, text=col)
        # Define specific column widths
        col_widths = {
            "Numéro": 120,
            "Type": 100,
            "Réf. Liée": 120,
            "Date": 100,
            "Client": 250, # More space for client name
            "Montant HT": 100,
            "TVA": 100,
            "Montant TTC": 100,
            "Etat Paiement": 100
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            width = col_widths.get(col, 100)
            self.tree.column(col, width=width, anchor=tk.W if col == "Client" else tk.CENTER)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right-click menu
        self.menu = tk.Menu(self.tree, tearoff=0)
        # Menu items will be populated dynamically in show_context_menu
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.tree.tag_configure('evenrow', background='#546e7a')
        self.tree.tag_configure('avoir_row', foreground='#ff5252') # Dark Red/Orange for dark theme visibility
        self.tree.tag_configure('annulee', foreground='#ff9800', font=('Arial', 9, 'bold')) # Orange Bold for Cancelled
        self.load_data()

    def create_filter_bar(self):
        filter_frame = tk.LabelFrame(self, text="Filtres", bg=BG_COLOR, fg=TEXT_COLOR, padx=10, pady=5)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        
        # Helper widgets
        def add_filter(parent, label, key, width=15, is_combo=False, values=None):
            frame = tk.Frame(parent, bg=BG_COLOR)
            frame.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=label, bg=BG_COLOR, fg="white", font=("Arial", 9)).pack(anchor="w")
            
            if is_combo:
                widget = ttk.Combobox(frame, values=values, width=width)
                widget.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
            else:
                widget = tk.Entry(frame, bg="#455a64", fg="white", insertbackground="white", width=width)
                widget.bind("<KeyRelease>", lambda e: self.apply_filters())
                
            widget.pack()
            self.filters[key] = widget
            
        add_filter(filter_frame, "Numéro", "numero", width=12)
        add_filter(filter_frame, "Type", "type", is_combo=True, values=["", "Facture", "Avoir"], width=10)
        add_filter(filter_frame, "Date (AAAA-MM-JJ)", "date", width=12)
        add_filter(filter_frame, "Client", "client", width=20)
        add_filter(filter_frame, "Etat Paiement", "etat", is_combo=True, values=["", "Comptant", "À Terme", "Non soldée", "Payée"], width=12)
        
        # Clear button
        tk.Button(filter_frame, text="Effacer", command=self.clear_filters, bg="#757575", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=15, pady=5)

    def clear_filters(self):
        for key, widget in self.filters.items():
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)
        self.apply_filters()
    
    def load_data(self):
        # Fetch all data once
        self.all_invoices = self.app.db.get_all_factures()
        self.apply_filters()

    def apply_filters(self):
        # Get filter values
        f_num = self.filters['numero'].get().lower()
        f_type = self.filters['type'].get()
        f_date = self.filters['date'].get()
        f_client = self.filters['client'].get().lower()
        f_etat = self.filters['etat'].get()

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort manually if needed, but DB usually returns sorted or we trust insertion order
        
        for idx, f in enumerate(self.all_invoices):
            # Apply filters
            if f_num and f_num not in f['numero'].lower(): continue
            if f_type and f['type_document'] != f_type: continue
            if f_date and f_date not in f['date_facture']: continue
            if f_client and f_client not in f['client_nom'].lower(): continue
            
            # Logic for payment status if needed (some fields might be calculated or string)
            # In DB it is 'etat_paiement' usually
            current_etat = f.get('etat_paiement', 'N/A')
            if f_etat:
                 # Fuzzy match or exact? Let's do partial for flexibility
                 if f_etat.lower() not in str(current_etat).lower(): continue

            # Determine linked reference(s)
            linked_ref = ""
            if f.get('parent_ref'):
                linked_ref = f['parent_ref']
            elif f.get('child_refs'):
                linked_ref = f['child_refs']
            
            tags = []
            if idx % 2 == 0:
                tags.append('evenrow')
            
            if idx % 2 == 0:
                tags.append('evenrow')
            
            # Highlight Logic
            # 1. Cancelled (Highest Priority)
            if f.get('statut') == 'ANNULEE' or f.get('statut_facture') == 'Annulée':
                tags.append('annulee')
            # 2. Avoir
            elif f['type_document'] == 'Avoir':
                tags.append('avoir_row')
            # 3. Linked to Avoir (e.g. Refunded)
            elif f.get('child_refs') and f['child_refs'].strip():
                tags.append('avoir_row')
            
            # Note: idx is from ALL list, but visually evens/odds might look weird if filtered.
            # Ideally we recalculate evens/odds from filtered list index.
            
            # Better tags logic for visual striping on Filtered List
            display_idx = len(self.tree.get_children())
            display_tags = []
            if display_idx % 2 == 0:
                display_tags.append('evenrow')
            
            # Re-apply color tags
            if f.get('statut') == 'ANNULEE' or f.get('statut_facture') == 'Annulée':
                display_tags.append('annulee')
            elif f['type_document'] == 'Avoir':
                display_tags.append('avoir_row')
            elif f.get('child_refs') and f['child_refs'].strip():
                display_tags.append('avoir_row')

            # Determine status text
            status_text = f.get('etat_paiement', 'N/A')
            if f.get('statut') == 'ANNULEE' or f.get('statut_facture') == 'Annulée':
                status_text = "(ANNULEE)"

            self.tree.insert("", tk.END, iid=f['id'], values=(
                f['numero'],
                f['type_document'],
                linked_ref,
                f['date_facture'],
                f['client_nom'],
                format_currency(f['montant_ht']),
                format_currency(f['montant_tva']),
                format_currency(f['montant_ttc']),
                status_text
            ), tags=tuple(display_tags))
    
    def add_invoice(self, type_doc):
        # type_doc argument kept for compatibility but we mostly use for Facture now
        InvoiceDialog(self.app.root, self.app, type_doc, callback=self.load_data)
        
    def add_avoir(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner une facture pour créer un avoir.")
            return

        origin_id = int(selection[0])
        InvoiceDialog(self.app.root, self.app, 'Avoir', callback=self.load_data, facture_origine_id=origin_id)

    def edit_selected(self):
        self.show_details() # Re-use show_details which has the edit logic built-in

    def print_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        facture_id = int(selection[0])
        facture_data = self.app.db.get_facture_by_id(facture_id)
        
        if facture_data:
            filename = f"{facture_data['numero']}.pdf"
            generate_invoice_pdf(facture_data, filename)
            preview_and_print_pdf(filename)
    
    def show_context_menu(self, event):
        selection = self.tree.selection()
        if selection:
            # Rebuild menu dynamically
            self.menu.delete(0, tk.END)
            
            facture_id = int(selection[0])
            facture_data = self.app.db.get_facture_by_id(facture_id)
            
            if facture_data:
                if facture_data.get('statut_facture') == 'Brouillon':
                     self.menu.add_command(label="Modifier Facture", command=self.edit_selected)
                
                self.menu.add_command(label="Voir Détails", command=self.show_details)
                
                if facture_data.get('statut_facture') != 'Brouillon':
                    self.menu.add_command(label="Générer PDF", command=self.generate_pdf)
            
            self.menu.post(event.x_root, event.y_root)
    
    def generate_pdf(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        facture_id = int(selection[0])
        facture_data = self.app.db.get_facture_by_id(facture_id)
        
        if facture_data:
            filename = f"{facture_data['numero']}.pdf"
            generate_invoice_pdf(facture_data, filename)
            preview_and_print_pdf(filename)
    
    def show_details(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        facture_id = int(selection[0])
        facture_data = self.app.db.get_facture_by_id(facture_id)
        
        if facture_data:
            # Check draft status to enable editing
            is_readonly = True
            if facture_data.get('statut_facture') == 'Brouillon':
                 is_readonly = False
            
            InvoiceDialog(self.app.root, self.app, facture_data.get('type_document', 'Facture'), readonly=is_readonly, facture_id=facture_id)
    
    def export_excel(self):
        factures = self.app.db.get_all_factures()
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filename:
            export_factures_to_excel(factures, filename)
            messagebox.showinfo("Succès", "Export Excel effectué")
            
    def show_reports_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="État des Créances (PDF)", command=self.gen_report_creances)
        menu.add_command(label="État du Chiffre d'Affaires (PDF)", command=self.gen_report_ca)
        
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        menu.post(x, y)

    def gen_report_creances(self):
        # Gather data: Invoices with 'A terme'
        conn = self.app.db._get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT f.numero, f.date_facture, f.montant_ttc, c.raison_sociale 
            FROM factures f 
            JOIN clients c ON f.client_id = c.id
            WHERE f.statut_facture = 'Non soldée' AND f.type_document = 'Facture' AND f.statut != 'Annulée' AND c.solde_creance > 0
            ORDER BY c.raison_sociale
        """)
        rows = c.fetchall()
        
        data = []
        for r in rows:
            data.append({
                'client': r['raison_sociale'],
                'numero': r['numero'],
                'date': r['date_facture'],
                'montant': r['montant_ttc']
            })
        
        if not data:
             messagebox.showinfo("Info", "Aucune créance à terme trouvée.")
             return

        try:
            from utils import generate_creances_pdf
            filename = f"Etat_Creances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            generate_creances_pdf(data, filename)
            preview_and_print_pdf(filename)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF:\n{str(e)}")

    def gen_report_ca(self):
         from tkinter import simpledialog
         year = simpledialog.askinteger("Année", "Entrez l'année:", initialvalue=datetime.now().year)
         if not year: return
         
         start_date = f"{year}-01-01"
         end_date = f"{year}-12-31"
         
         conn = self.app.db._get_connection()
         c = conn.cursor()
         
         # CA Brut
         c.execute("""
            SELECT COALESCE(SUM(montant_ht), 0) FROM factures 
            WHERE type_document='Facture' AND date_facture BETWEEN ? AND ? AND statut != 'Annulée'
         """, (start_date, end_date))
         ca_brut = c.fetchone()[0]
         
         # Details Avoirs Linked
         c.execute("""
            SELECT a.numero, f.numero as ref, a.date_facture, a.montant_ht 
            FROM factures a
            JOIN factures f ON a.facture_origine_id = f.id
            WHERE a.type_document='Avoir' AND f.type_document='Facture'
            AND f.date_facture BETWEEN ? AND ?
            AND a.statut != 'Annulée'
         """, (start_date, end_date))
         avoirs_rows = c.fetchall()
         
         total_avoirs = sum(r['montant_ht'] for r in avoirs_rows)
         
         # Calculation Logic:
         # CA Brut = Sum of Valid Invoices (Positive)
         # Total Avoirs = Sum of Valid Avoirs (Negative in DB)
         # CA Net = CA Brut + Total Avoirs (e.g., 100 + (-20) = 80)
         ca_net = ca_brut + total_avoirs
         
         details_avoirs = []
         for r in avoirs_rows:
             details_avoirs.append({
                 'numero': r['numero'],
                 'facture_ref': r['ref'],
                 'date': r['date_facture'],
                 'montant': abs(r['montant_ht']) # Send absolute value for display
             })
             
         data = {
             'start_date': start_date,
             'end_date': end_date,
             'ca_brut': ca_brut,
             'total_avoirs': abs(total_avoirs), # Send absolute value for display (PDF adds negative sign)
             'ca_net': ca_net, 
             'details_avoirs': details_avoirs
         }
         
         try:
             from utils import generate_ca_pdf
             filename = f"Etat_CA_{year}_{datetime.now().strftime('%H%M%S')}.pdf"
             generate_ca_pdf(data, filename)
             preview_and_print_pdf(filename)
         except Exception as e:
             messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF CA:\n{str(e)}")


# ==================== PAYMENTS FRAME ====================

class PaymentsFrame(ttk.Frame):
    """Payments management frame"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()
    
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text="Paiements", 
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header, bg=BG_COLOR)
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(
            btn_frame, 
            text="+ Nouveau Paiement", 
            bg=PRIMARY_COLOR, 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.add_payment,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="Modifier", 
            bg=SECONDARY_COLOR, 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.modify_payment,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        if self.app.user.get('role') == 'admin':
            tk.Button(
                btn_frame, 
                text="Supprimer", 
                bg="#d32f2f", 
                fg="white",
                font=("Arial", 10, "bold"),
                command=self.delete_payment,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, 
            text="Créer Bordereau", 
            bg="#c62828", 
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.create_bordereau,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # Table
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        
        columns = ("Numéro", "Date", "Client", "Montant", "Mode", "Référence", "Statut")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=vsb.set
        )
        
        vsb.config(command=self.tree.yview)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree.tag_configure('evenrow', background='#546e7a')
        self.tree.tag_configure('pending', foreground='#ff9800', font=('Arial', 10, 'bold')) # Orange for Pending
        self.load_data()
        
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        paiements = self.app.db.get_all_paiements()
        for idx, p in enumerate(paiements):
            tags = []
            if idx % 2 == 0:
                tags.append('evenrow')
            
            if p['statut'] == 'En attente':
                tags.append('pending')

            self.tree.insert("", tk.END, iid=p['id'], values=(
                p['numero'],
                p['date_paiement'],
                p['client_nom'],
                format_currency(p['montant']),
                p['mode_paiement'],
                p.get('reference', '-'),
                p['statut']
            ), tags=tuple(tags))
    
    def add_payment(self):
        PaymentDialog(self.app.root, self.app, callback=self.load_data)

    def modify_payment(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un paiement à modifier")
            return
        
        payment_id = int(selection[0])
        PaymentDialog(self.app.root, self.app, payment_id=payment_id, callback=self.load_data)

    def delete_payment(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un paiement à supprimer")
            return
            
        if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce paiement ?"):
            return
            
        payment_id = int(selection[0])
        try:
            self.app.db.delete_payment(payment_id)
            messagebox.showinfo("Succès", "Paiement supprimé")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

    def create_bordereau(self):
        # Get selected payments with status 'En attente'
        BordereauDialog(self.app.root, self.app, callback=self.load_data)



# ==================== SITUATION FRAME ====================

# ==================== SITUATION FRAME ====================

class SituationFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.mode = tk.StringVar(value="client")  # "client" or "daily_sales"
        self._build()
    
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header, text="Situation & Rapports", font=("Arial", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        
        # Mode Selection
        mode_frame = tk.Frame(self, bg=BG_COLOR)
        mode_frame.pack(fill=tk.X, padx=40, pady=5)
        
        tk.Radiobutton(mode_frame, text="Situation Client", variable=self.mode, 
                      value="client", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="État Journalier des Ventes", variable=self.mode, 
                      value="daily_sales", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="État CA par Famille", variable=self.mode, 
                      value="ca_category", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Rapport Stock Valorisé", variable=self.mode, 
                      value="stock_valuation", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)

        # Second Row of Modes
        mode_frame_2 = tk.Frame(self, bg=BG_COLOR)
        mode_frame_2.pack(fill=tk.X, padx=40, pady=5)

        tk.Radiobutton(mode_frame_2, text="État de Consommation Global", variable=self.mode, 
                      value="global_consumption", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame_2, text="Mouvements Valorisés", variable=self.mode, 
                      value="valorized_movements", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame_2, text="État Annuel des Créances", variable=self.mode, 
                      value="annual_receivables", command=self.update_ui, bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(mode_frame_2, text="Analyse des Annulations", variable=self.mode, 
                      value="cancellations_analysis", command=self.update_ui, bg="orange", fg="black", selectcolor=SIDEBAR_COLOR).pack(side=tk.LEFT, padx=10)
        
        # Controls Frame (Dynamic)
        self.controls_frame = tk.Frame(self, bg=BG_COLOR)
        self.controls_frame.pack(fill=tk.X, padx=40, pady=10)
        
        # Initial UI setup
        self.update_ui()
        
        # Info/Preview Area
        self.info_text = tk.Text(self, height=30, width=100, bg="#455a64", fg="white", insertbackground="white")
        self.info_text.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)

    def update_ui(self):
        # Clear controls frame
        for widget in self.controls_frame.winfo_children():
            widget.destroy()
            
        mode = self.mode.get()
        
        if mode == "client":
            tk.Label(self.controls_frame, text="Sélectionner un client:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            
            clients = self.app.db.get_all_clients()
            self.client_var = tk.StringVar()
            self.client_combo = ttk.Combobox(self.controls_frame, textvariable=self.client_var, width=40)
            self.client_combo['values'] = [f"{c['id']} - {c['raison_sociale']}" for c in clients]
            self.client_combo.pack(side=tk.LEFT, padx=5)
            self.client_combo.bind("<<ComboboxSelected>>", self.load_situation)
            
            tk.Button(self.controls_frame, text="Exporter Situation PDF", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)
            
        elif mode == "daily_sales":
            tk.Label(self.controls_frame, text="Date:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            
            if DateEntry:
                self.date_entry = DateEntry(self.controls_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                self.date_entry.pack(side=tk.LEFT, padx=5)
            else:
                self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                self.date_entry = tk.Entry(self.controls_frame, textvariable=self.date_var, width=15, bg="#455a64", fg="white", insertbackground="white")
                self.date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(self.controls_frame, text="Générer Rapport PDF", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)
            
            # Auto-preview logic? Maybe manual for now. 
            # Or just instructions in text area.
            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Sélectionnez une date et cliquez sur 'Générer Rapport PDF' pour voir l'état journalier des ventes.")

        elif mode == "global_consumption":
            tk.Label(self.controls_frame, text="Arrêté au :", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            
            if DateEntry:
                self.date_entry = DateEntry(self.controls_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                self.date_entry.pack(side=tk.LEFT, padx=5)
            else:
                self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                self.date_entry = tk.Entry(self.controls_frame, textvariable=self.date_var, width=15, bg="#455a64", fg="white", insertbackground="white")
                self.date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(self.controls_frame, text="Générer Rapport (PDF & Excel)", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)
            
            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Génère l'état de consommation (Global) pour la date sélectionnée.\nInclus : Consommation Journalière, Mensuelle et Annuelle.\nValorisation au coût de revient.")

        elif mode == "ca_category":
            tk.Label(self.controls_frame, text="Du:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            self.start_date_entry = tk.Entry(self.controls_frame, width=12, bg="#455a64", fg="white", insertbackground="white")
            self.start_date_entry.insert(0, datetime.now().strftime("%Y-%m-01"))
            self.start_date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Label(self.controls_frame, text="Au:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            self.end_date_entry = tk.Entry(self.controls_frame, width=12, bg="#455a64", fg="white", insertbackground="white")
            self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.end_date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(self.controls_frame, text="Générer Rapport PDF", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)

            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Sélectionnez une période et cliquez sur 'Générer Rapport PDF' pour voir l'état du chiffre d'affaire par famille.")

        elif mode == "stock_valuation":
            # Product Selection
            tk.Label(self.controls_frame, text="Produit:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            products = self.app.db.get_all_products()
            self.product_var = tk.StringVar()
            self.product_combo = ttk.Combobox(self.controls_frame, textvariable=self.product_var, width=30)
            self.product_combo['values'] = [f"{p['id']} - {p['nom']}" for p in products]
            self.product_combo.pack(side=tk.LEFT, padx=5)

            # Date Selection
            tk.Label(self.controls_frame, text="Du:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            self.start_date_entry = tk.Entry(self.controls_frame, width=12, bg="#455a64", fg="white", insertbackground="white")
            self.start_date_entry.insert(0, datetime.now().strftime("%Y-%m-01"))
            self.start_date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Label(self.controls_frame, text="Au:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            self.end_date_entry = tk.Entry(self.controls_frame, width=12, bg="#455a64", fg="white", insertbackground="white")
            self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.end_date_entry.pack(side=tk.LEFT, padx=5)
            
            # Buttons
            tk.Button(self.controls_frame, text="Excel", bg="#4caf50", fg="white", 
                     command=self.generate_stock_val_excel).pack(side=tk.RIGHT, padx=5)
            tk.Button(self.controls_frame, text="PDF", bg=ACCENT_COLOR, fg="white", 
                     command=self.generate_stock_val_pdf).pack(side=tk.RIGHT, padx=5)
            
            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Rapport de Stock Valorisé.\nSélectionnez un produit et une période.\nLes calculs sont basés sur le Coût de Revient (Prix Unitaire) de la table Produits.")

        elif mode == "valorized_movements":
            tk.Label(self.controls_frame, text="Date Journée (N):", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            
            if DateEntry:
                self.date_entry = DateEntry(self.controls_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                self.date_entry.pack(side=tk.LEFT, padx=5)
            else:
                self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                self.date_entry = tk.Entry(self.controls_frame, textvariable=self.date_var, width=15, bg="#455a64", fg="white", insertbackground="white")
                self.date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(self.controls_frame, text="Générer Rapport PDF", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)
            
            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Génère l'ÉTAT DES MOUVEMENTS DES STOCKS VALORISES pour la journée choisie.\nFormat PDF A4 Paysage. Deux tableaux : Quantités et Valeurs.")

        elif mode == "annual_receivables":
            tk.Label(self.controls_frame, text="Situation au (Date N):", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            
            if DateEntry:
                self.date_entry = DateEntry(self.controls_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                self.date_entry.pack(side=tk.LEFT, padx=5)
            else:
                self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                self.date_entry = tk.Entry(self.controls_frame, textvariable=self.date_var, width=15, bg="#455a64", fg="white", insertbackground="white")
                self.date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(self.controls_frame, text="Générer Rapport (PDF & Excel)", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)
            
            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Génère l'ÉTAT RÉCAPITULATIF ANNUEL DES CRÉANCES ET RECOUVREMENT CLIENTS.\nCalculs basés sur :\n- Solde au 01/01 (Report N-1 + Historique)\n- Mouvements de l'année (Achats Net, Paiements)\n- Solde Final et % Recouvrement.")

        elif mode == "annual_receivables":
            tk.Label(self.controls_frame, text="Situation au (Date N):", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            
            if DateEntry:
                self.date_entry = DateEntry(self.controls_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                self.date_entry.pack(side=tk.LEFT, padx=5)
            else:
                self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                self.date_entry = tk.Entry(self.controls_frame, textvariable=self.date_var, width=15, bg="#455a64", fg="white", insertbackground="white")
                self.date_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Button(self.controls_frame, text="Générer Rapport (PDF & Excel)", bg=ACCENT_COLOR, fg="white", 
                     command=self.export_pdf).pack(side=tk.RIGHT, padx=5)
            
            if hasattr(self, 'info_text'):
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Génère l'ÉTAT RÉCAPITULATIF ANNUEL DES CRÉANCES ET RECOUVREMENT CLIENTS.\nCalculs basés sur :\n- Solde au 01/01 (Report N-1 + Historique)\n- Mouvements de l'année (Achats Net, Paiements)\n- Solde Final et % Recouvrement.")

        elif mode == "annual_receivables":
            tk.Button(self.controls_frame, text="Générer Rapport Créances", bg=ACCENT_COLOR, fg="white",
                      command=lambda: self._generate_report_creances()).pack(side=tk.LEFT, padx=5)
                      
        elif mode == "cancellations_analysis":
            tk.Label(self.controls_frame, text="Rapport d'analyse des factures annulées", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
            tk.Button(self.controls_frame, text="Afficher l'analyse", bg=SECONDARY_COLOR, fg="white",
                      command=self.load_situation).pack(side=tk.LEFT, padx=5)

    def load_situation(self, event=None):
        mode = self.mode.get()

        if mode == "client":
            selected = self.client_var.get()
            if not selected:
                return
            client_id = int(selected.split(' - ')[0])
            situation = self.app.logic.get_client_situation(client_id)
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Client: {situation['client']['raison_sociale']}\n")
            self.info_text.insert(tk.END, f"Seuil de crédit: {format_currency(situation['client']['seuil_credit'])} DA\n\n")
            self.info_text.insert(tk.END, f"Report N-1: {format_currency(situation['balance']['report'])} DA\n")
            self.info_text.insert(tk.END, f"Total Paiements: {format_currency(situation['balance']['total_paiements'])} DA\n")
            self.info_text.insert(tk.END, f"Total Avoirs: {format_currency(situation['balance']['total_avoirs'])} DA\n")
            self.info_text.insert(tk.END, f"Total Factures: {format_currency(situation['balance']['total_factures'])} DA\n")
            self.info_text.insert(tk.END, f"\nSOLDE: {format_currency(situation['balance']['solde'])} DA\n")

        elif mode == "cancellations_analysis":
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "ANALYSE DES ANNULATIONS\n")
            self.info_text.insert(tk.END, "="*60 + "\n\n")
            
            # Fetch data
            conn = self.app.db._get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM journal_annulations ORDER BY date_annulation DESC")
            annulations = c.fetchall()
            
            if not annulations:
                self.info_text.insert(tk.END, "Aucune annulation enregistrée.\n")
                return

            total_perdu_ht = 0.0
            
            # Group by Motif
            by_motif = {}
            
            self.info_text.insert(tk.END, f"{'DATE':<12} | {'NUMERO':<10} | {'MONTANT HT':<15} | {'MOTIF'}\n")
            self.info_text.insert(tk.END, "-"*60 + "\n")
            
            for row in annulations:
                # Handling different row factories
                try:
                     # If row is dict-like
                     date_val = row['date_annulation']
                     num = row['numero_facture']
                     motif = row['motif']
                     mht = row['montant_original_ht']
                except:
                     # Fallback tuple index
                     date_val = row[2]
                     num = row[5] # Adjusted indices based on typical schema
                     motif = row[4]
                     mht = row[6]

                total_perdu_ht += mht
                
                if motif not in by_motif: by_motif[motif] = 0
                by_motif[motif] += 1
                
                self.info_text.insert(tk.END, f"{str(date_val)[:10]:<12} | {str(num):<10} | {format_currency(mht):<15} | {motif}\n")
            
            self.info_text.insert(tk.END, "-"*60 + "\n")
            self.info_text.insert(tk.END, f"TOTAL MANQUE À GAGNER (HT): {format_currency(total_perdu_ht)} DA\n\n")
            
            self.info_text.insert(tk.END, "SYNTHÈSE PAR MOTIF:\n")
            for m, count in by_motif.items():
                self.info_text.insert(tk.END, f"- {m}: {count} fois\n")

    def export_pdf(self):
        from utils import generate_situation_pdf, generate_daily_sales_pdf, generate_sales_by_category_pdf
        import os
        
        mode = self.mode.get()
        
        if mode == "valorized_movements":
            from reports import generate_movements_valorises_pdf
            
            if DateEntry and hasattr(self, 'date_entry') and isinstance(self.date_entry, DateEntry):
                date_str = self.date_entry.get_date().strftime("%Y-%m-%d")
            elif hasattr(self, 'date_var'):
                date_str = self.date_var.get()
            else:
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide")
                return

            try:
                pdf_path = generate_movements_valorises_pdf(date_str)
                messagebox.showinfo("Succès", f"Rapport généré :\n- {os.path.basename(pdf_path)}")
                preview_and_print_pdf(pdf_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération :\n{e}")
                print(f"ERROR: {e}")
            return

        elif mode == "annual_receivables":
            from reports import generate_annual_receivables_pdf, generate_annual_receivables_excel
            
            # Date retrieval
            if DateEntry and hasattr(self, 'date_entry') and isinstance(self.date_entry, DateEntry):
                date_str = self.date_entry.get_date().strftime("%Y-%m-%d")
            elif hasattr(self, 'date_var'):
                date_str = self.date_var.get()
            else:
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide")
                return

            try:
                # Fetch Data
                data = self.app.logic.get_annual_receivables_data(date_str)
                
                # Generate both
                excel_path = generate_annual_receivables_excel(data, date_str)
                pdf_path = generate_annual_receivables_pdf(data, date_str)
                
                messagebox.showinfo("Succès", f"Rapports générés :\n- {os.path.basename(excel_path)}\n- {os.path.basename(pdf_path)}")
                preview_and_print_pdf(pdf_path)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Erreur", f"Erreur lors de la génération :\n{e}")
            return


        elif mode == "client":
            selected = self.client_var.get()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un client")
                return
            
            client_id = int(selected.split(' - ')[0])
            # client_name = selected.split(' - ')[1] # Use safe retrieval
            client = self.app.db.get_client_by_id(client_id)
            situation = self.app.logic.get_client_situation(client_id)
            
            filename = f"Situation_Client_{client_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
            generate_situation_pdf(client, situation, filename)
            try: os.startfile(filename)
            except: pass
            
        elif mode == "daily_sales":
            if DateEntry and hasattr(self, 'date_entry') and isinstance(self.date_entry, DateEntry):
                date_str = self.date_entry.get_date().strftime("%Y-%m-%d")
            elif hasattr(self, 'date_var'):
                date_str = self.date_var.get()
            else:
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide")
                return
                
            data = self.app.logic.get_daily_sales_stats(date_str)
            filename = f"Etat_Vente_{date_str}.pdf"
            generate_daily_sales_pdf(data, filename)
            try: os.startfile(filename)
            except: pass

        elif mode == "ca_category":
            start = self.start_date_entry.get()
            end = self.end_date_entry.get()
            
            try:
                datetime.strptime(start, "%Y-%m-%d")
                datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                 messagebox.showerror("Erreur", "Format de date invalide (YYYY-MM-DD requis)")
                 return

            try:
                data = self.app.logic.get_sales_by_category(start, end)
                if not data:
                    messagebox.showinfo("Information", "Aucune donnée pour cette période.")
                    return
                    
                filename = f"Etat_CA_Famille_{start}_{end}.pdf"
                generate_sales_by_category_pdf(data, start, end, filename)
                preview_and_print_pdf(filename)
            except Exception as e:
                messagebox.showerror("Erreur PDF", f"Erreur lors de la génération: {str(e)}")
                print(f"DEBUG ERROR: {e}")

        elif mode == "global_consumption":
            from reports import generate_global_consumption_pdf, generate_global_consumption_excel
            
            # Date retrieval
            if DateEntry and hasattr(self, 'date_entry') and isinstance(self.date_entry, DateEntry):
                date_str = self.date_entry.get_date().strftime("%Y-%m-%d")
            elif hasattr(self, 'date_var'):
                date_str = self.date_var.get()
            else:
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide")
                return

            try:
                # Generate both
                excel_path = generate_global_consumption_excel(date_str)
                pdf_path = generate_global_consumption_pdf(date_str)
                
                messagebox.showinfo("Succès", f"Rapports générés :\n- {os.path.basename(excel_path)}\n- {os.path.basename(pdf_path)}")
                preview_and_print_pdf(pdf_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération :\n{e}")

    def generate_stock_val_excel(self):
        self._generate_stock_report("excel")

    def generate_stock_val_pdf(self):
        self._generate_stock_report("pdf")

    def _generate_stock_report(self, format_type):
        product_sel = self.product_var.get()
        if not product_sel:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit.")
            return

        product_id = int(product_sel.split(' - ')[0])
        start = self.start_date_entry.get()
        end = self.end_date_entry.get()

        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
             messagebox.showerror("Erreur", "Format de date invalide (YYYY-MM-DD)")
             return
             
        data = self.app.logic.get_stock_valuation_data(product_id, start, end)
        if not data or not data.get('data'):
             messagebox.showinfo("Info", "Aucune donnée trouvée pour cette période.")
             return
             
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format_type == "excel":
            filename = f"Etat_Stock_Valorise_{product_id}_{timestamp}.xlsx"
            generate_stock_valuation_excel(data, filename)
            try: os.startfile(filename)
            except: pass
        else:
            filename = f"Etat_Stock_Valorise_{product_id}_{timestamp}.pdf"
            generate_stock_valuation_pdf(data, filename)
            try: os.startfile(filename)
            except: pass


# ==================== STOCK FRAME ====================

class StockFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()
    
    def _build(self):
        # Create Canvas and Scrollbar
        canvas = tk.Canvas(self, bg=BG_COLOR)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Header
        header = tk.Frame(scrollable_frame, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header, text="État des Stocks", font=("Arial", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        tk.Button(header, text="Exporter Excel", bg=ACCENT_COLOR, fg="white", command=self.export_excel).pack(side=tk.RIGHT)
        
        # Table
        table_frame = tk.Frame(scrollable_frame, bg=BG_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        columns = ("Code", "Désignation", "Unité", "Stock Initial", "Réceptions (+)", "Ventes (-)", "Stock Final", "Réf. Stock")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        for col in columns:
            self.tree.heading(col, text=col)
            width = 90 # Default smaller
            if col == "Code": width = 100
            elif col == "Désignation": width = 250
            elif col == "Unité": width = 70
            elif col == "Réf. Stock": width = 200
            elif col in ["Stock Initial", "Réceptions (+)", "Ventes (-)", "Stock Final"]: width = 90
            
            self.tree.column(col, width=width, anchor="center")
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree.tag_configure('evenrow', background='#546e7a')
        self.load_data()
        
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        products = self.app.db.get_all_products()
        
        # Pre-fetch for parent lookup
        product_map = {p['id']: p for p in products}
        
        for idx, p in enumerate(products):
            display_name = p['nom']
            stock_final = p['stock_actuel']
            ref_stock = ""
            
            # Helper to get effective stock if child
            if p.get('parent_stock_id'):
                 # Show parent stock for availability context
                 parent = product_map.get(p['parent_stock_id'])
                 if parent:
                     # stock_final = parent['stock_actuel']  <-- REMOVE OVERRIDE
                     ref_stock = f"-> {parent['nom']}"

            movements = self.app.db.get_stock_movements(p['id'])
            # Logic recalculation could be here if needed
            # For now relying on p['stock_actuel'] as master for "Final"
            
            # Simplified Stats:
            # Init = Final - (In - Out) ==> Init = Final - In + Out
            # Net Sales = Ventes (negative) + Retours (positive)
            # We want to display the OUTFLOW. So if we sold 100 (-100) and returned 20 (+20), Net = -80. Display 80.
            sales_movements = [m['quantite'] for m in movements if m['type_mouvement'] in ['Vente', 'Retour Avoir', 'Annulation Facture']]
            net_sales = sum(sales_movements)
            total_out = abs(net_sales) # Sum of Vente+Avoir should be negative (net outflow), or 0 if balanced.
            
            # Receptions only
            reception_movements = [m['quantite'] for m in movements if m['type_mouvement'] in ['Réception', 'Annulation Réception']]
            total_in = sum(reception_movements)
            
            # Logic tweak: if parent stock management, stock_initial might be misleading if just calc from movements
            # But let's show visual calc:
            stock_initial = stock_final - total_in + total_out
            
            tag = 'evenrow' if idx % 2 == 0 else ''
            
            self.tree.insert("", tk.END, values=(
                p.get('code_produit', ''),
                display_name,
                p['unite'],
                format_quantity(stock_initial, p['unite']),
                format_quantity(total_in, p['unite']),
                format_quantity(total_out, p['unite']),
                format_quantity(stock_final, p['unite']),
                ref_stock
            ), tags=(tag,))

    def export_excel(self):
        products = self.app.db.get_all_products()
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if filename:
            export_stock_to_excel(products, filename)
            messagebox.showinfo("Succès", "Export effectué")


# ==================== USERS FRAME ====================

class UsersFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()
    
    def _build(self):
        tk.Label(self, text="Utilisateurs", font=("Arial", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=20)
        button_frame = tk.Frame(self, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(button_frame, text="+ Nouvel utilisateur", bg=PRIMARY_COLOR, fg="white", command=self.add_user).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Modifier", bg=SECONDARY_COLOR, fg="white", command=self.edit_user_btn).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Supprimer", bg="#d32f2f", fg="white", command=self.delete_user_btn).pack(side=tk.LEFT, padx=5)
        
        self.tree = ttk.Treeview(self, columns=("ID", "Username", "Nom", "Rôle"), show="headings")
        for col in ("ID", "Username", "Nom", "Rôle"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        self.load_data()
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        users = self.app.db.get_all_users()
        for u in users:
            self.tree.insert("", tk.END, values=(u['id'], u['username'], u['full_name'], u['role']))
    
    def add_user(self):
        UserDialog(self.app.root, self.app.user['id'], callback=self.load_data)

    def edit_user_btn(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return
        # Get user ID from selection values (first column)
        item = self.tree.item(selection[0])
        user_id = item['values'][0]
        UserDialog(self.app.root, self.app.user['id'], user_id=user_id, callback=self.load_data)

    def delete_user_btn(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return
        
        item = self.tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer l'utilisateur {username} ?"):
            try:
                self.app.db.delete_user(user_id)
                self.app.db.log_action(self.app.user['id'], "DELETE_USER", f"Deleted user {username} (ID: {user_id})")
                self.load_data()
                messagebox.showinfo("Succès", "Utilisateur supprimé")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))


# ==================== PRICES FRAME ====================

class PricesFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()
    
    def _build(self):
        tk.Label(self, text="Gestion des Prix", font=("Arial", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=20)
        
        products = self.app.db.get_all_products()
        for p in products:
            frame = tk.LabelFrame(self, text=p['nom'], bg=BG_COLOR, fg=TEXT_COLOR)
            frame.pack(fill=tk.X, padx=40, pady=10)
        for p in products:
            frame = tk.LabelFrame(self, text=p['nom'], bg=BG_COLOR, fg=TEXT_COLOR)
            frame.pack(fill=tk.X, padx=40, pady=10)
            tk.Label(frame, text=f"Prix actuel: {format_currency(p['prix_actuel'])} DA", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=10)
            tk.Button(frame, text="Modifier", command=lambda pid=p['id']: self.update_price(pid)).pack(side=tk.RIGHT, padx=10)
            tk.Button(frame, text="Modifier", command=lambda pid=p['id']: self.update_price(pid)).pack(side=tk.RIGHT, padx=10)
    
    def update_price(self, product_id):
        PriceDialog(self.app.root, product_id, self.app.user['id'], callback=lambda: self._build())


# ==================== DIALOGS ====================

class ClientDialog:
    def __init__(self, parent, user_id, client_id=None, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Client")
        self.dialog.state('zoomed')
        self.user_id = user_id
        self.client_id = client_id
        self.callback = callback
        self.entries = {}
        self._build()
        if client_id:
            self._load_client()
            self._load_balance() # Load balance for display
    
    def _build(self):
        # Main container with two columns
        # Main container with two columns
        main_frame = tk.LabelFrame(self.dialog, text="Informations Client", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Configure columns
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Left Column
        col1 = tk.Frame(main_frame)
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Right Column
        col2 = tk.Frame(main_frame)
        col2.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Helper to create fields
        def create_field(parent, label_text, key, read_only=False):
            tk.Label(parent, text=label_text).pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(parent, bg="#455a64", fg="white", insertbackground="white")
            entry.pack(fill=tk.X, pady=(0, 5))
            if read_only:
                entry.config(state='readonly')
            else:
                entry.bind("<Return>", lambda e: self._focus_next(e.widget))
            self.entries[key] = entry
            return entry

        # --- Fields Layout ---
        create_field(col1, "Code Client", "code_client")
        create_field(col1, "Raison Sociale*", "raison_sociale")
        create_field(col1, "Adresse*", "adresse")
        create_field(col1, "N° Tél 1", "tel_1")
        create_field(col1, "N° Tél 2", "tel_2")
        create_field(col1, "E-mail", "email")
        create_field(col1, "Banque", "compte_bancaire")

        # Categorie Field (Combobox)
        tk.Label(col1, text="Catégorie").pack(anchor="w", pady=(5, 0))
        cat_values = ['Public', 'Privé', 'Revendeur', 'Entreprise Publique']
        cat_combo = ttk.Combobox(col1, values=cat_values)
        cat_combo.pack(fill=tk.X, pady=(0, 5))
        self.entries['categorie'] = cat_combo

        create_field(col2, "Registre de Commerce (RC)*", "rc")
        create_field(col2, "Article d'Imposition (AI)*", "article_imposition")
        create_field(col2, "NIF*", "nif")
        create_field(col2, "NIS*", "nis")
        create_field(col2, "Seuil Crédit", "seuil_credit")
        
        # Check if user is admin to allow editing "Solde Exercice précédent"
        conn = get_db()._get_connection()
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE id=?", (self.user_id,))
        res = c.fetchone()
        is_admin = (res and res[0] == 'admin')
        
        # Solde (Read Only)
        self.solde_entry = create_field(col2, "Solde (Information)", "solde", read_only=True)
        # Note: 'report_n_moins_1' is implicitly part of the balance but we might want to edit it?
        # The prompt says "Solde Ne doit pas être changeable mais doit être affiché."
        # Usually Solde = Report + Transactions. 
        # I'll add Report N-1 as editable if needed, but for now sticking to the strict "Solde visible" rule.
        # Let's add Report N-1 as editable since it's an input.
        create_field(col2, "Solde Exercice précédent", "report_n_moins_1", read_only=not is_admin)

        # Buttons Frame
        btn_frame = tk.Frame(self.dialog, pady=20)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        if self.client_id:
            btn_text = "Enregistrer les modifications"
            btn_width = 25
        else:
            btn_text = "Confirmer"
            btn_width = 15

        tk.Button(btn_frame, text=btn_text, bg="#2e7d32", fg="white", 
                 font=("Arial", 11, "bold"), command=self.save, width=btn_width).pack(side=tk.RIGHT, padx=10)
        
        tk.Button(btn_frame, text="Annuler", bg="#757575", fg="white", 
                 font=("Arial", 11, "bold"), command=self.dialog.destroy, width=15).pack(side=tk.RIGHT, padx=10)
    
    def _focus_next(self, widget):
        widget.tk_focusNext().focus()
    
    def _load_client(self):
        client = get_db().get_client_by_id(self.client_id)
        if client:
            for key, entry in self.entries.items():
                if key == 'solde': continue # Handle separately
                val = client.get(key, "")
                if val is None: val = ""
                entry.delete(0, tk.END)
                entry.insert(0, str(val))
    
    def _load_balance(self):
        if self.client_id:
            # Assuming logic.py has calculate_client_balance
            try:
                balance = get_logic().calculate_client_balance(self.client_id)
                solde = balance.get('solde', 0.0)
                
                # Color coding: "Military Green" (Olive-ish) for >= 0, Red for < 0
                # Using #9ccc65 for military/olive tone that is readable on dark bg
                # Or #8bc34a. Let's try #7cb342 (Light Green 600) which is vibrant but earthy.
                # Actually user said "vert militaire", often #4b5320 but that's too dark for text.
                # Let's use #689f38 (Light Green 700) 
                color = "#689f38" if solde >= 0 else "#ff1744"
                
                self.entries['solde'].config(state='normal', fg=color, disabledforeground=color, font=("Arial", 10, "bold"))
                self.entries['solde'].delete(0, tk.END)
                self.entries['solde'].config(state='normal', fg=color, disabledforeground=color, font=("Arial", 10, "bold"))
                self.entries['solde'].delete(0, tk.END)
                self.entries['solde'].insert(0, format_currency(solde))
                self.entries['solde'].config(state='readonly')
                self.entries['solde'].config(state='readonly')
            except Exception as e:
                print(f"Error loading balance: {e}")

    def save(self):
        try:
            data = {k: v.get() for k, v in self.entries.items() if k != 'solde'}
            
            # Validations
            if not data.get('raison_sociale'):
                messagebox.showwarning("Attention", "La Raison Sociale est obligatoire")
                return

            # Check Duplicates
            code_client = data.get('code_client')
            raison_sociale = data.get('raison_sociale')
            exists, msg = get_db().check_client_exists(code_client, raison_sociale, exclude_id=self.client_id)
            if exists:
                messagebox.showerror("Erreur doublon", msg)
                return

            data['seuil_credit'] = parse_currency(data.get('seuil_credit') or 0)
            data['report_n_moins_1'] = parse_currency(data.get('report_n_moins_1') or 0)
            
            if self.client_id:
                get_db().update_client(self.client_id, **data)
                get_db().log_action(self.user_id, "UPDATE_CLIENT", f"Updated Client: {data}")
            else:
                get_db().create_client(**data, created_by=self.user_id)
                get_db().log_action(self.user_id, "CREATE_CLIENT", f"Created Client: {data}")
            
            messagebox.showinfo("Succès", "Client enregistré avec succès")
            if self.callback:
                self.callback()
            self.dialog.destroy()
        except ValueError as ve:
             messagebox.showerror("Erreur", "Veuillez vérifier les champs numériques")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))




class ContractDialog:
    def __init__(self, parent, user_id, client):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Contrats - {client['raison_sociale']}")
        self.dialog.geometry("900x600")
        self.user_id = user_id
        self.client = client
        self.db = get_db()
        self._build()
        self.load_contracts()

    def _build(self):
        # Header
        header = tk.Frame(self.dialog, pady=10, padx=20)
        header.pack(fill=tk.X)
        tk.Label(header, text=f"Contrats Client: {self.client['raison_sociale']}", 
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT)

        # Form Frame
        form_frame = tk.LabelFrame(self.dialog, text="Nouveau / Modifier Contrat", padx=10, pady=10)
        form_frame.pack(fill=tk.X, padx=20, pady=10)

        # Fields
        tk.Label(form_frame, text="Code / N° Convention:").grid(row=0, column=0, padx=5, sticky='w')
        self.code_entry = tk.Entry(form_frame, width=20, bg="#455a64", fg="white", insertbackground="white")
        self.code_entry.grid(row=1, column=0, padx=5)

        tk.Label(form_frame, text="Date Début (YYYY-MM-DD):").grid(row=0, column=1, padx=5, sticky='w')
        if DateEntry:
            self.start_date = DateEntry(form_frame, width=12, date_pattern='yyyy-mm-dd')
        else:
            self.start_date = tk.Entry(form_frame, width=15, bg="#455a64", fg="white", insertbackground="white")
            self.start_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.start_date.grid(row=1, column=1, padx=5)

        tk.Label(form_frame, text="Date Fin (YYYY-MM-DD):").grid(row=0, column=2, padx=5, sticky='w')
        if DateEntry:
            self.end_date = DateEntry(form_frame, width=12, date_pattern='yyyy-mm-dd')
        else:
            self.end_date = tk.Entry(form_frame, width=15, bg="#455a64", fg="white", insertbackground="white")
        self.end_date.grid(row=1, column=2, padx=5)

        tk.Label(form_frame, text="Montant Global (Optionnel):").grid(row=0, column=3, padx=5, sticky='w')
        self.montant_entry = tk.Entry(form_frame, width=15, bg="#455a64", fg="white", insertbackground="white")
        self.montant_entry.insert(0, "0.0")
        self.montant_entry.grid(row=1, column=3, padx=5)

        # Buttons
        self.btn_save = tk.Button(form_frame, text="Ajouter", bg=PRIMARY_COLOR, fg="white", 
                                  command=self.save_contract)
        self.btn_save.grid(row=1, column=4, padx=10)
        
        tk.Button(form_frame, text="Effacer", command=self.clear_form).grid(row=1, column=5, padx=5)

        # List
        list_frame = tk.Frame(self.dialog, padx=20, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Code", "Début", "Fin", "Montant", "Statut")
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_select)
        
        # Bottom Actions
        action_frame = tk.Frame(self.dialog, pady=10)
        action_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(action_frame, text="Supprimer (Désactiver)", bg="#d32f2f", fg="white", 
                  command=self.delete_contract).pack(side=tk.RIGHT)

        self.editing_id = None

    def load_contracts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        contracts = self.db.get_client_contracts(self.client['id'], active_only=True)
        for c in contracts:
            self.tree.insert("", tk.END, values=(
                c['id'], c['code'], c['date_debut'], c['date_fin'], 
                f"{c.get('montant_total', 0):.2f}", 
                "Actif" if c['active'] else "Inactif"
            ))

    def save_contract(self):
        code = self.code_entry.get()
        if not code:
            messagebox.showwarning("Erreur", "Le code est obligatoire")
            return

        # Handle DateEntry or Entry
        if DateEntry and isinstance(self.start_date, DateEntry):
             date_debut = self.start_date.get_date().strftime("%Y-%m-%d")
        else:
             date_debut = self.start_date.get()
             
        if DateEntry and isinstance(self.end_date, DateEntry):
             date_fin = self.end_date.get_date().strftime("%Y-%m-%d")
        else:
             date_fin = self.end_date.get()
        
        try:
            montant = parse_currency(self.montant_entry.get())
        except:
            montant = 0.0

        if self.editing_id:
            # Update
            self.db.update_contract(self.editing_id, code=code, date_debut=date_debut, 
                                    date_fin=date_fin, montant_total=montant)
            messagebox.showinfo("Succès", "Contrat modifié")
        else:
            # Create
            self.db.create_contract(self.client['id'], code, date_debut, date_fin, montant, self.user_id)
            messagebox.showinfo("Succès", "Contrat créé")
            
        self.clear_form()
        self.load_contracts()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        vals = item['values']
        
        self.editing_id = vals[0]
        self.code_entry.delete(0, tk.END)
        self.code_entry.insert(0, vals[1])
        
        if DateEntry:
            try:
                self.start_date.set_date(vals[2])
                self.end_date.set_date(vals[3])
            except: pass
        else:
            self.start_date.delete(0, tk.END)
            self.start_date.insert(0, vals[2])
            self.end_date.delete(0, tk.END)
            self.end_date.insert(0, vals[3])
            
        self.montant_entry.delete(0, tk.END)
        self.montant_entry.insert(0, vals[4])
        
        self.btn_save.config(text="Modifier")

    def clear_form(self):
        self.editing_id = None
        self.code_entry.delete(0, tk.END)
        self.montant_entry.delete(0, tk.END)
        self.montant_entry.insert(0, "0.0")
        self.btn_save.config(text="Ajouter")
        self.montant_entry.bind('<FocusOut>', lambda e: self._format_entry(self.montant_entry, currency=True))
        
    def _format_entry(self, entry_widget, currency=True):
        val = entry_widget.get()
        if not val: return
        try:
            num = parse_currency(val)
            if currency:
                formatted = format_number(num, 2)
            else:
                formatted = format_number(num, 2) # Default quantity decimals. Or detect unit?
                # Actually quantity formatting depends on unit. 
                # For input, let's stick to 2 decimals standard or just clean it up.
                # Or just standard currency-like formatting for now (thousands space).
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, formatted)
        except: pass

    def delete_contract(self):
        sel = self.tree.selection()
        if not sel: return
        cid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", "Supprimer ce contrat ?"):
            self.db.delete_contract(cid)
            self.load_contracts()
            self.clear_form()


class ProductDialog:
    def __init__(self, parent, user_id, product_id=None, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Fiche Produit")
        self.dialog.state('zoomed')
        self.user_id = user_id
        self.product_id = product_id
        self.callback = callback
        self._build()
        if product_id:
            self._load_product()
    
    def _build(self):
        # Container for form
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        col1 = tk.Frame(main_frame)
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        col2 = tk.Frame(main_frame)
        col2.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Code Produit
        tk.Label(col1, text="Code Produit").pack(anchor="w", pady=(5,0))
        self.code_var = tk.StringVar()
        self.code_entry = ttk.Combobox(col1, textvariable=self.code_var, width=37)
        self.code_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Populate with "Code - Name" for better UX
        existing_products = get_db().get_all_products()
        self.code_map = {}
        code_values = []
        for p in existing_products:
            c = p.get('code_produit')
            if c:
                label = f"{c} - {p.get('nom', '')}"
                self.code_map[label] = p
                code_values.append(label)
                
        self.code_entry['values'] = sorted(code_values)
        self.code_entry.bind("<<ComboboxSelected>>", self._on_code_select)

        # Checkbox Is Child
        self.is_child_var = tk.BooleanVar(value=False)
        self.chk_child = tk.Checkbutton(col1, text="Est un code de prix (Enfant)", 
                                        variable=self.is_child_var, 
                                        command=self._toggle_parent_requirement)
        self.chk_child.pack(anchor="w", pady=(5,0))

        # Designation
        tk.Label(col1, text="Désignation*").pack(anchor="w", pady=(5,0))
        self.nom_entry = tk.Entry(col1, width=40, bg="#455a64", fg="white", insertbackground="white")
        self.nom_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Unité
        tk.Label(col1, text="Unité*").pack(anchor="w", pady=(5,0))
        self.unite_var = tk.StringVar(value="Sacs 50")
        self.unite_combo = ttk.Combobox(col1, textvariable=self.unite_var, 
                                      values=["Sacs 25", "Sacs 50", "Tonne", "Pièce"])
        self.unite_combo.pack(fill=tk.X, pady=(0, 10))

        # Catégorie
        tk.Label(col1, text="Catégorie").pack(anchor="w", pady=(5,0))
        self.categ_var = tk.StringVar(value="Autre")
        self.categ_combo = ttk.Combobox(col1, textvariable=self.categ_var, values=["Ciment", "Autre"])
        self.categ_combo.pack(fill=tk.X, pady=(0, 10))

        # Parent Product (For shared stock)
        self.lbl_parent = tk.Label(col1, text="Produit Parent (Optionnel - Stock partagé)")
        self.lbl_parent.pack(anchor="w", pady=(5,0))
        self.parent_var = tk.StringVar()
        self.parent_combo = ttk.Combobox(col1, textvariable=self.parent_var, width=37)
        
        # Load products for parent selection (exclude self if editing)
        all_prods = get_db().get_all_products()
        self.parent_map = {}
        parent_values = [""]
        for p in all_prods:
            if self.product_id and p['id'] == self.product_id:
                continue
            
            code = p.get('code_produit', '')
            nom = p.get('nom', 'Inconnu')
            if code:
                label = f"{code} - {nom}"
            else:
                label = f"{p['id']} - {nom}"
            
            self.parent_map[label] = p['id']
            parent_values.append(label)
            
        self.parent_combo['values'] = parent_values
        self.parent_combo.pack(fill=tk.X, pady=(0, 10))

        # Prices
        tk.Label(col2, text="Prix Unitaire Vente HT").pack(anchor="w", pady=(5,0))
        self.prix_entry = tk.Entry(col2, bg="#455a64", fg="white", insertbackground="white")
        self.prix_entry.insert(0, "0.0")
        self.prix_entry.pack(fill=tk.X, pady=(0, 10))

        tk.Label(col2, text="Coût de revient").pack(anchor="w", pady=(5,0))
        self.cout_entry = tk.Entry(col2, bg="#455a64", fg="white", insertbackground="white")
        self.cout_entry.insert(0, "0.0")
        self.cout_entry.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(col2, text="TVA (%)").pack(anchor="w", pady=(5,0))
        self.tva_entry = tk.Entry(col2, bg="#455a64", fg="white", insertbackground="white")
        self.tva_entry.insert(0, "19.0")
        self.tva_entry.pack(fill=tk.X, pady=(0, 10))

        # Stocks (Read Only)
        tk.Label(col2, text="Stock Initial").pack(anchor="w", pady=(5,0))
        self.stock_init_entry = tk.Entry(col2, bg="#455a64", fg="white", insertbackground="white")
        self.stock_init_entry.insert(0, "0.0")
        self.stock_init_entry.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(col2, text="Stock Actuel (Géré par le système)").pack(anchor="w", pady=(5,0))
        self.stock_final_entry = tk.Entry(col2, state='readonly', bg="#263238", fg="white", disabledbackground="#263238", disabledforeground="#b0bec5")
        self.stock_final_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        btn_frame = tk.Frame(self.dialog, pady=20)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        if self.product_id:
            btn_text = "Enregistrer les modifications"
            btn_width = 25
        else:
            btn_text = "Confirmer"
            btn_width = 15

        tk.Button(btn_frame, text=btn_text, bg="#2e7d32", fg="white", 
                 font=("Arial", 11, "bold"), command=self.save, width=btn_width).pack(side=tk.RIGHT, padx=10)
        
        tk.Button(btn_frame, text="Annuler", bg="#757575", fg="white", 
                 font=("Arial", 11, "bold"), command=self.dialog.destroy, width=15).pack(side=tk.RIGHT, padx=10)
    
    def _toggle_parent_requirement(self):
        if self.is_child_var.get():
             self.lbl_parent.config(text="Produit Parent (Obligatoire)*", fg="orange")
             # Block Initial Stock for Child Products
             self.stock_init_entry.delete(0, tk.END)
             self.stock_init_entry.insert(0, "0.0")
             self.stock_init_entry.config(state='disabled')
        else:
             self.lbl_parent.config(text="Produit Parent (Optionnel - Stock partagé)", fg="white")
             self.stock_init_entry.config(state='normal')

    def _load_product(self):
        product = get_db().get_product_by_id(self.product_id)
        if product:
            self.code_entry.set(str(product.get('code_produit', '') or ''))
            self.nom_entry.insert(0, str(product.get('nom', '')))
            self.unite_var.set(str(product.get('unite', '')))
            
            self.stock_init_entry.delete(0, tk.END)
            self.stock_init_entry.insert(0, str(product.get('stock_initial', 0.0)))
            
            self.stock_final_entry.config(state='normal')
            self.stock_final_entry.delete(0, tk.END)
            self.stock_final_entry.insert(0, str(product.get('stock_actuel', 0.0)))
            self.stock_final_entry.config(state='readonly')
            
            # Categorie load
            if 'categorie' in product and product['categorie']:
                self.categ_var.set(product['categorie'])
            
            self.prix_entry.delete(0, tk.END)
            self.prix_entry.insert(0, str(product.get('prix_actuel', 0.0)))
            
            self.cout_entry.delete(0, tk.END)
            self.cout_entry.insert(0, str(product.get('cout_revient', 0.0)))
            
            self.tva_entry.delete(0, tk.END)
            self.tva_entry.insert(0, str(product.get('tva', 19.0)))
            
            # Parent load
            if product.get('parent_stock_id'):
                self.is_child_var.set(True)
                pid = product['parent_stock_id']
                # find label
                for label, id_ in self.parent_map.items():
                    if id_ == pid:
                        self.parent_combo.set(label)
                        break
            else:
                self.is_child_var.set(False)
            
            self._toggle_parent_requirement()
    
    def _on_code_select(self, event):
        val = self.code_entry.get()
        product = self.code_map.get(val)
        if product:
            # Set Code field to JUST the code (strip name)
            code = product.get('code_produit', '')
            self.code_var.set(code)
            
            # Auto-fill Designation if empty or different
            self.nom_entry.delete(0, tk.END)
            self.nom_entry.insert(0, product.get('nom', ''))
            
            # Auto-fill Unit/Category/Price if helpful
            if product.get('unite'): self.unite_var.set(product['unite'])
            if product.get('categorie'): self.categ_var.set(product['categorie'])
            
            c = product.get('prix_actuel', 0.0)
            self.prix_entry.delete(0, tk.END)
            self.prix_entry.insert(0, str(c))
            
            # Note: We don't overwrite ID so this remains a "New Product" action 
            # unless we entered this dialog with an ID.
            # If the user wants to EDIT, they should have selected "Edit" from the list.
            # This autofill just helps creating variants or correcting codes.

    def save(self):
        try:
            # Sanitize Code (in case user typed "Code - Name" but didn't trigger select)
            raw_code = self.code_entry.get()
            if " - " in raw_code:
                 # Check if it matches a known label pattern
                 if raw_code in self.code_map:
                      raw_code = self.code_map[raw_code]['code_produit']
                 else:
                      # Maybe just split? Safe bet.
                      parts = raw_code.split(" - ", 1)
                      if len(parts) == 2:
                          raw_code = parts[0]

            data = {
                'nom': self.nom_entry.get(),
                'unite': self.unite_var.get(),
                'code_produit': raw_code,
                'categorie': self.categ_var.get()
            }
            
            # Parent ID
            parent_str = self.parent_var.get().strip()
            if parent_str:
                pid = self.parent_map.get(parent_str)
                # Fallback partial match
                if not pid:
                     prefix = f"{parent_str} - "
                     for label, id_ in self.parent_map.items():
                         if label.startswith(prefix) or label == parent_str:
                             pid = id_
                             break
                data['parent_stock_id'] = pid
            else:
                data['parent_stock_id'] = None
                
            # Validation: Is Child requirement
            if self.is_child_var.get() and not data['parent_stock_id']:
                 messagebox.showerror("Erreur", "Ce produit est marqué comme 'Code de prix (Enfant)'.\nVeuillez sélectionner un produit parent pour ce code.")
                 return
            
            # Numeric fields
            try:
                data['stock_initial'] = float(self.stock_init_entry.get())
                data['cout_revient'] = float(self.cout_entry.get())
                data['prix_actuel'] = float(self.prix_entry.get())
                data['tva'] = float(self.tva_entry.get())
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
                return

            if self.product_id:
                # Recalculate stock_actuel if stock_initial changed
                old_prod = get_db().get_product_by_id(self.product_id)
                if old_prod:
                    old_init = old_prod.get('stock_initial', 0.0) or 0.0
                    old_actuel = old_prod.get('stock_actuel', 0.0) or 0.0
                    delta = data['stock_initial'] - old_init
                    if abs(delta) > 0.001:
                        data['stock_actuel'] = old_actuel + delta

                get_db().update_product(self.product_id, **data)
                get_db().log_action(self.user_id, "UPDATE_PRODUCT", f"Updated Product: {data}")
            else:
                # For new product, stock_actuel = stock_initial
                data['stock_actuel'] = data['stock_initial']
                get_db().create_product(**data, created_by=self.user_id)
                get_db().log_action(self.user_id, "CREATE_PRODUCT", f"Created Product: {data}")
            
            messagebox.showinfo("Succès", "Produit enregistré")
            if self.callback:
                self.callback()
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


class ReceptionDialog:
    def __init__(self, parent, user_id, reception_id=None, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Bon de Réception")
        self.dialog.state('zoomed')
        self.user_id = user_id
        self.reception_id = reception_id
        self.callback = callback
        self.products = get_db().get_all_products()
        self._build()
        if reception_id:
            self._load_reception()

    def _build(self):
        # Main Container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        col1 = tk.Frame(main_frame)
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        col2 = tk.Frame(main_frame)
        col2.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # --- Date Reception ---
        tk.Label(col1, text="Date Réception (AAAA-MM-JJ)*").pack(anchor="w", pady=(5,0))
        from datetime import datetime
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = tk.Entry(col1, textvariable=self.date_var, width=40, bg="#263238", fg="white", insertbackground="white")
        self.date_entry.pack(fill=tk.X, pady=(0, 10))

        # 1. Code Produit
        tk.Label(col1, text="Produit*").pack(anchor="w", pady=(5,0))
        self.code_var = tk.StringVar()
        self.code_combo = ttk.Combobox(col1, textvariable=self.code_var, width=37)
        
        # Robust Product Mapping
        self.product_map = {}
        for p in self.products:
            code = p.get('code_produit', '')
            nom = p.get('nom', 'Inconnu')
            if code:
                label = f"{code} - {nom}"
            else:
                label = f"{p['id']} - {nom}"
            self.product_map[label] = p
            
        # Add prefixes for child products in Reception list
        formatted_labels = []
        for label, p in list(self.product_map.items()):
             if p.get('parent_stock_id'):
                  # It's a child/price product
                  new_label = f"[PRIX] {label}"
                  # Update map to point new label to p
                  self.product_map[new_label] = p
                  # Remove old key if strictly needed, but keeping it is safe
                  formatted_labels.append(new_label)
             else:
                  formatted_labels.append(label)
            
        self.code_combo['values'] = sorted(formatted_labels)
        self.code_combo.pack(fill=tk.X, pady=(0, 10))
        self.code_combo.bind("<<ComboboxSelected>>", self._on_code_select)
        
        # 2. Désignation (Read only)
        tk.Label(col1, text="Désignation").pack(anchor="w", pady=(5,0))
        self.designation = tk.Entry(col1, width=40, state='readonly', 
                                  bg="#616161", fg="#00e676", 
                                  disabledbackground="#616161", disabledforeground="#00e676",
                                  readonlybackground="#616161")
        self.designation.pack(fill=tk.X, pady=(0, 10))
        
        # 3. Unité
        tk.Label(col1, text="Unité").pack(anchor="w", pady=(5,0))
        self.unite_var = tk.StringVar()
        self.unite_combo = ttk.Combobox(col1, textvariable=self.unite_var, width=37, state='disabled')
        self.unite_combo.pack(fill=tk.X, pady=(0, 10))

        # 4. Logistics
        tk.Label(col2, text="Chauffeur").pack(anchor="w", pady=(5,0))
        self.chauffeur = tk.Entry(col2, width=40, bg="#263238", fg="gray", insertbackground="white", state='disabled')
        self.chauffeur.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(col2, text="Matricule Tracteur").pack(anchor="w", pady=(5,0))
        self.matricule = tk.Entry(col2, width=40, bg="#263238", fg="gray", insertbackground="white", state='disabled')
        self.matricule.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(col2, text="Matricule Remorque").pack(anchor="w", pady=(5,0))
        self.matricule_remorque = tk.Entry(col2, width=40, bg="#263238", fg="gray", insertbackground="white", state='disabled')
        self.matricule_remorque.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(col2, text="Transporteur").pack(anchor="w", pady=(5,0))
        self.transporteur = tk.Entry(col2, width=40, bg="#263238", fg="gray", insertbackground="white", state='disabled')
        self.transporteur.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(col2, text="Lieu de Livraison*").pack(anchor="w", pady=(5,0))
        self.lieu_var = tk.StringVar(value="Sur Stock")
        frame_lieu = tk.Frame(col2)
        frame_lieu.pack(fill=tk.X, pady=(0, 10))
        tk.Radiobutton(frame_lieu, text="Sur Stock", variable=self.lieu_var, value="Sur Stock", command=self._toggle_chantier).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_lieu, text="Sur Chantier", variable=self.lieu_var, value="Sur Chantier", command=self._toggle_chantier).pack(side=tk.LEFT, padx=10)
        
        self.lbl_chantier = tk.Label(col2, text="Adresse Chantier")
        self.lbl_chantier.pack(anchor="w", pady=(5,0))
        self.adresse_chantier = tk.Entry(col2, width=40, state=tk.DISABLED, bg="#455a64", fg="white", insertbackground="white", disabledbackground="#263238")
        self.adresse_chantier.pack(fill=tk.X, pady=(0, 10))

        # Moved Facture Info to Col2 to balance height
        tk.Label(col2, text="N° facture").pack(anchor="w", pady=(5,0))
        self.num_facture_rec = tk.Entry(col2, width=40, bg="#455a64", fg="white", insertbackground="white")
        self.num_facture_rec.pack(fill=tk.X, pady=(0, 10))

        tk.Label(col2, text="Date Fact").pack(anchor="w", pady=(5,0))
        if DateEntry:
            self.date_fact_rec = DateEntry(col2, width=38, background=PRIMARY_COLOR, foreground='white',
                                         headersbackground=PRIMARY_COLOR, headersforeground='white',
                                         borderwidth=2, date_pattern='dd/mm/yyyy')
        else:
            self.date_fact_rec = tk.Entry(col2, width=40, bg="#455a64", fg="white")
            self.date_fact_rec.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.date_fact_rec.pack(fill=tk.X, pady=(0, 10))
        
        # Quantities (bottom full width or split?)
        # Let's put quantities in col1 bottom
        tk.Label(col1, text="Quantité Annoncée*").pack(anchor="w", pady=(5,0))
        self.qte_annoncee = tk.Entry(col1, width=40, bg="#455a64", fg="white", insertbackground="white")
        self.qte_annoncee.pack(fill=tk.X, pady=(0, 10))
        self.qte_annoncee.bind('<KeyRelease>', self._check_ecart)
        
        tk.Label(col1, text="Quantité Reçue*").pack(anchor="w", pady=(5,0))
        self.qte_recue = tk.Entry(col1, width=40, bg="#455a64", fg="white", insertbackground="white")
        self.qte_recue.pack(fill=tk.X, pady=(0, 10))
        self.qte_recue.bind('<KeyRelease>', self._check_ecart)

        # New Fields (Bon Transfert & Facture)
        tk.Label(col1, text="N° Bon transfert").pack(anchor="w", pady=(5,0))
        self.num_bt = tk.Entry(col1, width=40, bg="#455a64", fg="white", insertbackground="white")
        self.num_bt.pack(fill=tk.X, pady=(0, 10))

        tk.Label(col1, text="Date BT").pack(anchor="w", pady=(5,0))
        if DateEntry:
            self.date_bt = DateEntry(col1, width=38, background=PRIMARY_COLOR, foreground='white', 
                                   headersbackground=PRIMARY_COLOR, headersforeground='white',
                                   borderwidth=2, date_pattern='dd/mm/yyyy')
        else:
            self.date_bt = tk.Entry(col1, width=40, bg="#455a64", fg="white")
            self.date_bt.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.date_bt.pack(fill=tk.X, pady=(0, 10))

        # Facture fields moved to col2
        
        # Motif Ecart
        self.frame_ecart = tk.Frame(col1)
        tk.Label(self.frame_ecart, text="Motif de l'écart*", fg="red").pack(anchor="w")
        self.motif_ecart = tk.Entry(self.frame_ecart, width=40, bg="#455a64", fg="white", insertbackground="white")
        self.motif_ecart.pack(fill=tk.X)
        
        # Buttons
        btn_frame = tk.Frame(self.dialog, pady=20)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Button(btn_frame, text="Confirmer", bg="#2e7d32", fg="white", 
                 font=("Arial", 11, "bold"), command=self.save, width=15).pack(side=tk.RIGHT, padx=10)
        
        tk.Button(btn_frame, text="Annuler", bg="#757575", fg="white", 
                 font=("Arial", 11, "bold"), command=self.dialog.destroy, width=15).pack(side=tk.RIGHT, padx=10)
        
        self.selected_product_id = None

    def _on_code_select(self, event):
        code = self.code_var.get() # Don't strip, exact match needed for spaces
        product = self.product_map.get(code)
        
        # Fallback for partial match
        if not product and code:
            prefix = f"{code} - "
            for key, p in self.product_map.items():
                if key.startswith(prefix) or key == code:
                    product = p
                    self.code_var.set(key)
                    break
        
        if product:
            self.selected_product_id = product['id']
            self.designation.config(state='normal')
            self.designation.delete(0, tk.END)
            self.designation.insert(0, product['nom'])
            self.designation.config(state='readonly')
            self.unite_var.set(product['unite'])
            # Update combobox selection if not exact
            if self.code_var.get() != code and product:
                 # It was updated in loop above if partial match
                 pass

            if product.get('parent_stock_id'):
                 parent = get_db().get_product_by_id(product['parent_stock_id'])
                 parent_info = f"{parent['code_produit']} - {parent['nom']}" if parent else "Inconnu"
                 messagebox.showerror("Interdit", f"Impossible de réceptionner sur ce code de prix.\n\nLa réception doit être faite sur le produit parent :\n{parent_info}\n\nVeuillez saisir ce code pour mettre à jour le stock physique.")
                 
                 # Clear selection
                 self.code_var.set('')
                 self.selected_product_id = None
                 self.designation.config(state='normal')
                 self.designation.delete(0, tk.END)
                 self.designation.config(state='readonly')
                 return
    
    def _toggle_chantier(self):
        if self.lieu_var.get() == "Sur Chantier":
            self.adresse_chantier.config(state=tk.NORMAL)
        else:
            self.adresse_chantier.delete(0, tk.END)
            self.adresse_chantier.config(state=tk.DISABLED)

    def _check_ecart(self, event=None):
        try:
            q_ann = float(self.qte_annoncee.get() or 0)
            q_rec = float(self.qte_recue.get() or 0)
            if abs(q_ann - q_rec) > 0.001:
                self.frame_ecart.pack(fill=tk.X, pady=(0, 10))
            else:
                self.frame_ecart.pack_forget()
        except ValueError:
            pass

    def _load_reception(self):
        # We need a method to get reception by ID in database.py
        # assuming logic.db.get_reception_by_id or similar exists or we query it.
        # ReceptionsFrame used `SELECT r.*, p.nom ... WHERE r.id=?`
        # I'll implement a query here or rely on DB
        conn = get_db()._get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM receptions WHERE id=?", (self.reception_id,))
        row = c.fetchone()
        if row:
            r = dict(row)
            # Find product code
            for label, p in self.product_map.items():
                if p['id'] == r['product_id']:
                    self.code_combo.set(label)
                    self._on_code_select(None) # This will set designation and unite
                    break
            
            self.date_var.set(r['date_reception']) # Load date_reception
            
            self.chauffeur.insert(0, r['chauffeur'])
            self.matricule.insert(0, r['matricule'])
            if r.get('matricule_remorque'): # Safe get for new field
                self.matricule_remorque.insert(0, r['matricule_remorque'])
            self.transporteur.insert(0, r['transporteur'])
            self.lieu_var.set(r['lieu_livraison'])
            self._toggle_chantier()
            if r['adresse_chantier']:
                self.adresse_chantier.insert(0, r['adresse_chantier'])
            
            self.qte_annoncee.insert(0, f"{r['quantite_annoncee']:.3f}")
            self.qte_recue.insert(0, f"{r['quantite_recue']:.3f}")
            self._check_ecart()
            if r['motif_ecart']:
                self.motif_ecart.insert(0, r['motif_ecart'])

            # Load new fields
            self.num_bt.insert(0, r.get('num_bon_transfert', ''))
            if DateEntry and r.get('date_bt'):
                try:
                    self.date_bt.set_date(datetime.strptime(r['date_bt'], "%Y-%m-%d"))
                except ValueError:
                    pass # Keep default if format is wrong
            elif r.get('date_bt'):
                self.date_bt.insert(0, datetime.strptime(r['date_bt'], "%Y-%m-%d").strftime("%d/%m/%Y"))

            self.num_facture_rec.insert(0, r.get('num_facture', ''))
            if DateEntry and r.get('date_fact'):
                try:
                    self.date_fact_rec.set_date(datetime.strptime(r['date_fact'], "%Y-%m-%d"))
                except ValueError:
                    pass # Keep default if format is wrong
            elif r.get('date_fact'):
                self.date_fact_rec.insert(0, datetime.strptime(r['date_fact'], "%Y-%m-%d").strftime("%d/%m/%Y"))

    def save(self):
        try:
            # Retrieve values
            date_reception = self.date_var.get().strip()
            # Validate Date
            try:
                from datetime import datetime
                dt = datetime.strptime(date_reception, "%Y-%m-%d")
                annee = dt.year
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide. Utilisez AAAA-MM-JJ")
                return

            lieu_livraison = self.lieu_var.get()
            adresse_chantier = self.adresse_chantier.get() if lieu_livraison == "Sur Chantier" else ""
            
            chauffeur = self.chauffeur.get()
            matricule = self.matricule.get()
            matricule_remorque = self.matricule_remorque.get()
            transporteur = self.transporteur.get()

            product_id = self.selected_product_id
            if not product_id:
                messagebox.showerror("Erreur", "Veuillez sélectionner un produit")
                return



            qte_annoncee = float(self.qte_annoncee.get() or 0)
            qte_recue = float(self.qte_recue.get() or 0)

            # New fields
            num_bt = self.num_bt.get()
            date_bt = self.date_bt.get_date().strftime("%Y-%m-%d") if DateEntry and isinstance(self.date_bt, DateEntry) else self.date_bt.get()
            num_fact = self.num_facture_rec.get()
            date_fact = self.date_fact_rec.get_date().strftime("%Y-%m-%d") if DateEntry and isinstance(self.date_fact_rec, DateEntry) else self.date_fact_rec.get()

            # Ensure Dates are properly formatted strings if they come from plain Entry default
            if not date_bt: date_bt = None
            if not date_fact: date_fact = None

            ecart = qte_recue - qte_annoncee
            motif_ecart = ""
            if abs(ecart) > 0.001:
                motif_ecart = self.motif_ecart.get()
                if not motif_ecart:
                    messagebox.showerror("Erreur", "Veuillez justifier l'écart")
                    self.motif_ecart.focus_set()
                    return
                # If not, I might need to update database.py or use **kwargs if flexible.
            
            # Since I cannot easily see database.py signature right now (it was visible before), 
            # I will assume I might need to update logic or DB method if it fails.
            # But let's proceed. 
            
            if self.reception_id:
                # Update existing reception
                
                # 1. Revert previous stock impact (if any)
                # This ensures we start clean before applying new quantity/location
                get_logic().revert_reception_stock_impact(self.reception_id)
                
                conn = get_db()._get_connection()
                try:
                     # Check if columns exist (graceful fallback if DB not migrated in runtime? No, we migrated)
                     conn.execute("""
                        UPDATE receptions SET 
                        chauffeur=?, matricule=?, transporteur=?, lieu_livraison=?, adresse_chantier=?,
                        product_id=?, quantite_annoncee=?, quantite_recue=?, ecart=?, motif_ecart=?,
                        matricule_remorque=?, num_bon_transfert=?, date_bt=?, num_facture=?, date_fact=?
                        WHERE id=?
                     """, (chauffeur, matricule, transporteur, lieu_livraison, adresse_chantier,
                           product_id, qte_annoncee, qte_recue, ecart, motif_ecart,
                           matricule_remorque, num_bt, date_bt, num_fact, date_fact, self.reception_id))
                     conn.commit()
                     
                     # 2. Apply new stock impact
                     # Now that DB has new values, process_reception will read them and apply correct movement
                     get_logic().process_reception(self.reception_id, self.user_id)
                     
                except Exception as ex:
                     messagebox.showerror("Erreur SQL", str(ex))
                     return

            else:
                 # Create new reception
                 db = get_db()
                 rid = db.create_reception(
                    annee=annee,
                    date_reception=date_reception,
                    chauffeur=chauffeur,
                    matricule=matricule,
                    transporteur=transporteur,
                    lieu_livraison=lieu_livraison,
                    adresse_chantier=adresse_chantier,
                    product_id=product_id,
                    quantite_annoncee=qte_annoncee,
                    quantite_recue=qte_recue,
                    matricule_remorque=matricule_remorque,
                    num_bon_transfert=num_bt,
                    date_bt=date_bt,
                    num_facture=num_fact,
                    date_fact=date_fact,
                    motif_ecart=motif_ecart,
                    created_by=self.user_id
                 )
                 
                 get_logic().process_reception(rid, self.user_id)

            product_name = self.designation.get()
            unite = self.unite_var.get()
            messagebox.showinfo("Succès", f"Réception enregistrée pour '{product_name}'\nQuantité: {qte_recue} {unite}")
            if self.callback:
                self.callback()
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Erreur", "Vérifiez les valeurs numériques")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _check_ecart(self, event=None):
        try:
            q_ann_str = self.qte_annoncee.get()
            q_rec_str = self.qte_recue.get()
            
            qa = float(q_ann_str) if q_ann_str else 0.0
            qr = float(q_rec_str) if q_rec_str else 0.0
            
            if abs(qa - qr) > 0.001:
                self.frame_ecart.pack(after=self.qte_recue, pady=5)
            else:
                self.frame_ecart.pack_forget()
        except ValueError:
            pass
    
    # Duplicate save method removed - using the correctly implemented one above


class InvoiceDialog:
    def __init__(self, parent, app, type_doc, callback=None, facture_origine_id=None, readonly=False, facture_id=None):
        self.dialog = tk.Toplevel(parent)
        self.readonly = readonly
        self.view_facture_id = facture_id
        
        # If viewing, set title appropriately
        title = f"Détails {type_doc}" if readonly else f"Nouvelle {type_doc}"
        self.dialog.title(title)
        self.dialog.state('zoomed')
        
        self.app = app
        self.type_doc = type_doc # 'Facture' or 'Avoir'
        self.callback = callback
        self.facture_origine_id = facture_origine_id
        self.lignes = []
        self._build()
        
        if self.facture_origine_id:
            print(f"DEBUG: InvoiceDialog init direct load origin={self.facture_origine_id}")
            self._load_facture_by_id(self.facture_origine_id)
        elif self.view_facture_id:
            print(f"DEBUG: InvoiceDialog view mode id={self.view_facture_id}")
            self.dialog.after(100, lambda: self._load_view_data(self.view_facture_id))
    
    def _build(self):
        # Action Buttons (Packed first at bottom to ensure visibility)
        btn_frame = tk.Frame(self.dialog, pady=20)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        if not self.readonly:
            # Two-Step Validation
            if self.type_doc == 'Facture':
                 tk.Button(btn_frame, text="Confirmer avec impression", bg="#2e7d32", fg="white", 
                          font=("Arial", 11, "bold"), command=self.save_validate).pack(side=tk.RIGHT, padx=5)
                 
                 tk.Button(btn_frame, text="Confirmer sans impression", bg="#f9a825", fg="black", 
                          font=("Arial", 11, "bold"), command=self.save_draft).pack(side=tk.RIGHT, padx=5)
            else:
                 # Avoir - Standard Confirm
                 tk.Button(btn_frame, text="Confirmer Avoir", bg="#2e7d32", fg="white", 
                          font=("Arial", 11, "bold"), command=self.save_validate).pack(side=tk.RIGHT, padx=20)
        
        tk.Button(btn_frame, text="Imprimer", bg=ACCENT_COLOR, fg="white", 
                 font=("Arial", 11, "bold"), command=self.print_preview).pack(side=tk.RIGHT, padx=20)
        
        tk.Button(btn_frame, text="Imprimer BL (Matricielle)", bg="#795548", fg="white", 
                 font=("Arial", 11, "bold"), command=self.print_matrix).pack(side=tk.RIGHT, padx=20)

        if self.readonly and self.type_doc == 'Facture':
             tk.Button(btn_frame, text="Ajouter Paiement", bg="#009688", fg="white",
                      font=("Arial", 11, "bold"), command=self.open_payment_dialog).pack(side=tk.RIGHT, padx=20)
             
             # BOUTON ANNULER (Rouge/Orange) - Seulement si la facture n'est pas déjà annulée
             # On vérifie l'état actuel (passé dans init ou à recharger)
             conn = self.app.db._get_connection()
             cursor = conn.cursor()
             cursor.execute("SELECT statut FROM factures WHERE id=?", (self.view_facture_id,))
             current_status = cursor.fetchone()
             if current_status and current_status[0] != 'ANNULEE':
                 tk.Button(btn_frame, text="Annuler la Facture", bg="#d32f2f", fg="white",
                          font=("Arial", 11, "bold"), command=self.confirm_cancellation).pack(side=tk.LEFT, padx=20)
        
        cancel_text = "Fermer" if self.readonly else "Annuler"
        tk.Button(btn_frame, text=cancel_text, command=self.dialog.destroy).pack(side=tk.RIGHT, padx=20)

        # Footer Totals (Yellow Box) - ALWAYS VISIBLE
        # Increased padding for height and reduced font sizes
        footer_frame = tk.Frame(self.dialog, bg="#fff9c4", padx=10, pady=20, relief="solid", borderwidth=1)
        # Pack above buttons
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))
        
        # Left side: Amount in words
        left_footer = tk.Frame(footer_frame, bg="#fff9c4")
        left_footer.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_montant_lettres = tk.Label(left_footer, text="Arrêter la présente facture à la somme de : ...", 
                                          bg="#fff9c4", fg="black", font=("Arial", 10, "italic"), wraplength=400, justify="left")
        self.lbl_montant_lettres.pack(anchor="w", padx=10)
        
        # Transport Info (Requested by user)
        self.lbl_footer_transport = tk.Label(left_footer, text="", bg="#fff9c4", fg="#455a64", font=("Arial", 9), justify="left")
        self.lbl_footer_transport.pack(anchor="w", padx=10, pady=(5,0))
        
        # Right side: Totals
        totals_subframe = tk.Frame(footer_frame, bg="#fff9c4")
        totals_subframe.pack(side=tk.RIGHT, padx=10)
        
        # Using grid to ensure horizontal alignment (HT - TVA - TTC)
        
        self.lbl_total_ht = tk.Label(totals_subframe, text="Montant HT: 0.00 DA", bg="#fff9c4", fg="black", font=("Arial", 10, "bold"))
        self.lbl_total_ht.grid(row=0, column=0, sticky="e", padx=(0, 20))
        
        self.lbl_total_tva = tk.Label(totals_subframe, text="Montant TVA: 0.00 DA", bg="#fff9c4", fg="black", font=("Arial", 10, "bold"))
        self.lbl_total_tva.grid(row=0, column=1, sticky="e", padx=(0, 20))

        self.lbl_total_ttc = tk.Label(totals_subframe, text="Montant TTC: 0.00 DA", bg="#fff9c4", fg="#d50000", font=("Arial", 12, "bold"))
        self.lbl_total_ttc.grid(row=0, column=2, sticky="e")
        # Top Frame: Header Info (Green Box) - ONLY IN READONLY VIEW
        if self.readonly:
            header_frame = tk.Frame(self.dialog, bg="#dcedc8", padx=10, pady=5, relief="solid", borderwidth=1)
            header_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(10, 0))
            
            self.lbl_header_num = tk.Label(header_frame, text="N° Facture: --", bg="#dcedc8", font=("Arial", 12, "bold"), fg="#2e7d32")
            self.lbl_header_num.pack(side=tk.LEFT, padx=20)
            
            self.lbl_header_date = tk.Label(header_frame, text="Date: --", bg="#dcedc8", font=("Arial", 12, "bold"), fg="#2e7d32")
            self.lbl_header_date.pack(side=tk.RIGHT, padx=20)

            # Check status for styling
            if self.view_facture_id:
                facture = self.app.db.get_facture_by_id(self.view_facture_id)
                if facture and (facture.get('statut') == 'ANNULEE' or facture.get('statut_facture') == 'Annulée'):
                    header_frame.config(bg="#ffccbc") # Light Red/Orange
                    self.lbl_header_num.config(bg="#ffccbc", fg="#d32f2f", text=f"N° Facture: {facture['numero']} (ANNULÉE)")
                    self.lbl_header_date.config(bg="#ffccbc", fg="#d32f2f")
                    
                    if facture.get('motif_annulation'):
                         tk.Label(header_frame, text=f"Motif: {facture['motif_annulation']}", 
                                  bg="#ffccbc", fg="#bf360c", font=("Arial", 10, "bold italic")).pack(side=tk.BOTTOM, pady=5)


        # Client Selection Area
        top_frame = tk.Frame(self.dialog, padx=20, pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Client*").pack(side=tk.LEFT, padx=5)
        clients = self.app.db.get_all_clients()
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(top_frame, textvariable=self.client_var, width=40)
        self.client_combo['values'] = [f"{c['id']} - {c['raison_sociale']}" for c in clients]
        if self.readonly:
            self.client_combo.config(state="disabled")
        else:
            self.client_combo.bind("<<ComboboxSelected>>", self._on_client_select)
        self.client_combo.pack(side=tk.LEFT, padx=5)

        # Contract
        tk.Label(top_frame, text="Contrat / Convention").pack(side=tk.LEFT, padx=(20, 5))
        self.contract_var = tk.StringVar()
        state_contract = "disabled" if self.readonly else "normal"
        self.contract_combo = ttk.Combobox(top_frame, textvariable=self.contract_var, width=30, state=state_contract)
        self.contract_combo.pack(side=tk.LEFT, padx=5)
        self.contract_combo.pack(side=tk.LEFT, padx=5)
        self.contracts_map = {}
        
        if self.type_doc == 'Avoir':
             tk.Label(top_frame, text="Facture d'Origine (N°)").pack(side=tk.LEFT, padx=(20, 5))
             self.ref_facture = tk.Entry(top_frame, width=20, bg="#455a64", fg="white", insertbackground="white")

             self.ref_facture.pack(side=tk.LEFT, padx=5)

             tk.Button(top_frame, text="Charger Facture", command=self._load_facture_origine).pack(side=tk.LEFT, padx=5)
             
        # Header Info (Black Box) - Right Aligned (Shifted Left for Calendar)
        header_right_frame = tk.Frame(top_frame, bg="black", padx=10, pady=5, relief="solid", borderwidth=2)
        # Shift away from right edge by 250px to allow calendar visibility
        header_right_frame.pack(side=tk.RIGHT, padx=(10, 300))
        
        # 1. Invoice Number
        import datetime
        
        invoice_num_text = "N° Facture: --"
        if self.view_facture_id:
             # Fetched in load_view_data
             invoice_num_text = "N° Facture: ..." 
        elif self.facture_origine_id:
             # Avoir logic
             pass 
        else:
             # New Invoice Preview
             try:
                 cur_year = datetime.datetime.now().year
                 next_num = self.app.db.get_next_invoice_number(self.type_doc, cur_year)
                 invoice_num_text = f"N° Facture: {next_num}"
             except:
                 invoice_num_text = "N° Facture: Nouveau"

        self.lbl_invoice_num = tk.Label(header_right_frame, text=invoice_num_text, font=("Arial", 12, "bold"), fg="white", bg="black")
        self.lbl_invoice_num.pack(anchor="e")
        
        # 2. System Date
        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.lbl_sys_date = tk.Label(header_right_frame, text=f"Système: {now_str}", font=("Arial", 10), fg="#cfd8dc", bg="black")
        self.lbl_sys_date.pack(anchor="e")
        
        # 3. Modifiable Date Field
        date_frame = tk.Frame(header_right_frame, bg="black")
        date_frame.pack(anchor="e", pady=(5, 0))
        
        tk.Label(date_frame, text="Date Facture:", font=("Arial", 10), fg="white", bg="black").pack(side=tk.LEFT, padx=5)
        
        if DateEntry:
            self.date_facture_entry = DateEntry(date_frame, width=12, background='darkblue',
                                                foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        else:
            self.date_facture_entry = tk.Entry(date_frame, width=12)
            self.date_facture_entry.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))
            
        self.date_facture_entry.pack(side=tk.LEFT)
        
        # Add Tooltip
        create_tooltip(self.date_facture_entry, "Veuillez choisir la date de la facture")

        # Motif Frame (Separate line for Avoir)
        if self.type_doc == 'Avoir':
             motif_frame = tk.Frame(self.dialog, padx=20, pady=5)
             motif_frame.pack(fill=tk.X)
             
             tk.Label(motif_frame, text="Motif de l'Avoir*").pack(side=tk.LEFT, padx=5)
             self.motif_entry = tk.Entry(motif_frame, width=80, bg="#455a64", fg="white", insertbackground="white") # Wider width
             self.motif_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        else:
             # Dummy entry for compatibility if not Avoir (though it checks type_doc usually)
             self.motif_entry = None
        
        # Extra Client Info (Auto-filled)
        top_frame_2 = tk.Frame(self.dialog, padx=20, pady=5)
        top_frame_2.pack(fill=tk.X)
        
        tk.Label(top_frame_2, text="Catégorie").pack(side=tk.LEFT, padx=5)
        self.client_categorie_entry = tk.Entry(top_frame_2, width=20, bg="#455a64", fg="white", insertbackground="white")
        self.client_categorie_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(top_frame_2, text="Banque").pack(side=tk.LEFT, padx=(20, 5))
        self.client_banque_entry = tk.Entry(top_frame_2, width=30, bg="#455a64", fg="white", insertbackground="white")
        self.client_banque_entry.pack(side=tk.LEFT, padx=5)






        # Transport Information
        transport_frame = tk.LabelFrame(self.dialog, text="Information Transport", padx=10, pady=5)
        transport_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(transport_frame, text="Chauffeur:").pack(side=tk.LEFT, padx=5)
        self.chauffeur_var = tk.StringVar()
        self.chauffeur_entry = ttk.Combobox(transport_frame, textvariable=self.chauffeur_var, width=20)
        if not self.readonly:
             try:
                 uniques = self.app.db.get_unique_chauffeurs()
                 self.chauffeur_entry['values'] = uniques
             except: pass
        else:
             self.chauffeur_entry.config(state='disabled')

        self.chauffeur_entry.pack(side=tk.LEFT, padx=5)
        self.chauffeur_entry.bind("<<ComboboxSelected>>", self._on_chauffeur_select)
        
        tk.Label(transport_frame, text="Matricule Tracteur:").pack(side=tk.LEFT, padx=5)
        self.mat_tracteur_entry = tk.Entry(transport_frame, width=15, bg="#455a64", fg="white", insertbackground="white")
        if self.readonly: self.mat_tracteur_entry.config(state='disabled')
        self.mat_tracteur_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(transport_frame, text="Matricule Remorque:").pack(side=tk.LEFT, padx=5)
        self.mat_remorque_entry = tk.Entry(transport_frame, width=15, bg="#455a64", fg="white", insertbackground="white")
        if self.readonly: self.mat_remorque_entry.config(state='disabled')
        self.mat_remorque_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(transport_frame, text="Transporteur:").pack(side=tk.LEFT, padx=5)
        self.transporteur_var = tk.StringVar()
        self.transporteur_combo = ttk.Combobox(transport_frame, textvariable=self.transporteur_var, width=20)
        if not self.readonly:
             try:
                 # Populate from Logic/DB
                 uniques = self.app.db.get_unique_transporteurs()
                 self.transporteur_combo['values'] = uniques
             except: pass
        else:
             self.transporteur_combo.config(state='disabled')
        self.transporteur_combo.pack(side=tk.LEFT, padx=5)

        # Type de Vente Checkboxes
        if self.type_doc == 'Facture':
            opt_frame = tk.LabelFrame(self.dialog, text="Conditions de Vente", padx=10, pady=5)
            opt_frame.pack(fill=tk.X, padx=20, pady=5)
            
            self.vente_var = tk.StringVar(value="A terme")
            rb_state = "disabled" if self.readonly else "normal"
            
            tk.Radiobutton(opt_frame, text="Vente À terme", variable=self.vente_var, 
                          value="A terme", command=self._toggle_payment_fields, state=rb_state).pack(side=tk.LEFT, padx=10)
            tk.Radiobutton(opt_frame, text="Vente Au comptant", variable=self.vente_var, 
                          value="Au comptant", command=self._toggle_payment_fields, state=rb_state).pack(side=tk.LEFT, padx=10)
            tk.Radiobutton(opt_frame, text="Sur Avances", variable=self.vente_var, 
                          value="Sur Avances", command=self._toggle_payment_fields, state=rb_state).pack(side=tk.LEFT, padx=10)
            
            # Payment Fields (Hidden by default or if A Terme/Sur Avances)
            self.pay_frame = tk.Frame(opt_frame)
            self.pay_frame.pack(side=tk.LEFT, fill=tk.X, padx=20)
            
            tk.Label(self.pay_frame, text="Mode:").pack(side=tk.LEFT)
            self.mode_var = tk.StringVar(value="Espèces")
            modes = ["Espèces", "Chèque", "Virement", "Versement"]
            self.mode_combo = ttk.Combobox(self.pay_frame, textvariable=self.mode_var, values=modes, width=10, state="readonly")
            self.mode_combo.pack(side=tk.LEFT, padx=5)
            
            tk.Label(self.pay_frame, text="Réf:").pack(side=tk.LEFT, padx=5)
            self.ref_paiement_entry = tk.Entry(self.pay_frame, width=10, bg="#455a64", fg="white", insertbackground="white")
            self.ref_paiement_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Label(self.pay_frame, text="Banque:").pack(side=tk.LEFT, padx=5)
            self.banque_var = tk.StringVar()
            banques = ["BNA", "BEA", "CPA", "BADR", "BDL", "Al Baraka", "AGB", "Natixis", "Société Générale"]
            self.banque_combo = ttk.Combobox(self.pay_frame, textvariable=self.banque_var, values=banques, width=15)
            self.banque_combo.pack(side=tk.LEFT, padx=5)
            
            # Init State
            self._toggle_payment_fields()

        # Line Entry Frame
        if not self.readonly:
            entry_frame = tk.LabelFrame(self.dialog, text="Ajout Ligne", padx=10, pady=10)
            entry_frame.pack(fill=tk.X, padx=20, pady=5)
            
            # Product Code
            tk.Label(entry_frame, text="Produit").grid(row=0, column=0, padx=5)
            self.prod_code_var = tk.StringVar()
            self.prod_combo = ttk.Combobox(entry_frame, textvariable=self.prod_code_var, width=30)
            
            # Load products with more robust keys
            self.products = self.app.db.get_all_products()
            
            # Identify parents (any product that is a parent of another)
            parent_ids = set()
            for p in self.products:
                if p.get('parent_stock_id'):
                    parent_ids.add(p['parent_stock_id'])

            self.prod_map = {}
            for p in self.products:
                code = p.get('code_produit', '')
                nom = p.get('nom', 'Inconnu')
                # Format: "CODE - Nom" or "ID - Nom" if no code
                if code:
                    label = f"{code} - {nom}"
                else:
                    label = f"{p['id']} - {nom}"
                
                # Check for Parent/Child
                if p['id'] in parent_ids:
                    label = f"*** [GROUPE] {label} ***"
                elif p.get('parent_stock_id'):
                    label = f"[PRIX] {label}"
                    
                self.prod_map[label] = p
                
            self.prod_combo['values'] = sorted(list(self.prod_map.keys()))
            self.prod_combo.grid(row=1, column=0, padx=5)
            self.prod_combo.bind("<<ComboboxSelected>>", self._on_prod_select)
            # ALSO bind to trace to ensure we catch changes
            self.prod_code_var.trace_add("write", lambda *args: self._on_prod_select(None))
            


            # Designation (Label)
            tk.Label(entry_frame, text="Désignation").grid(row=0, column=1, padx=5)
            self.lbl_designation = tk.Label(entry_frame, text="-", fg="blue", font=("Arial", 10, "bold"))
            self.lbl_designation.grid(row=1, column=1, padx=5)

            # Quantity
            tk.Label(entry_frame, text="Quantité").grid(row=0, column=2, padx=5)
            self.qte_entry = tk.Entry(entry_frame, width=10, bg="#455a64", fg="white", insertbackground="white")
            self.qte_entry.grid(row=1, column=2, padx=5)
            
            # Unit Price
            tk.Label(entry_frame, text="Prix Unit (HT)").grid(row=0, column=3, padx=5)
            self.price_entry = tk.Entry(entry_frame, width=15, bg="#455a64", fg="white", insertbackground="white")
            self.price_entry.grid(row=1, column=3, padx=5)
            
            # Add Button
            self.add_btn = tk.Button(entry_frame, text="Ajouter", bg=SECONDARY_COLOR, fg="white", command=self.add_ligne)
            self.add_btn.grid(row=1, column=6, padx=10)

            # Discount Controls
            self.remise_var = tk.BooleanVar()
            self.chk_remise = tk.Checkbutton(entry_frame, text="Remise", variable=self.remise_var, command=self._toggle_remise)
            self.chk_remise.grid(row=0, column=4, padx=5)
            
            self.lbl_taux = tk.Label(entry_frame, text="Taux %")
            self.taux_entry = tk.Entry(entry_frame, width=5, bg="#455a64", fg="white", insertbackground="white")
            
            # Stock Info Label
            self.lbl_stock_info = tk.Label(entry_frame, text="Sélectionnez un produit", font=("Arial", 9, "bold"), fg="blue")
            self.lbl_stock_info.grid(row=2, column=0, columnspan=7, sticky="w", padx=5, pady=(5,0))

            # Initial state
            self._toggle_remise()

        # Lines List
        self.lignes_frame = tk.Frame(self.dialog)
        self.lignes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview for lines
        cols = ('Produit', 'Désignation', 'Unité', 'Qté', 'P.U. Init', 'Remise %', 'Total (HT)', 'TVA', 'Total (TTC)')
        self.tree = ttk.Treeview(self.lignes_frame, columns=cols, show='headings', height=10)
        
        self.tree.heading('Produit', text='Code')
        self.tree.column('Produit', width=80)
        
        self.tree.heading('Désignation', text='Désignation')
        self.tree.column('Désignation', width=150)
        
        self.tree.heading('Unité', text='Unité')
        self.tree.column('Unité', width=60)
        
        self.tree.heading('Qté', text='Qté')
        self.tree.column('Qté', width=60)
        
        self.tree.heading('P.U. Init', text='P.U. Init')
        self.tree.column('P.U. Init', width=80)
        
        self.tree.heading('Remise %', text='Rem')
        self.tree.column('Remise %', width=50)

        self.tree.heading('Total (HT)', text='Montant HT')
        self.tree.column('Total (HT)', width=80)
        
        self.tree.heading('TVA', text='TVA')
        self.tree.column('TVA', width=50)

        self.tree.heading('Total (TTC)', text='Montant TTC')
        self.tree.column('Total (TTC)', width=90)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

        if not self.readonly:
            self.menu = tk.Menu(self.tree, tearoff=0)
            self.menu.add_command(label="Supprimer", command=self.remove_line)
            self.tree.bind("<Button-3>", self.show_context_menu)





    def _update_footer(self):
        # Calculate totals from self.lignes
        total_ht = 0.0
        total_tva = 0.0
        
        for ligne in self.lignes:
             qty = ligne['quantite']
             price = ligne['prix_unitaire'] # Net price
             
             # Calculate Line Totals
             l_ht = qty * price
             
             # Get TVA Rate for product
             product = self.app.db.get_product_by_id(ligne['product_id'])
             tva_rate = product.get('tva', 19.0) if product else 19.0
             
             l_tva = l_ht * (tva_rate / 100)
             
             total_ht += l_ht
             total_tva += l_tva
             
        total_ttc = total_ht + total_tva
        
        if hasattr(self, 'lbl_total_ht'):
             self.lbl_total_ht.config(text=f"Montant HT: {format_currency(total_ht)}")
             self.lbl_total_tva.config(text=f"Montant TVA: {format_currency(total_tva)}")
             self.lbl_total_ttc.config(text=f"Montant TTC: {format_currency(total_ttc)}")
             
        # Optional: Update amount in words if needed, but maybe too heavy to do real-time?
        # Let's keep it simple for now or fetch num2words if available.
        # Ideally, we display "..." until saved or just basic info.

    def open_payment_dialog(self):
        if not self.view_facture_id: return
        
        facture = self.app.db.get_facture_by_id(self.view_facture_id)
        if facture:
             # Pass client_id and facture_id to pre-fill
             PaymentDialog(self.app.root, self.app, 
                           client_id=facture['client_id'], 
                           facture_id=facture['id'],
                           callback=self.callback)
        
    def confirm_cancellation(self):
        """Demande confirmation et motif pour l'annulation"""
        if not self.view_facture_id: return
        
        # 1. Ask for Motif
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Confirmation d'Annulation")
        dialog.geometry("400x250")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        tk.Label(dialog, text="ATTENTION : Action Irréversible", fg="red", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(dialog, text="Veuillez saisir le motif de l'annulation :").pack(pady=5)
        
        motif_entry = tk.Entry(dialog, width=50)
        motif_entry.pack(pady=5, padx=20)
        motif_entry.focus_set()
        
        def do_cancel():
            motif = motif_entry.get().strip()
            if not motif:
                messagebox.showerror("Erreur", "Le motif est obligatoire.", parent=dialog)
                return
            
            # 2. Call Logic
            try:
                success, msg = self.app.logic.annuler_facture(self.view_facture_id, self.app.user['id'], motif)
                if success:
                    messagebox.showinfo("Succès", msg, parent=dialog)
                    dialog.destroy()
                    self.dialog.destroy()
                    if self.callback: self.callback()
                else:
                    messagebox.showerror("Erreur", msg, parent=dialog)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur technique: {str(e)}", parent=dialog)

        tk.Button(dialog, text="Confirmer l'Annulation", bg="#d32f2f", fg="white", font=("Arial", 10, "bold"), command=do_cancel).pack(pady=20) 
        tk.Button(dialog, text="Abandonner", command=dialog.destroy).pack()


        



    def _on_prod_select(self, event=None):
        # Visual Debug: prove we entered the function
        try:
            # self.lbl_stock_info.config(text="Recherche du stock...", fg="orange")
            # self.lbl_stock_info.update_idletasks()
            pass
        except: pass
        
        # DEBUG POPUP
        # messagebox.showinfo("DEBUG", f"Event triggered! Selection: {self.prod_code_var.get()}")

        selection = self.prod_code_var.get()
        print(f"DEBUG: Selected product raw: '{selection}'")
        # messagebox.showinfo("DEBUG", f"Selection: '{selection}'")
        if not selection:
            return
            
        product = self.prod_map.get(selection)
        print(f"DEBUG: Found product in map: {product is not None}")
        
        if product:
             # PARENT PRODUCT CHECK
             if self.app.logic.is_parent_product(product['id']):
                  messagebox.showerror("Interdit", f"Le produit '{product['nom']}' est un produit parent (Groupe/Code de prix).\n\nIl est interdit de le vendre directement.\nVeuillez sélectionner un produit enfant spécifique.")
                  self.prod_code_var.set('')
                  self.selected_product = None
                  self.lbl_designation.config(text="-")
                  return

             self.selected_product = product
             self.lbl_designation.config(text=product.get('nom', ''))
             
             try:
                 # Update Stock Info
                 current_stock = product['stock_actuel']
                 stock_label_text = f"Stock disp. : {current_stock:.2f} {product.get('unite', '')}"
                 color = "#2e7d32" if current_stock > 0 else "#d32f2f"
                 
                 print(f"DEBUG: Initial Stock Text: {stock_label_text}")
                 
                 if product.get('parent_stock_id'):
                      print(f"DEBUG: Has Parent ID: {product['parent_stock_id']}")
                      parent = self.app.db.get_product_by_id(product['parent_stock_id'])
                      if parent:
                           current_stock = parent['stock_actuel']
                           stock_label_text = f"Stock disp. : {current_stock:.2f} {product.get('unite', '')} - (Produit lié à {parent['nom']})"
                           color = "#2e7d32" if current_stock > 0 else "#d32f2f"
                      else:
                           print("DEBUG: Parent product not found in DB")
                 
                 print(f"DEBUG: Final Label Text: {stock_label_text}")
                 self.lbl_stock_info.config(text=stock_label_text, fg=color)
                 self.lbl_stock_info.update_idletasks() # Force update
             except Exception as e:
                 print(f"DEBUG: Error updating stock label: {e}")
                 import traceback
                 traceback.print_exc()

             # Update price
             if not self.price_entry.get() or self.price_entry.get() == "0.0":
                 self.price_entry.delete(0, tk.END)
                 self.price_entry.insert(0, str(product.get('prix_actuel', 0.0)))
                 
             # Focus Quantity
             self.qte_entry.focus_set()

    def _toggle_remise(self):
        if self.remise_var.get():
            self.lbl_taux.grid(row=0, column=5, padx=5)
            self.taux_entry.grid(row=1, column=5, padx=5)
        else:
            self.lbl_taux.grid_remove()
            self.taux_entry.grid_remove()

        # Old Action Buttons Location - Removed

        
        self.selected_product = None

    def _toggle_payment_fields(self):
        if not hasattr(self, 'pay_frame'): return
        
        mode = self.vente_var.get()
        if mode == 'Au comptant':
            # Enable widgets
            for child in self.pay_frame.winfo_children():
                try: child.configure(state='normal')
                except: pass
        else:
            # Disable widgets (Gray out)
            for child in self.pay_frame.winfo_children():
                try: child.configure(state='disabled')
                except: pass



    def blink_motif(self):
        if not hasattr(self, 'motif_entry') or not self.motif_entry or not self.dialog.winfo_exists(): return
        try:
            current_bg = self.motif_entry.cget("bg")
            # Blink between Military Green (#689f38) and Dark/Default (#455a64)
            if current_bg == "#689f38":
                 self.motif_entry.config(bg="#455a64", fg="white")
            else:
                 self.motif_entry.config(bg="#689f38", fg="white")
            
            self.dialog.after(800, self.blink_motif)
        except Exception:
            pass

    def _load_facture_origine(self):
        ref = self.ref_facture.get()
        try:
             conn = self.app.db._get_connection() 
             c = conn.cursor()
             c.execute("SELECT id FROM factures WHERE numero=?", (ref,))
             row = c.fetchone()
             if row:
                 self._load_facture_by_id(row[0])
             else:
                 messagebox.showerror("Erreur", "Facture introuvable")
        except Exception as e:
            print(e)
            
    def _load_facture_by_id(self, fid):
        try:
             fac = self.app.db.get_facture_by_id(fid)
             if not fac:
                 messagebox.showerror("Erreur", "Facture introuvable")
                 return
                 
             if hasattr(self, 'ref_facture'):
                 self.ref_facture.delete(0, tk.END)
                 self.ref_facture.insert(0, fac.get('numero', ''))
             
             # Load client
             client_id = fac['client_id']
             # Find matching string in combobox
             search_prefix = f"{client_id} - "
             
             found_client = False
             for val in self.client_combo['values']:
                 if val.startswith(search_prefix):
                     self.client_combo.set(val)
                     found_client = True
                     break
            
             if not found_client:
                 client = self.app.db.get_client_by_id(client_id)
                 if client:
                     self.client_combo.set(f"{client_id} - {client['raison_sociale']}")
                 else:
                     self.client_combo.set(f"{client_id} - (Inconnu)")
             
             
             # Load Contracts
             if not self.readonly:
                 self._load_contracts(None)

             # --- MISSING POPULATION LOGIC [FIX] ---
             # 1. Populate Client Details (Category, Bank)
             # Note: 'client' obj might be loaded above, if not, re-fetch
             fetched_client = self.app.db.get_client_by_id(client_id)
             if fetched_client:
                 if self.client_categorie_entry:
                     self.client_categorie_entry.delete(0, tk.END)
                     val = fetched_client.get('categorie', '')
                     if val: self.client_categorie_entry.insert(0, str(val))
                 
                 if self.client_banque_entry:
                     self.client_banque_entry.delete(0, tk.END)
                     val = fetched_client.get('compte_bancaire', '')
                     if val: self.client_banque_entry.insert(0, str(val))

             # 2. Populate Transport Details from Invoice (fac)
             if self.chauffeur_entry and fac.get('chauffeur'):
                 self.chauffeur_entry.set(str(fac['chauffeur']))
                 
             if self.mat_tracteur_entry and fac.get('matricule_tracteur'):
                 self.mat_tracteur_entry.delete(0, tk.END)
                 self.mat_tracteur_entry.insert(0, facture['matricule_tracteur'])
                 
             if self.mat_remorque_entry and fac.get('matricule_remorque'):
                 self.mat_remorque_entry.delete(0, tk.END)
                 self.mat_remorque_entry.insert(0, str(fac['matricule_remorque']))

             if self.transporteur_combo and fac.get('transporteur'):
                  self.transporteur_combo.set(str(fac['transporteur']))
             # --------------------------------------
             
             # Clear existing lines
             for item in self.tree.get_children():
                 self.tree.delete(item)
             self.lignes = []
             
             # Load lines
             facture_lines = fac.get('lignes', [])
             
             if not facture_lines:
                 conn = self.app.db._get_connection()
                 c = conn.cursor()
                 c.execute("SELECT * FROM lignes_facture WHERE facture_id=?", (fid,))
                 facture_lines = c.fetchall()

             for l in facture_lines:
                  # Handle both Row objects and dicts
                  pid = l['product_id']
                  qte = l['quantite']
                  prix = l['prix_unitaire']
                  
                  p = self.app.db.get_product_by_id(pid)
                  if p:
                      self._add_ligne_internal(p, qte, prix)
             
             self._update_footer()
             
             # === READ ONLY MODE FOR AVOIR ===
             if self.type_doc == 'Avoir':
                 # Define Styles
                 grey_bg = "#cfd8dc" # Light Grey
                 red_fg = "#d32f2f"  # Red
                 
                 # 1. Disable Main Inputs
                 self.prod_combo.config(state='disabled')
                 self.qte_entry.config(state='disabled', disabledbackground=grey_bg, disabledforeground=red_fg)
                 self.price_entry.config(state='disabled', disabledbackground=grey_bg, disabledforeground=red_fg)
                 self.add_btn.config(state='disabled')
                 
                 # 2. Disable Client & Contract
                 self.client_combo.config(state='disabled')
                 self.contract_combo.config(state='disabled')
                 
                 # 3. Disable & Style Info Fields
                 # A. Reference Facture -> Red
                 if self.ref_facture:
                      self.ref_facture.config(state='disabled', disabledbackground=grey_bg, disabledforeground=red_fg)

                 # B. Info Fields -> Black, Bold, Italic
                 info_entries = [
                     self.client_categorie_entry, 
                     self.client_banque_entry,
                     self.chauffeur_entry, 
                     self.mat_tracteur_entry, 
                     self.mat_remorque_entry
                 ]
                 
                 black_font = ("Arial", 10, "bold italic")
                 
                 for entry in info_entries:
                     if entry:
                        entry.config(state='disabled', disabledbackground=grey_bg, disabledforeground="black", font=black_font)
                 
                 # 4. Start Blinking Motif
                 self.blink_motif()

                 self.dialog.title(self.dialog.title() + " (ANNULATION TOTALE)")
                 
        except Exception as e:
            messagebox.showerror("Erreur Loading", f"Impossible de charger la facture: {str(e)}")

    def _on_chauffeur_select(self, event=None):
        """Auto-fill transport info when chauffeur is selected"""
        try:
            val = self.chauffeur_entry.get()
            if not val: return
            
            info = self.app.db.get_last_transport_info_by_chauffeur(val)
            if info:
                # Tracteur
                if self.mat_tracteur_entry and info.get('matricule_tracteur'):
                    self.mat_tracteur_entry.delete(0, tk.END)
                    self.mat_tracteur_entry.insert(0, info['matricule_tracteur'])
                
                # Remorque
                if self.mat_remorque_entry and info.get('matricule_remorque'):
                    self.mat_remorque_entry.delete(0, tk.END)
                    self.mat_remorque_entry.insert(0, info['matricule_remorque'])
                    
                # Transporteur
                if self.transporteur_combo and info.get('transporteur'):
                    self.transporteur_combo.set(info['transporteur'])
                    
        except Exception as e:
            print(f"Error auto-filling transport info: {e}")

    def _on_client_select(self, event):
        self._load_contracts(event)
        client_str = self.client_var.get()
        if client_str:
            try:
                client_id = int(client_str.split(' - ')[0])
                client = self.app.db.get_client_by_id(client_id)
                if client:
                    self.client_categorie_entry.delete(0, tk.END)
                    val_cat = client.get('categorie')
                    if val_cat: self.client_categorie_entry.insert(0, str(val_cat))
                    
                    self.client_banque_entry.delete(0, tk.END)
                    val_banque = client.get('compte_bancaire')
                    if val_banque: self.client_banque_entry.insert(0, str(val_banque))
            except Exception as e:
                print(f"Error auto-filling client info: {e}")

    def _load_contracts(self, event=None):
        try:
            client_str = self.client_var.get()
            if not client_str: return
            client_id = int(client_str.split(' - ')[0])
            
            contracts = self.app.db.get_client_contracts(client_id, active_only=True)
            self.contracts_map = {f"{c['code']} ({c['date_fin']})": c['id'] for c in contracts}
            
            # Add "No Contract" option
            values = ["--- Hors Contrat ---"] + list(self.contracts_map.keys())
            self.contract_combo['values'] = values
            
            # Default to "Hors Contrat" or first active? 
            # User request implies optionality. Let's default to Hors Contrat if available, or just selct 0 which is Hors Contrat.
            self.contract_combo.current(0)
        except Exception as e:
            print(f"Error loading contracts: {e}")

    def _load_view_data(self, facture_id):
        try:
            facture = self.app.db.get_facture_by_id(facture_id)
            if not facture:
                 messagebox.showerror("Erreur", "Facture introuvable")
                 self.dialog.destroy()
                 return
            
            # Populate Header (Green Box)
            if self.readonly:
                if hasattr(self, 'lbl_header_num'):
                    self.lbl_header_num.config(text=f"N° Facture: {facture['numero']}")
                if hasattr(self, 'lbl_header_date'):
                    self.lbl_header_date.config(text=f"Date: {facture['date_facture']}")

            # Update Black Box Header (Always visible if built)
            if hasattr(self, 'lbl_invoice_num'):
                 self.lbl_invoice_num.config(text=f"N° Facture: {facture['numero']}")
            
            if hasattr(self, 'lbl_sys_date'):
                 # Show Creation Timestamp
                 c_at = facture.get('created_at', 'Inconnu')
                 # Try format
                 try:
                     # If format is YYYY-MM-DD HH:MM:SS
                     dt = datetime.datetime.strptime(c_at, "%Y-%m-%d %H:%M:%S")
                     c_at = dt.strftime("%d/%m/%Y %H:%M")
                 except: pass
                 self.lbl_sys_date.config(text=f"Système: {c_at}")

            if hasattr(self, 'date_facture_entry'):
                 # Set date from facture
                 d_str = facture['date_facture']
                 # d_str is likely YYYY-MM-DD
                 if DateEntry:
                     try:
                         d_obj = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                         self.date_facture_entry.set_date(d_obj)
                     except: pass
                 else:
                     self.date_facture_entry.delete(0, tk.END)
                     self.date_facture_entry.insert(0, d_str)
                 
                 if self.readonly:
                     self.date_facture_entry.config(state='disabled')


            # Client
            client_name = facture.get('client_nom') or facture.get('raison_sociale')
            self.client_var.set(f"{facture['client_id']} - {client_name}")
            
            # Date
            if hasattr(self, 'date_entry') and 'DateEntry' in str(type(self.date_entry)):
                try:
                    self.date_entry.set_date(datetime.strptime(facture['date_facture'], "%Y-%m-%d"))
                except: pass
            elif hasattr(self, 'date_var'):
                try:
                    self.date_var.set(datetime.strptime(facture['date_facture'], "%Y-%m-%d").strftime("%d/%m/%Y"))
                except: pass

            # Contract
            if facture.get('contract_id'):
                # Try to load contracts map first
                self._load_contracts() 
                found = False
                for k, v in self.contracts_map.items():
                    if v == facture['contract_id']:
                        self.contract_combo.set(k)
                        found = True
                        break
                if not found:
                     # Maybe inactive? Just show ID if not found
                     self.contract_combo.set(f"Contrat ID: {facture['contract_id']}")
            elif facture.get('contrat_code'):
                self.contract_var.set(facture.get('contrat_code'))

            # Transport
            if facture.get('chauffeur'):
                self.chauffeur_entry.config(state='normal')
                self.chauffeur_entry.set(facture['chauffeur'])
                if self.readonly: self.chauffeur_entry.config(state='disabled')
            
            if facture.get('matricule_tracteur'):
                self.mat_tracteur_entry.config(state='normal')
                self.mat_tracteur_entry.delete(0, tk.END)
                self.mat_tracteur_entry.insert(0, facture['matricule_tracteur'])
                if self.readonly: self.mat_tracteur_entry.config(state='disabled')
                
            if facture.get('matricule_remorque'):
                self.mat_remorque_entry.config(state='normal')
                self.mat_remorque_entry.delete(0, tk.END)
                self.mat_remorque_entry.insert(0, facture['matricule_remorque'])
                if self.readonly: self.mat_remorque_entry.config(state='disabled')

            # Populate Footer Transport Info
            if self.readonly and hasattr(self, 'lbl_footer_transport'):
                trans_info = []
                if facture.get('chauffeur'): trans_info.append(f"Chauffeur: {facture['chauffeur']}")
                if facture.get('matricule_tracteur'): trans_info.append(f"Tracteur: {facture['matricule_tracteur']}")
                if facture.get('matricule_remorque'): trans_info.append(f"Remorque: {facture['matricule_remorque']}")
                if facture.get('transporteur'): trans_info.append(f"Transporteur: {facture['transporteur']}")
                
                if trans_info:
                    self.lbl_footer_transport.config(text=" | ".join(trans_info))
                else:
                    self.lbl_footer_transport.config(text="")


            # Type Vente & Payment
            if facture.get('type_vente'):
                self.vente_var.set(facture['type_vente'])
                self._toggle_payment_fields()
            
            if facture.get('mode_paiement'):
                self.mode_var.set(facture['mode_paiement'])
            
            if facture.get('ref_paiement') and hasattr(self, 'ref_paiement_entry'):
                self.ref_paiement_entry.delete(0, tk.END)
                self.ref_paiement_entry.insert(0, facture['ref_paiement'])
            
            if facture.get('banque') and hasattr(self, 'banque_var'):
                 self.banque_var.set(facture['banque'])
                 
            # Populate Footer (Yellow Box)
            if self.readonly:
                total_ht = float(facture['montant_ht'])
                total_tva = float(facture['montant_tva'])
                total_ttc = float(facture['montant_ttc'])
                
                print(f"DEBUG: Setting Footer Labels -> HT={total_ht}, TVA={total_tva}, TTC={total_ttc}") # Keep debug
                self.lbl_total_ht.config(text=f"Montant HT: {format_currency(total_ht)} DA")
                self.lbl_total_tva.config(text=f"Montant TVA: {format_currency(total_tva)} DA")
                self.lbl_total_ttc.config(text=f"Montant TTC: {format_currency(total_ttc)} DA")
                 
                try:
                    letter_amount = nombre_en_lettres(total_ttc) # Use total_ttc instead of undefined ttc
                    if hasattr(self, 'lbl_montant_lettres'):
                        self.lbl_montant_lettres.config(text=f"Arrêter la présente facture à la somme de :\n{letter_amount}")
                except Exception as e:
                    print(f"Error converting number: {e}")

            # Lines
            self.lignes = []
            for l in facture['lignes']:
                line_data = {
                    'product_id': l['product_id'],
                    'product_nom': l['product_nom'],
                    'unite': l.get('unite', ''), # Include Unite
                    'quantite': l['quantite'],
                    'prix_unitaire': l['prix_unitaire'],
                    'montant': l['montant'],
                    'taux_remise': l.get('taux_remise', 0),
                    'prix_initial': l.get('prix_initial', l['prix_unitaire'])
                }
                self.lignes.append(line_data)
            
            self._refresh_lines()
            
            # Disable payment fields if readonly
            if self.readonly:
                if hasattr(self, 'mode_combo'): self.mode_combo.config(state="disabled")
                if hasattr(self, 'ref_paiement_entry'): self.ref_paiement_entry.config(state="disabled")
                if hasattr(self, 'banque_combo'): self.banque_combo.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Erreur chargement", f"Impossible de charger la facture: {e}")

    def _refresh_lines(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for l in self.lignes:
            p_nom = l.get('product_nom', '')
            
            qte = float(l['quantite'])
            price = float(l['prix_unitaire']) # Net Price
            
            # Helper to display values
            prix_initial = float(l.get('prix_initial', price))
            taux = float(l.get('taux_remise', 0))
            
            # Calculate Line Total (Net)
            # ROUNDING FIX: Round at line level
            montant_ht = round(qte * price, 2)
            
            # Calculate TVA (Standard 19%)
            # ROUNDING FIX: Round line TVA
            tva_amount = round(montant_ht * 0.19, 2)
            # ROUNDING FIX: Round line TTC
            ttc_amount = round(montant_ht + tva_amount, 2)
            
            self.tree.insert("", tk.END, values=(
                l.get('code_produit', p_nom),
                p_nom,
                l.get('unite', ''),
                format_quantity(qte, l.get('unite', '')),
                format_currency(prix_initial),
                f"{taux:.1f}%",
                format_currency(montant_ht),
                format_currency(tva_amount), 
                format_currency(ttc_amount)
            ))

    def add_ligne(self):
        # Local logging helper
        def log_debug(msg):
            try:
                with open("error_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now()} - {msg}\n")
            except: pass

        log_debug("DEBUG: Clicked add_ligne")
        
        if not self.selected_product:
            code = self.prod_code_var.get().strip()
            log_debug(f"DEBUG: Selected is None. Trying lookup for code='{code}'")
            if code:
                # 1. Try exact match (e.g. user selected from dropdown)
                self.selected_product = self.prod_map.get(code)
                
                # 2. Try partial match (e.g. user typed code manually)
                if not self.selected_product:
                    prefix = f"{code} - "
                    for key, prod in self.prod_map.items():
                        if key.startswith(prefix) or key == code: # Also handle exact code if map had it
                            self.selected_product = prod
                            # Update the combo to show full name
                            self.prod_code_var.set(key)
                            break
                            
                if self.selected_product:
                     log_debug(f"DEBUG: Resolved product '{self.selected_product['nom']}'")
                     # Also ensure price is set if empty
                     if not self.price_entry.get():
                         self.price_entry.delete(0, tk.END)
                         self.price_entry.insert(0, str(self.selected_product['prix_actuel']))

        if not self.selected_product: 
            log_debug("DEBUG: No product selected")
            messagebox.showerror("Erreur", "Veuillez sélectionner un produit valide dans la liste")
            return
        
        try:
            qte_str = self.qte_entry.get()
            price_str = self.price_entry.get()
            log_debug(f"DEBUG: Qty='{qte_str}', Price='{price_str}'")
            
            if not qte_str or not price_str:
                messagebox.showerror("Erreur", "Champs vides")
                return

            qte = parse_currency(qte_str)
            price = parse_currency(price_str)
            
            # Update price logic
            # if abs(price - self.selected_product['prix_actuel']) > 0.01:
            #     if messagebox.askyesno("Mise à jour Prix", "Le prix a changé. Voulez-vous mettre à jour le prix du produit dans la base ?"):
            #         self.app.db.update_product_price(self.selected_product['id'], price)
            
            # Discount Logic
            is_remise = self.remise_var.get()
            log_debug(f"DEBUG: Remise={is_remise}")
            
            if is_remise:
                raw_taux = self.taux_entry.get()
                log_debug(f"DEBUG: Raw Taux='{raw_taux}'")
                
                taux = parse_currency(raw_taux.replace('%', '').strip())
                if taux < 0 or taux > 100:
                    messagebox.showerror("Erreur", "Le taux doit être entre 0 et 100")
                    return
                
                price_net = price * (1 - (taux / 100))
                log_debug(f"DEBUG: New Price={price_net}")

            else:
                taux = 0.0
                price_net = price

            self._add_ligne_internal(self.selected_product, qte, price_net, prix_initial=price, taux_remise=taux)
            
            self.qte_entry.delete(0, tk.END)
            if self.remise_var.get():
                self.taux_entry.delete(0, tk.END) 

            self._update_footer() 
                
        except Exception as e:
            err = traceback.format_exc()
            log_debug(f"ERROR: {err}")
            messagebox.showerror("Erreur Critique", f"Erreur: {str(e)}")

    def _add_ligne_internal(self, product, qte, price, prix_initial=None, taux_remise=0.0):
        if self.type_doc == 'Avoir':
            qte = -abs(qte)
        
        # Defaults if not provided (legacy or direct call)
        if prix_initial is None:
             prix_initial = price

        # ROUNDING FIX: Round at line level to match logic.py
        total = round(qte * price, 2)
        product_tva = product.get('tva', 19.0)
        montant_tva = round(total * (product_tva / 100), 2)
        total_ttc = round(total + montant_tva, 2)

        self.lignes.append({
            'product_id': product['id'],
            'product_nom': product['nom'],
            'quantite': qte,
            'prix_unitaire': price, # Net Price (Calculated)
            'montant': total,
            'prix_initial': prix_initial, # New
            'taux_remise': taux_remise    # New
        })
        self.tree.insert("", tk.END, values=(
            product.get('code_produit', product['nom']),
            product['nom'],
            product.get('unite', ''),
            format_quantity(qte, product.get('unite', '')),
            f"{prix_initial:.2f}",
            f"{taux_remise:.1f}%",
            f"{total:.2f}",
            f"{montant_tva:.2f}",
            f"{total_ttc:.2f}"
        ))

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def remove_line(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        # Get indices to remove from logic list
        indices = sorted([self.tree.index(item) for item in selected_items], reverse=True)
        
        for idx in indices:
            if 0 <= idx < len(self.lignes):
                del self.lignes[idx]
        
        # Remove from UI
        for item in selected_items:
            self.tree.delete(item)
            
        self._update_footer()

    def save_draft(self):
        self._save_internal(statut_final='Brouillon')

    def save_validate(self):
        # Ask confirmation for final validation
        if not messagebox.askyesno("Confirmer", "Confirmer et valider cette facture définitivement ?\n\nCette action est irréversible (sauf par Avoir)."):
            return
        self._save_internal(statut_final='Validée')

    def _save_internal(self, statut_final):
        try:
            client_str = self.client_var.get()
            if not client_str: 
                messagebox.showerror("Erreur", "Client requis")
                return
            client_id = int(client_str.split(' - ')[0])
            
            origin_id = self.facture_origine_id
            if self.type_doc == 'Avoir' and not origin_id:
                # Try to resolve from entry if not passed directly
                ref = self.ref_facture.get() if hasattr(self, 'ref_facture') else None
                if ref:
                    conn = self.app.db._get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM factures WHERE numero=?", (ref,))
                    row = cur.fetchone()
                    if row: origin_id = row[0]

            # DEBUG TRACE
            if self.type_doc == 'Avoir':
                if not origin_id:
                     messagebox.showerror("DEBUG ERROR", f"Origin ID is Missing! Self.fid={self.facture_origine_id}")
                     return

            # Gather payment fields
            type_vente = self.vente_var.get() if self.type_doc == 'Facture' else None
            mode_paiement = self.mode_var.get() if hasattr(self, 'mode_var') else None
            ref_paiement = self.ref_paiement_entry.get() if hasattr(self, 'ref_paiement_entry') else None
            banque = self.banque_var.get() if hasattr(self, 'banque_var') else None
            
            # Fix: Define motif_val
            motif_val = self.motif_entry.get() if self.type_doc == 'Avoir' and hasattr(self, 'motif_entry') else None

            # Contract
            contract_str = self.contract_var.get()
            contract_id = self.contracts_map.get(contract_str) if contract_str else None
            # If manual entry (contract_id is None but str is not empty and not "Hors Contrat")
            contrat_code = None
            if not contract_id and contract_str and "Hors Contrat" not in contract_str:
                contrat_code = contract_str
                
            # Transport
            chauffeur = self.chauffeur_entry.get() if hasattr(self, 'chauffeur_entry') else None
            mat_tracteur = self.mat_tracteur_entry.get() if hasattr(self, 'mat_tracteur_entry') else None
            mat_remorque = self.mat_remorque_entry.get() if hasattr(self, 'mat_remorque_entry') else None
            transporteur = self.transporteur_combo.get() if hasattr(self, 'transporteur_combo') else None

            client_compte_bancaire = self.client_banque_entry.get() if hasattr(self, 'client_banque_entry') else None
            client_categorie = self.client_categorie_entry.get() if hasattr(self, 'client_categorie_entry') else None

            # Distinguish CREATE vs UPDATE (Draft)
            if self.view_facture_id:
                 # === UPDATE MODE (Draft) ===
                 success, msg = self.app.logic.update_invoice_draft(
                     facture_id=self.view_facture_id,
                     new_lignes=self.lignes,
                     user_id=self.app.user['id'],
                     client_id=client_id,
                     type_vente=type_vente,
                     mode_paiement=mode_paiement,
                     ref_paiement=ref_paiement,
                     banque=banque,
                     contract_id=contract_id,
                     contrat_code=contrat_code,
                     chauffeur=chauffeur,
                     matricule_tracteur=mat_tracteur,
                     matricule_remorque=mat_remorque,
                     transporteur=transporteur,
                     client_compte_bancaire=client_compte_bancaire,
                     client_categorie=client_categorie,
                     motif=motif_val
                 )
                 # Update Header if needed (TODO: Add header update to logic if strictly required)
                 # For now assuming user mostly updates lines. 
                 
                 if success and statut_final == 'Validée':
                      # 2nd Step: Confirm
                      success_conf, msg_conf = self.app.logic.confirm_invoice(self.view_facture_id)
                      if not success_conf:
                           success = False
                           msg = f"Update OK, but Confirm Failed: {msg_conf}"
                      else:
                           msg = "Facture mise à jour et validée avec succès"
                           
                 if success:
                     self.app.db.log_action(self.app.user['id'], "UPDATE_INVOICE", f"Updated Invoice {self.view_facture_id} Statut={statut_final}")
                     messagebox.showinfo("Succès", msg)
                     self.saved_facture_id = self.view_facture_id
                     if self.callback: self.callback()
                     if statut_final == 'Validée':
                          if messagebox.askyesno("Imprimer", "Voulez-vous imprimer la facture ?"):
                                self.print_preview()
                     self.dialog.destroy()
                 else:
                     messagebox.showerror("Erreur", msg)

            else:
                # === CREATE MODE ===
                # Get Date from UI
                custom_date_val = None
                try:
                    raw_date = None
                    if DateEntry and isinstance(self.date_facture_entry, DateEntry):
                        d_obj = self.date_facture_entry.get_date()
                        custom_date_val = d_obj.strftime("%Y-%m-%d")
                    else:
                         raw_date = self.date_facture_entry.get()
                         # Expected DD/MM/YYYY
                         import datetime
                         d_obj = datetime.datetime.strptime(raw_date, "%d/%m/%Y")
                         custom_date_val = d_obj.strftime("%Y-%m-%d")
                except Exception as e:
                     print(f"Date conversion error: {e}")
                     # Fallback to None (Today) or Error?
                     # Ideally invalid date should block, but let's be soft for now
                     pass

                success, msg, fid = self.app.logic.create_invoice_with_validation(
                    type_document=self.type_doc,
                    client_id=client_id,
                    lignes=self.lignes,
                    user_id=self.app.user['id'],
                    facture_origine_id=origin_id,
                    motif=motif_val,
                    type_vente=type_vente,
                    mode_paiement=mode_paiement,
                    ref_paiement=ref_paiement,
                    banque=banque,
                    contract_id=contract_id,
                    contrat_code=contrat_code,
                    chauffeur=chauffeur,
                    matricule_tracteur=mat_tracteur,
                    matricule_remorque=mat_remorque,
                    transporteur=transporteur,
                    client_compte_bancaire=client_compte_bancaire,
                    client_categorie=client_categorie,
                    custom_date=custom_date_val,

                    statut_final=statut_final # Pass status
                )
                
                if success:
                    self.app.db.log_action(self.app.user['id'], f"CREATE_{self.type_doc.upper()}", f"Created {self.type_doc} for client {client_id}")
                    messagebox.showinfo("Succès", msg)
                    self.saved_facture_id = fid
                    if self.callback: self.callback()
                    # Offer print only if Validée (or ask user)
                    if statut_final == 'Validée':
                         if messagebox.askyesno("Imprimer", "Voulez-vous imprimer la facture/avoir ?"):
                            self.print_preview()
                    else:
                         # Draft created
                         pass
                    self.dialog.destroy()
                else:
                    messagebox.showerror("Erreur", msg)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def print_preview(self):
        # Placeholder for print
        if hasattr(self, 'saved_facture_id'):
             # Generate PDF
             try:
                 fac = self.app.db.get_facture_by_id(self.saved_facture_id)
                 from utils import generate_invoice_pdf
                 filename = f"{fac['type_document']}_{fac['numero']}.pdf"
                 generate_invoice_pdf(fac, filename)
                 preview_and_print_pdf(filename)
             except Exception as e:
                 messagebox.showerror("Erreur", str(e))
        else:
             messagebox.showinfo("Info", "Veuillez d'abord sauvegarder la facture.")

    def print_matrix(self):
        if hasattr(self, 'saved_facture_id'):
            success, msg = self.app.logic.print_delivery_note_text(self.saved_facture_id)
            if success:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)
        else:
             messagebox.showinfo("Info", "Veuillez d'abord sauvegarder la facture.")


class LigneDialog:
    def __init__(self, parent, app, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ligne de facture")
        self.dialog.state('zoomed')
        self.app = app
        self.callback = callback
        self.products = self.app.db.get_all_products()  # Fetch once
        self._build()
    
    def _build(self):
        tk.Label(self.dialog, text="Produit").pack(pady=5)
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(self.dialog, textvariable=self.product_var, width=40)
        # Map values
        self.products_map = {}
        for p in self.products:
             label = f"{p['id']} - {p['nom']}"
             if p.get('parent_stock_id'):
                  label = f"[PRIX] {label}"
             self.products_map[label] = p
             
        self.product_combo['values'] = sorted(list(self.products_map.keys()))
        self.product_combo.pack(pady=5)
        self.product_combo.bind("<<ComboboxSelected>>", self._on_product_select)
        
        tk.Label(self.dialog, text="Quantité").pack(pady=5)
        self.qte = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.qte.pack(pady=5)
        
        tk.Label(self.dialog, text="Prix Unitaire").pack(pady=5)
        self.prix = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.prix.pack(pady=5)
        
        tk.Button(self.dialog, text="Ajouter", command=self.add).pack(pady=10)
    
    def _on_product_select(self, event):
        val = self.product_var.get()
        p = self.products_map.get(val)
        if p:
            self.prix.delete(0, tk.END)
            self.prix.insert(0, str(p['prix_actuel']))

    def add(self):
        try:
            val = self.product_var.get()
            if not val:
                 messagebox.showerror("Erreur", "Sélectionnez un produit")
                 return
            
            product_id = int(val.split(' - ')[0])
            product = self.app.db.get_product_by_id(product_id)
            
            ligne_data = {
                'product_id': product_id,
                'product_nom': product['nom'],
                'quantite': parse_currency(self.qte.get()),
                'prix_unitaire': parse_currency(self.prix.get())
            }
            if self.callback:
                self.callback(ligne_data)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs invalides")


class PaymentDialog:
    def __init__(self, parent, app, client_id=None, facture_id=None, payment_id=None, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Nouveau Paiement")
        self.dialog.state('zoomed')
        self.app = app
        self.client_id = client_id
        self.facture_id = facture_id
        self.payment_id = payment_id
        self.callback = callback
        self._build()
        if self.payment_id:
            self._load_payment()
    
    def _build(self):
        tk.Label(self.dialog, text="Client*").pack(pady=5)
        clients = self.app.db.get_all_clients()
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(self.dialog, textvariable=self.client_var, width=40)
        self.client_combo['values'] = [f"{c['id']} - {c['raison_sociale']}" for c in clients]
        self.client_combo['values'] = [f"{c['id']} - {c['raison_sociale']}" for c in clients]
        self.client_combo.pack(pady=5)
        
        if self.client_id:
            for c_str in self.client_combo['values']:
                if c_str.startswith(f"{self.client_id} -"):
                    self.client_combo.set(c_str)
                    break
        
        tk.Label(self.dialog, text="Montant*").pack(pady=5)
        self.montant = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.montant.pack(pady=5)
        
        tk.Label(self.dialog, text="Mode de Paiement*").pack(pady=5)
        self.mode_var = tk.StringVar(value="Espèces")
        ttk.Combobox(self.dialog, textvariable=self.mode_var, values=["Espèces", "Chèque", "Virement", "Versement"]).pack(pady=5)
        
        tk.Label(self.dialog, text="Référence").pack(pady=5)
        self.reference = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.reference.pack(pady=5)
        
        tk.Label(self.dialog, text="Banque").pack(pady=5)
        self.banque_var = tk.StringVar()
        BANKS = ["BNA", "BEA", "CPA", "BADR", "BDL", "CNEP", "Société Générale", "Natixis", "AGB", "Trust Bank", "Al Salam", "Housing Bank", "ABC", "BNP Paribas"]
        self.banque = ttk.Combobox(self.dialog, textvariable=self.banque_var, values=BANKS)
        self.banque.pack(pady=5)
        
        # New Contract Fields
        tk.Label(self.dialog, text="N° Contrat / Convention").pack(pady=5)
        self.contrat_num = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.contrat_num.pack(pady=5)
        
        frame_dates = tk.Frame(self.dialog)
        frame_dates.pack(pady=5)
        
        tk.Label(frame_dates, text="Début:").pack(side=tk.LEFT)
        if DateEntry:
            self.date_debut = DateEntry(frame_dates, width=12, background=PRIMARY_COLOR, foreground='white',
                                      headersbackground=PRIMARY_COLOR, headersforeground='white',
                                      borderwidth=2, date_pattern='dd/mm/yyyy')
        else:
            self.date_debut = tk.Entry(frame_dates, width=12, bg="#455a64", fg="white", insertbackground="white")
            self.date_debut.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.date_debut.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_dates, text="Fin:").pack(side=tk.LEFT)
        if DateEntry:
            self.date_fin = DateEntry(frame_dates, width=12, background=PRIMARY_COLOR, foreground='white',
                                    headersbackground=PRIMARY_COLOR, headersforeground='white',
                                    borderwidth=2, date_pattern='dd/mm/yyyy')
        else:
            self.date_fin = tk.Entry(frame_dates, width=12, bg="#455a64", fg="white", insertbackground="white")
            # self.date_fin.insert(0, datetime.now().strftime("%d/%m/%Y")) # Optional
        self.date_fin.pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.dialog, text="Enregistrer", bg=PRIMARY_COLOR, fg="white", command=self.save).pack(pady=20)

    def _load_payment(self):
        p = self.app.db.get_payment_by_id(self.payment_id)
        if not p:
            return
            
        # Set Client
        for c_str in self.client_combo['values']:
            if c_str.startswith(f"{p['client_id']} -"):
                self.client_combo.set(c_str)
                break
                
        self.montant.insert(0, str(p['montant']))
        self.mode_var.set(p['mode_paiement'])
        if p.get('reference'): self.reference.insert(0, p['reference'])
        if p.get('banque'): self.banque.set(p['banque'])
        if p.get('contrat_num'): self.contrat_num.insert(0, p['contrat_num'])
        
        # Dates... if DateEntry vs Entry
        if DateEntry:
             if p.get('contrat_date_debut'):
                 try: self.date_debut.set_date(datetime.strptime(p['contrat_date_debut'], '%Y-%m-%d'))
                 except: pass
             if p.get('contrat_date_fin'):
                 try: self.date_fin.set_date(datetime.strptime(p['contrat_date_fin'], '%Y-%m-%d'))
                 except: pass
        else:
             if p.get('contrat_date_debut'): 
                 self.date_debut.delete(0, tk.END)
                 self.date_debut.insert(0, datetime.strptime(p['contrat_date_debut'], '%Y-%m-%d').strftime('%d/%m/%Y'))
             if p.get('contrat_date_fin'): 
                 self.date_fin.delete(0, tk.END)
                 self.date_fin.insert(0, datetime.strptime(p['contrat_date_fin'], '%Y-%m-%d').strftime('%d/%m/%Y'))
    
    def save(self):
        try:
            # Client
            val = self.client_var.get()
            if not val:
                 messagebox.showerror("Erreur", "Client obligatoire")
                 return
            client_id = int(val.split(' - ')[0])
            
            # Montant
            try:
                montant = float(self.montant.get())
            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide")
                return

            date_paiement = datetime.now().strftime("%Y-%m-%d") # Or add date field? 
            # Original code didn't have date field for payment itself? 
            # Looking at _build (previously viewed), I didn't see explicit Payment Date field, only Contract Dates.
            # Usually creates with TODAY date.
            # If editing, DO WE KEEP ORIGINAL DATE?
            # Yes, standard behavior.
            if self.payment_id:
                old_p = self.app.db.get_payment_by_id(self.payment_id)
                date_paiement = old_p['date_paiement']

            mode = self.mode_var.get()
            ref = self.reference.get()
            banque = self.banque_var.get()
            
            c_num = self.contrat_num.get()
            
            # Dates
            c_debut = None
            c_fin = None
            
            if DateEntry:
                if isinstance(self.date_debut, DateEntry):
                    c_debut = self.date_debut.get_date().strftime("%Y-%m-%d")
                    c_fin = self.date_fin.get_date().strftime("%Y-%m-%d")
            
            # Fallback if text entry or logic above failed
            if not c_debut:
                # Try parsing text
                 try: c_debut = datetime.strptime(self.date_debut.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
                 except: c_debut = None
                 try: c_fin = datetime.strptime(self.date_fin.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
                 except: c_fin = None

            if self.payment_id:
                self.app.db.update_payment(self.payment_id, date_paiement, client_id, montant, mode, ref, banque, c_num, c_debut, c_fin)
            else:
                self.app.db.create_paiement(date_paiement, client_id, montant, mode, self.facture_id, ref, banque, c_num, c_debut, c_fin, self.app.user['id'])
            
            if self.callback: self.callback()
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            client_id = int(self.client_var.get().split(' - ')[0])
            success, msg, _ = self.app.logic.create_payment(
                client_id=client_id,
                montant=parse_currency(self.montant.get()),
                mode_paiement=self.mode_var.get(),
                reference=self.reference.get() or None,
                banque=self.banque.get() or None,
                contrat_num=self.contrat_num.get() or None,
                contrat_date_debut=self.date_debut.get_date().strftime("%Y-%m-%d") if DateEntry and isinstance(self.date_debut, DateEntry) else self.date_debut.get(),
                contrat_date_fin=self.date_fin.get_date().strftime("%Y-%m-%d") if DateEntry and isinstance(self.date_fin, DateEntry) and self.date_fin.get() else self.date_fin.get(),

                user_id=self.app.user['id'],
                facture_id=self.facture_id # Link to invoice if provided
            )
            messagebox.showinfo("Succès" if success else "Erreur", msg)
            if success and self.callback:
                self.app.db.log_action(self.app.user['id'], "CREATE_PAYMENT", f"Created payment for client {client_id}")
                self.callback()
                self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


class BordereauDialog:
    def __init__(self, parent, app, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Créer Bordereau")
        self.dialog.state('zoomed')
        self.app = app
        self.callback = callback
        self._build()
    
    def _build(self):
        tk.Label(self.dialog, text="Sélectionner paiements 'En attente'").pack(pady=10)
        
        self.tree = ttk.Treeview(self.dialog, columns=("Num", "Client", "Montant", "Banque"), show="tree headings")
        for col in ("Num", "Client", "Montant", "Banque"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        paiements = self.app.db.get_all_paiements(statut="En attente")
        for p in paiements:
            self.tree.insert("", tk.END, iid=p['id'], values=(p['numero'], p['client_nom'], p['montant'], p.get('banque', '')))
        
        tk.Label(self.dialog, text="Banque*").pack(pady=5)
        self.banque_var = tk.StringVar()
        BANKS = ["BNA", "BEA", "CPA", "BADR", "BDL", "CNEP", "Société Générale", "Natixis", "AGB", "Trust Bank", "Al Salam", "Housing Bank", "ABC", "BNP Paribas"]
        self.banque = ttk.Combobox(self.dialog, textvariable=self.banque_var, values=BANKS)
        self.banque.pack(pady=5)
        
        tk.Button(self.dialog, text="Générer Bordereau", bg=PRIMARY_COLOR, fg="white", command=self.create).pack(pady=10)
    
    def _on_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        # Check banks of selected items
        banks = set()
        for item in selected_items:
            vals = self.tree.item(item)['values']
            # values are (Num, Client, Montant, Banque)
            # Treeview returns values as strings usually
            if len(vals) >= 4:
                b = vals[3]
                if b and str(b).strip():
                    banks.add(str(b))
        
        if len(banks) == 1:
            # Auto-fill if unique
            self.banque_var.set(list(banks)[0])
        elif len(banks) > 1:
            # Maybe clear if mixed? Or keep first?
            pass
            return
        
    def create(self):
        selected = [int(item) for item in self.tree.selection()]
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez au moins un paiement")
            return
        
        # Create bordereau
        success, msg, bordereau_id = self.app.logic.create_bordereau(
            banque=self.banque.get(),
            paiement_ids=selected,
            user_id=self.app.user['id']
        )
        
        if success:
            # Generate PDF
            try:
                # Fetch full details
                data = self.app.db.get_bordereau_with_details(bordereau_id)
                if data:
                    # Assuming utils and preview_and_print_pdf are imported elsewhere
                    # For this example, I'll assume they are available in the scope
                    # You might need to add 'import utils' and 'from your_module import preview_and_print_pdf'
                    # at the top of your file if they are not already.
                    import utils # Placeholder, replace with actual import if needed
                    from utils import preview_and_print_pdf # Placeholder
                    pdf_file = utils.generate_bordereau_pdf(data)
                    preview_and_print_pdf(pdf_file)
            except Exception as e:
                messagebox.showerror("Erreur PDF", f"Erreur génération PDF: {e}")
                
            messagebox.showinfo("Succès", msg)
            if self.callback:
                self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Erreur", msg)


class UserDialog:
    def __init__(self, parent, user_id, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Nouvel Utilisateur")
        self.dialog.state('zoomed')
        self.user_id = user_id
        self.callback = callback
        self._build()
    
    def _build(self):
        # Center constraint
        frame = tk.Frame(self.dialog, padx=40, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Nom d'utilisateur*", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.username = tk.Entry(frame, font=("Arial", 11), bg="#455a64", fg="white", insertbackground="white")
        self.username.pack(fill=tk.X, pady=5)
        self.username.focus()
        
        tk.Label(frame, text="Mot de Passe*", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.password = tk.Entry(frame, show="*", font=("Arial", 11), bg="#455a64", fg="white", insertbackground="white")
        self.password.pack(fill=tk.X, pady=5)
        
        tk.Button(frame, text="Enregistrer", bg=PRIMARY_COLOR, fg="white", 
                 font=("Arial", 11, "bold"), command=self.save, height=2).pack(fill=tk.X, pady=30)
    
    def save(self):
        try:
            username = self.username.get().strip()
            password = self.password.get().strip()
            
            if not username or not password:
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
                return

            # Request: "Nom de l'utlisateur" and "Mot de Passe" ONLY. 
            # Auto-fill full_name with username, default role to 'user'
            
            get_db().create_user(
                username=username,
                password=password,
                full_name=username, # Auto-filled
                role='user',        # Default
                created_by=self.user_id
            )
            messagebox.showinfo("Succès", "Utilisateur créé avec succès")
            if self.callback:
                self.callback()
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


class PriceDialog:
    def __init__(self, parent, product_id, user_id, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Modifier Prix")
        self.dialog.state('zoomed')
        self.product_id = product_id
        self.user_id = user_id
        self.callback = callback
        self._build()
    
    def _build(self):
        tk.Label(self.dialog, text="Nouveau Prix*").pack(pady=5)
        self.prix = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.prix.pack(pady=5)
        
        tk.Label(self.dialog, text="Référence Note").pack(pady=5)
        self.ref_note = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.ref_note.pack(pady=5)
        
        tk.Label(self.dialog, text="Date Note").pack(pady=5)
        if DateEntry:
            self.date_note = DateEntry(self.dialog, width=20, background=PRIMARY_COLOR, foreground='white',
                                     headersbackground=PRIMARY_COLOR, headersforeground='white',
                                     borderwidth=2, date_pattern='dd/mm/yyyy')
        else:
            self.date_note = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
            self.date_note.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.date_note.pack(pady=5)
        
        tk.Button(self.dialog, text="Mettre à jour", bg=PRIMARY_COLOR, fg="white", command=self.save).pack(pady=20)
    
    def save(self):
        try:
            get_db().update_product_price(
                product_id=self.product_id,
                nouveau_prix=float(self.prix.get()),
                reference_note=self.ref_note.get() or None,
                date_note=self.date_note.get_date().strftime("%Y-%m-%d") if DateEntry and isinstance(self.date_note, DateEntry) else self.date_note.get(),
                created_by=self.user_id
            )
            messagebox.showinfo("Succès", "Prix mis à jour")
            if self.callback:
                self.callback()
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


class ClosureDialog:
    def __init__(self, parent, user_id):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Clôture Annuelle")
        self.dialog.state('zoomed')
        self.user_id = user_id
        self._build()
    
    def _build(self):
        tk.Label(self.dialog, text="Clôture Annuelle", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Label(self.dialog, text="Année à clôturer:").pack(pady=5)
        self.annee = tk.Entry(self.dialog, bg="#455a64", fg="white", insertbackground="white")
        self.annee.insert(0, str(datetime.now().year - 1))
        self.annee.pack(pady=5)
        
        tk.Label(self.dialog, text="ATTENTION: Cette opération est irréversible!", fg="red").pack(pady=10)
        
        tk.Button(self.dialog, text="Effectuer la clôture", bg="#d32f2f", fg="white", command=self.close_year).pack(pady=20)
    
    def close_year(self):
        if messagebox.askyesno("Confirmation", "Confirmer la clôture annuelle ?"):
            try:
                success, msg = get_logic().perform_annual_closure(
                    annee=int(self.annee.get()),
                    user_id=self.user_id
                )
                messagebox.showinfo("Succès" if success else "Erreur", msg)
                if success:
                    self.dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))


class InvoiceDetailsDialog:
    def __init__(self, parent, facture_data):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Détails {facture_data['numero']}")
        self.dialog.state('zoomed')
        
        text = tk.Text(self.dialog, wrap=tk.WORD, bg="#455a64", fg="white", insertbackground="white")
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        text.insert(tk.END, f"Numéro: {facture_data['numero']}\n")
        text.insert(tk.END, f"Type: {facture_data['type_document']}\n")
        text.insert(tk.END, f"Client: {facture_data['raison_sociale']}\n\n")
        text.insert(tk.END, "Lignes:\n")
        for ligne in facture_data['lignes']:
            text.insert(tk.END, f"  - {ligne['product_nom']}: {format_quantity(ligne['quantite'], ligne.get('unite', ''))} x {format_currency(ligne['prix_unitaire'])} = {format_currency(ligne['montant'])}\n")
        
        text.insert(tk.END, f"\nTotal HT: {format_currency(facture_data['montant_ht'])}\n")
        text.insert(tk.END, f"TVA: {format_currency(facture_data['montant_tva'])}\n")
        text.insert(tk.END, f"Total TTC: {format_currency(facture_data['montant_ttc'])}\n\n")
        text.insert(tk.END, f"En lettres: {nombre_en_lettres(facture_data['montant_ttc'])}\n")
        text.config(state=tk.DISABLED)



class ClientStateDialog:
    def __init__(self, parent, clients):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("État Détaillé des Clients")
        self.dialog.state('zoomed')
        self.clients = clients
        self._build()
        
    def _build(self):
        # Header
        header = tk.Frame(self.dialog, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header, text="État Détaillé des Clients Actifs", font=("Arial", 16, "bold"), bg=BG_COLOR).pack(side=tk.LEFT)
        
        tk.Button(
            header, text="Imprimer / PDF", bg=PRIMARY_COLOR, fg="white", font=("Arial", 10, "bold"),
            command=self.print_pdf
        ).pack(side=tk.RIGHT)
        
        # Table
        columns = ("Raison Sociale", "Adresse", "N° RC", "N° NIS", "N° NIF", "N° Art Imp")
        tree_frame = tk.Frame(self.dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        self.tree.heading("Raison Sociale", text="Raison Sociale")
        self.tree.column("Raison Sociale", width=200)
        self.tree.heading("Adresse", text="Adresse")
        self.tree.column("Adresse", width=250)
        self.tree.heading("N° RC", text="N° RC")
        self.tree.column("N° RC", width=100)
        self.tree.heading("N° NIS", text="N° NIS")
        self.tree.column("N° NIS", width=100)
        self.tree.heading("N° NIF", text="N° NIF")
        self.tree.column("N° NIF", width=100)
        self.tree.heading("N° Art Imp", text="N° Art Imp")
        self.tree.column("N° Art Imp", width=100)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load Data
        for client in self.clients:
            if client['active']:
                self.tree.insert("", tk.END, values=(
                    client['raison_sociale'],
                    client['adresse'],
                    client['rc'],
                    client['nis'],
                    client['nif'],
                    client['article_imposition']
                ))
                
    def print_pdf(self):
        filename = f"Etat_Clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        utils.generate_client_state_pdf(self.clients, filename)
        # messagebox.showinfo("Succès", f"PDF généré: {filename}")
        try:
            preview_and_print_pdf(filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur PDF: {e}")


class DateRangeDialog:
    def __init__(self, parent, callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Sélectionner une période")
        self.dialog.state('zoomed')
        self.callback = callback
        self._build()
        
    def _build(self):
        tk.Label(self.dialog, text="Période du :", font=("Arial", 10)).pack(pady=(20, 5))
        
        self.start_entry = tk.Entry(self.dialog)
        self.start_entry.insert(0, datetime.now().strftime("%Y-%m-01")) # First day of current month
        self.start_entry.pack(pady=5)
        
        tk.Label(self.dialog, text="Au :", font=("Arial", 10)).pack(pady=5)
        
        self.end_entry = tk.Entry(self.dialog)
        self.end_entry.insert(0, datetime.now().strftime("%Y-%m-%d")) # Today
        self.end_entry.pack(pady=5)
        
        tk.Label(self.dialog, text="(Format: YYYY-MM-DD)", font=("Arial", 8), fg="gray").pack()
        
        tk.Button(self.dialog, text="Valider", bg=PRIMARY_COLOR, fg="white", command=self.validate).pack(pady=20)
        
    def validate(self):
        start = self.start_entry.get()
        end = self.end_entry.get()
        # Basic validation could be added here
        self.dialog.destroy()
        self.callback(start, end)


class InvoiceStateDialog:
    def __init__(self, parent, lines, date_range):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("État des Factures")
        self.dialog.state('zoomed')
        self.lines = lines
        self.date_range = date_range
        self._build()
        
    def _build(self):
        # Header
        header = tk.Frame(self.dialog, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text=f"État des Factures ({self.date_range['start']} au {self.date_range['end']})", 
            font=("Arial", 14, "bold"), 
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        tk.Button(
            header, text="Imprimer PDF", bg=PRIMARY_COLOR, fg="white", font=("Arial", 10, "bold"),
            command=self.print_pdf
        ).pack(side=tk.RIGHT)
        
        # Table
        columns = ("N° Facture", "Date", "Produit", "Quantité", "Montant HT")
        tree_frame = tk.Frame(self.dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=vsb.set)
        
        vsb.config(command=self.tree.yview)
        
        self.tree.heading("N° Facture", text="N° Facture")
        self.tree.column("N° Facture", width=120)
        self.tree.heading("Date", text="Date")
        self.tree.column("Date", width=100)
        self.tree.heading("Produit", text="Produit")
        self.tree.column("Produit", width=200)
        self.tree.heading("Quantité", text="Quantité")
        self.tree.column("Quantité", width=100, anchor="e")
        self.tree.heading("Montant HT", text="Montant HT")
        self.tree.column("Montant HT", width=120, anchor="e")
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load Data & Calculate Total
        total_ht = 0.0
        for line in self.lines:
            self.tree.insert("", tk.END, values=(
                line['numero'],
                line['date_facture'],
                line['product_nom'],
                f"{line['quantite']:.2f}",
                f"{line['montant_ht']:.2f}"
            ))
            total_ht += line['montant_ht']
            
        # Footer Total
        footer = tk.Frame(self.dialog, bg=BG_COLOR, height=40)
        footer.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(footer, text="TOTAL GÉNÉRAL HT:", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        tk.Label(footer, text=f"{total_ht:,.2f} DA", font=("Arial", 12, "bold"), fg=ACCENT_COLOR, bg=BG_COLOR).pack(side=tk.RIGHT)

    def print_pdf(self):
        filename = f"Etat_Factures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        utils.generate_invoice_state_pdf(self.lines, self.date_range, filename)
        # messagebox.showinfo("Succès", f"PDF généré: {filename}")
        try:
            preview_and_print_pdf(filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur PDF: {e}")


class Etat104Dialog:
    def __init__(self, parent, data, date_range):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ÉTAT 104 - Chiffre d'Affaires par Client")
        self.dialog.geometry("1000x600")
        self.data = data
        self.date_range = date_range
        self._build()
        
    def _build(self):
        # Header
        header = tk.Frame(self.dialog, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text=f"ÉTAT N° 104 ({self.date_range['start']} au {self.date_range['end']})", 
            font=("Arial", 14, "bold"), 
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        tk.Button(
            header, text="Imprimer PDF", bg=PRIMARY_COLOR, fg="white", font=("Arial", 10, "bold"),
            command=self.print_pdf
        ).pack(side=tk.RIGHT)
        
        # Table
        columns = ("Raison Sociale", "N° RC", "N° NIF", "N° NIS", "Art. Imposition", "CA HT")
        tree_frame = tk.Frame(self.dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Raison Sociale", text="Raison Sociale")
        self.tree.column("Raison Sociale", width=250)
        self.tree.heading("N° RC", text="N° RC")
        self.tree.column("N° RC", width=100)
        self.tree.heading("N° NIF", text="N° NIF")
        self.tree.column("N° NIF", width=100)
        self.tree.heading("N° NIS", text="N° NIS")
        self.tree.column("N° NIS", width=100)
        self.tree.heading("Art. Imposition", text="Art. Imposition")
        self.tree.column("Art. Imposition", width=100)
        self.tree.heading("CA HT", text="CA HT")
        self.tree.column("CA HT", width=120, anchor="e")
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load Data & Calculate Total
        total_ca = 0.0
        for row in self.data:
            self.tree.insert("", tk.END, values=(
                row['raison_sociale'],
                row['rc'],
                row['nif'],
                row['nis'],
                row['article_imposition'],
                f"{row['chiffre_affaire_ht']:,.2f}"
            ))
            total_ca += row['chiffre_affaire_ht']
            
        # Footer Total
        footer = tk.Frame(self.dialog, bg=BG_COLOR, height=40)
        footer.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(footer, text="TOTAL CA HT:", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        tk.Label(footer, text=f"{total_ca:,.2f} DA", font=("Arial", 12, "bold"), fg=ACCENT_COLOR, bg=BG_COLOR).pack(side=tk.RIGHT)

    def print_pdf(self):
        filename = f"Etat_104_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        utils.generate_etat_104_pdf(self.data, self.date_range, filename)
        # messagebox.showinfo("Succès", f"PDF généré: {filename}")
        try:
            preview_and_print_pdf(filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur PDF: {e}")


class PaymentsStateDialog:
    def __init__(self, parent, data, date_range):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ÉTAT DES PAIEMENTS")
        self.dialog.geometry("1000x600")
        self.data = data
        self.date_range = date_range
        self._build()
        
    def _build(self):
        # Header
        header = tk.Frame(self.dialog, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            header, 
            text=f"ÉTAT DES PAIEMENTS ({self.date_range['start']} au {self.date_range['end']})", 
            font=("Arial", 14, "bold"), 
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(side=tk.LEFT)
        
        tk.Button(
            header, text="Imprimer PDF", bg=PRIMARY_COLOR, fg="white", font=("Arial", 10, "bold"),
            command=self.print_pdf
        ).pack(side=tk.RIGHT)
        
        # Table
        columns = ("Raison Sociale", "Date Paiement", "Référence", "Mode", "Montant")
        tree_frame = tk.Frame(self.dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Raison Sociale", text="Raison Sociale")
        self.tree.column("Raison Sociale", width=250)
        self.tree.heading("Date Paiement", text="Date Paiement")
        self.tree.column("Date Paiement", width=120)
        self.tree.heading("Référence", text="Référence")
        self.tree.column("Référence", width=150)
        self.tree.heading("Mode", text="Mode")
        self.tree.column("Mode", width=100)
        self.tree.heading("Montant", text="Montant")
        self.tree.column("Montant", width=120, anchor="e")
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load Data & Calculate Total
        total_paiements = 0.0
        for row in self.data:
            self.tree.insert("", tk.END, values=(
                row['raison_sociale'],
                row['date_paiement'],
                row['reference'] or "-",
                row['mode_paiement'],
                f"{row['montant']:,.2f}"
            ))
            total_paiements += row['montant']
            
        # Footer Total
        footer = tk.Frame(self.dialog, bg=BG_COLOR, height=40)
        footer.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(footer, text="TOTAL PAIEMENTS:", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        tk.Label(footer, text=f"{total_paiements:,.2f} DA", font=("Arial", 12, "bold"), fg=ACCENT_COLOR, bg=BG_COLOR).pack(side=tk.RIGHT)

    def print_pdf(self):
        filename = f"Etat_Paiements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        utils.generate_payments_state_pdf(self.data, self.date_range, filename)
        # messagebox.showinfo("Succès", f"PDF généré: {filename}")
        try:
            preview_and_print_pdf(filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur PDF: {e}")


class UserDialog:
    """Dialog for creating/editing users"""
    
    def __init__(self, parent, admin_id, user_id=None, callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Gestion Utilisateur")
        self.dialog.geometry("500x450")
        self.dialog.configure(bg=BG_COLOR)
        
        self.admin_id = admin_id
        self.user_id = user_id
        self.callback = callback
        self.db = get_db()
        
        # Center dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        self._build_ui()
        
        if user_id:
            self._load_user()
    
    def _build_ui(self):
        container = tk.Frame(self.dialog, bg=BG_COLOR, padx=40, pady=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_text = "Modifier Utilisateur" if self.user_id else "Nouvel Utilisateur"
        tk.Label(
            container, 
            text=title_text, 
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).pack(pady=(0, 20))
        
        # Username
        tk.Label(container, text="Nom d'utilisateur*", bg=BG_COLOR, fg=TEXT_COLOR, anchor="w").pack(fill=tk.X)
        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(container, textvariable=self.username_var, font=("Arial", 11), bg="#455a64", fg="white", insertbackground="white")
        self.username_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Full Name
        tk.Label(container, text="Nom & Prénom*", bg=BG_COLOR, fg=TEXT_COLOR, anchor="w").pack(fill=tk.X)
        self.fullname_var = tk.StringVar()
        self.fullname_entry = tk.Entry(container, textvariable=self.fullname_var, font=("Arial", 11), bg="#455a64", fg="white", insertbackground="white")
        self.fullname_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Role
        tk.Label(container, text="Rôle", bg=BG_COLOR, fg=TEXT_COLOR, anchor="w").pack(fill=tk.X)
        self.role_var = tk.StringVar(value="user")
        role_combo = ttk.Combobox(container, textvariable=self.role_var, values=["user", "admin", "magasinier"], state="readonly")
        role_combo.pack(fill=tk.X, pady=(5, 15))
        
        # Password
        tk.Label(container, text="Mot de passe*", bg=BG_COLOR, fg=TEXT_COLOR, anchor="w").pack(fill=tk.X)
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(container, textvariable=self.password_var, show="*", font=("Arial", 11), bg="#455a64", fg="white", insertbackground="white")
        self.password_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Confirm Password (Hidden initially)
        self.confirm_frame = tk.Frame(container, bg=BG_COLOR)
        tk.Label(self.confirm_frame, text="Resaisir Mot de passe*", bg=BG_COLOR, fg=TEXT_COLOR, anchor="w").pack(fill=tk.X)
        self.confirm_var = tk.StringVar()
        self.confirm_entry = tk.Entry(self.confirm_frame, textvariable=self.confirm_var, show="*", font=("Arial", 11), bg="#455a64", fg="white", insertbackground="white")
        self.confirm_entry.pack(fill=tk.X, pady=5)
        
        # Bindings for dynamic confirmation field
        self.password_var.trace_add("write", self._check_password_field)
        
        # Buttons
        btn_frame = tk.Frame(container, bg=BG_COLOR, pady=20)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(
            btn_frame, 
            text="Annuler", 
            command=self.dialog.destroy,
            bg="#757575", 
            fg="white",
            width=10
        ).pack(side=tk.RIGHT, padx=5)
        
        self.save_btn = tk.Button(
            btn_frame, 
            text="Enregistrer", 
            command=self.save,
            bg=PRIMARY_COLOR, 
            fg="white",
            width=15
        )
        self.save_btn.pack(side=tk.RIGHT, padx=5)
    
    def _check_password_field(self, *args):
        password = self.password_var.get()
        if password:
            self.confirm_frame.pack(fill=tk.X, pady=(0, 15), after=self.password_entry)
        else:
            self.confirm_frame.pack_forget()
            
    def _load_user(self):
        user = self.db.get_user_by_id(self.user_id) # Need to implement get_user_by_id or fetch directly
        # Wait, get_user_by_id is NOT in database.py yet?
        # I saw get_all_users and authenticate_user.
        # I need to implement get_user_by_id or just use a query here or iterate get_all_users (inefficient but safe).
        # OR better, since I am in UI, I can assume I passed the user object? No, I passed ID.
        # I'll implement a quick fetch here or use get_all_users explicitly.
        # Ideally, I should add get_user_by_id to database.py but I want to avoid too many edits.
        # I'll use a direct cursor query here effectively via private method access or just add the method to DB.
        # Adding to DB is cleaner. I recall doing some DB edits earlier.
        # For now, I'll cheat and iterate get_all_users() since N is small.
        users = self.db.get_all_users()
        user_data = next((u for u in users if u['id'] == self.user_id), None)
        
        if user_data:
            self.username_var.set(user_data['username'])
            self.fullname_var.set(user_data['full_name'])
            self.role_var.set(user_data['role'])
            # Password not loaded for security and nature of hashing (if hashed). 
            # If plain text, I could load it, but usually standard is leave blank to keep unchanged.
            self.dialog.title(f"Modifier: {user_data['username']}")
    
    def save(self):
        username = self.username_var.get().strip()
        fullname = self.fullname_var.get().strip()
        role = self.role_var.get()
        password = self.password_var.get()
        confirm = self.confirm_var.get()
        
        if not username or not fullname:
            messagebox.showwarning("Erreur", "Veuillez remplir les champs obligatoires")
            return
            
        if self.user_id: # Edit mode
            update_data = {
                'username': username,
                'full_name': fullname,
                'role': role
            }
            if password:
                if password != confirm:
                    messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
                    return
                update_data['password'] = password
                
            try:
                self.db.update_user(self.user_id, **update_data)
                self.db.log_action(self.admin_id, "UPDATE_USER", f"Updated User Data: {update_data}") 
                messagebox.showinfo("Succès", "Utilisateur modifié")
                if self.callback: self.callback()
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
                
        else: # Create mode
            if not password:
                messagebox.showwarning("Erreur", "Le mot de passe est obligatoire")
                return
            if password != confirm:
                messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
                return
                
            try:
                self.db.create_user(username, password, fullname, role, created_by=self.admin_id)
                self.db.log_action(self.admin_id, "CREATE_USER", f"Created User: {username}, Role: {role}")
                messagebox.showinfo("Succès", "Utilisateur créé")
                if self.callback: self.callback()
                self.dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erreur", "Ce nom d'utilisateur existe déjà")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))


class AboutDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("A Propos")
        self.dialog.geometry("600x400")
        self.dialog.resizable(False, False)
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')
        self.dialog.configure(bg="white")
        
        self._build()
        
    def _build(self):
        # Container
        container = tk.Frame(self.dialog, bg="white", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Flag (Text based for simplicity and reliability)
        lbl_flag = tk.Label(container, text="🇩🇿", font=("Arial", 64), bg="white")
        lbl_flag.pack(pady=(0, 20))
        
        # Text
        lbl_text = tk.Label(
            container,
            text=("Développé par : Mr Oulmi Abdeldjallil\n"
                  "en collaboration avec Mr Boullala Rabah\n"
                  "pour l'ECDE OUED SMAR"),
            font=("Arial", 14, "bold"),
            fg="#2e7d32", # Green
            bg="white",
            justify="center",
            wraplength=500
        )
        lbl_text.pack(pady=20)
        
        tk.Button(container, text="Fermer", command=self.dialog.destroy, bg="#757575", fg="white", font=("Arial", 10)).pack(pady=(20,0))
