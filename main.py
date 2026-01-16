"""
Main Entry Point - Commercial Management System
Handles application startup, login, and initialization
"""

import tkinter as tk
from tkinter import messagebox
from database import get_db
from ui import MainApplication
from utils import create_backup
import sys


class LoginWindow:
    """Login window for user authentication"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Connexion - Gestion Commerciale")
        self.root.geometry("400x300")
        self.root.configure(bg="#1a237e")
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")
        
        self.user = None
        self._build_ui()
    
    def _build_ui(self):
        """Build login UI"""
        # Title
        title = tk.Label(
            self.root,
            text="GESTION COMMERCIALE",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#1a237e"
        )
        title.pack(pady=30)
        
        # Login frame
        frame = tk.Frame(self.root, bg="white", bd=2, relief=tk.RAISED)
        frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)
        
        # Username
        tk.Label(
            frame,
            text="Nom d'utilisateur",
            font=("Arial", 11),
            bg="white"
        ).pack(pady=(20, 5))
        
        self.username_entry = tk.Entry(frame, font=("Arial", 12), width=25)
        self.username_entry.pack(pady=5)
        self.username_entry.focus()
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        
        # Password
        tk.Label(
            frame,
            text="Mot de passe",
            font=("Arial", 11),
            bg="white"
        ).pack(pady=(15, 5))
        
        self.password_entry = tk.Entry(frame, font=("Arial", 12), width=25, show="•")
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Login button
        login_btn = tk.Button(
            frame,
            text="Se connecter",
            font=("Arial", 12, "bold"),
            bg="#00bcd4",
            fg="white",
            cursor="hand2",
            command=self.login,
            width=20
        )
        login_btn.pack(pady=20)
        
        # Default credentials hint
        hint = tk.Label(
            self.root,
            text="Par défaut: admin / admin123",
            font=("Arial", 9),
            fg="white",
            bg="#1a237e"
        )
        hint.pack(pady=5)
    
    def login(self):
        """Authenticate user"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
        
        db = get_db()
        user = db.authenticate_user(username, password)
        
        if user:
            self.user = user
            self.root.destroy()
        else:
            messagebox.showerror(
                "Erreur",
                "Nom d'utilisateur ou mot de passe incorrect"
            )
            self.password_entry.delete(0, tk.END)
    
    def run(self):
        """Run login window"""
        self.root.mainloop()
        return self.user


def main():
    """Main application entry point"""
    # [NEW] Check Database Existence & Prompt if Missing
    import os
    import configparser
    from tkinter import filedialog
    
    config_path = "config.ini"
    default_db_path = r"C:\GICA_PROJET\gestion_commerciale.db"
    
    # Resolve expected path
    target_path = default_db_path
    if os.path.exists(config_path):
        cfg = configparser.ConfigParser()
        try:
            cfg.read(config_path)
            if 'DATABASE' in cfg and 'path' in cfg['DATABASE']:
                 candidate = cfg['DATABASE']['path'].strip()
                 if candidate:
                     target_path = candidate
        except:
            pass

    # If file doesn't exist, prompt user
    if not os.path.exists(target_path):
        # Create hidden root for dialog (since we haven't started app yet)
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        
        msg = f"La base de données n'a pas été trouvée à l'emplacement :\n{target_path}\n\nVoulez-vous indiquer l'emplacement réel ?"
        # Note: We must update window to ensure dialog appears on top/focus
        root_tmp.update()
        
        if messagebox.askyesno("Base de données introuvable", msg):
            new_path = filedialog.askopenfilename(
                title="Sélectionner la base de données",
                filetypes=[("Base de données SQLite", "*.db"), ("Tous les fichiers", "*.*")]
            )
            if new_path:
                # Update config.ini
                cfg = configparser.ConfigParser()
                if os.path.exists(config_path):
                    cfg.read(config_path)
                
                if 'DATABASE' not in cfg:
                    cfg['DATABASE'] = {}
                cfg['DATABASE']['path'] = new_path
                
                try:
                    with open(config_path, 'w') as configfile:
                        cfg.write(configfile)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de sauvegarder la configuration:\n{e}")
        
        root_tmp.destroy()

    try:
        while True:
            # Show login window
            login = LoginWindow()
            user = login.run()
            
            if not user:
                print("Connexion annulée")
                break
            
            # Create main window
            root = tk.Tk()
            app = MainApplication(root, user)
            
            # Use a shared state to track if we should restart (logout) or quit
            app_state = {'restart': False}
            app.set_logout_callback(lambda: _trigger_restart(root, app_state))
            
            # Handle window close
            def on_closing():
                if messagebox.askyesno("Quitter", "Voulez-vous quitter l'application ?"):
                    # Create backup before closing
                    backup_path = create_backup()
                    if backup_path:
                        print(f"Sauvegarde créée: {backup_path}")
                    root.destroy()
            
            root.protocol("WM_DELETE_WINDOW", on_closing)
            
            # Run application
            root.mainloop()
            
            if not app_state['restart']:
                break

    except Exception as e:
        messagebox.showerror("Erreur Critique", f"Une erreur est survenue:\n{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def _trigger_restart(root, state):
    state['restart'] = True
    root.destroy()


if __name__ == "__main__":
    main()
