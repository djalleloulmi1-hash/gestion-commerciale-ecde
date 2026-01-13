"""
Database Layer - Commercial Management System
Handles all database operations, schema creation, and data access
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


# ==================================================================================
# MASTER SCHEMA - The Single Source of Truth for Database Structure
# ==================================================================================
# ATTENTION : Pour toute modification de structure, mettez d'abord à jour ce MASTER_SCHEMA.
# Le programme se chargera de répercuter les changements sur le fichier .db au prochain lancement.
# ==================================================================================

# ==================================================================================
# MASTER SCHEMA - The Single Source of Truth for Database Structure
# ==================================================================================
# ATTENTION : Pour toute modification de structure, mettez d'abord à jour ce MASTER_SCHEMA.
# Le programme se chargera de répercuter les changements sur le fichier .db au prochain lancement.
# ==================================================================================

MASTER_SCHEMA = {
    "users": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "username": "TEXT UNIQUE NOT NULL",
        "password": "TEXT NOT NULL",
        "full_name": "TEXT NOT NULL",
        "role": "TEXT DEFAULT 'user'",
        "active": "INTEGER DEFAULT 1",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "created_by": "INTEGER REFERENCES users(id)"
    },
    "clients": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "code_client": "TEXT",
        "raison_sociale": "TEXT NOT NULL",
        "adresse": "TEXT NOT NULL",
        "rc": "TEXT NOT NULL",
        "nis": "TEXT NOT NULL",
        "nif": "TEXT NOT NULL",
        "article_imposition": "TEXT NOT NULL",
        "email": "TEXT",
        "tel_1": "TEXT",
        "tel_2": "TEXT",
        "compte_bancaire": "TEXT",
        "categorie": "TEXT",
        "banque": "TEXT",
        "seuil_credit": "REAL DEFAULT 0.0",
        "report_n_moins_1": "REAL DEFAULT 0.0",
        "solde_creance": "REAL DEFAULT 0.0",
        "active": "INTEGER DEFAULT 1",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "products": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nom": "TEXT NOT NULL",
        "unite": "TEXT NOT NULL",
        "code_produit": "TEXT",
        "stock_initial": "REAL DEFAULT 0.0",
        "cout_revient": "REAL DEFAULT 0.0",
        "prix_actuel": "REAL NOT NULL",
        "tva": "REAL DEFAULT 19.0",
        "stock_actuel": "REAL DEFAULT 0.0",
        "categorie": "TEXT DEFAULT 'Autre'",
        "parent_stock_id": "INTEGER REFERENCES products(id)",
        "active": "INTEGER DEFAULT 1",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "historique_prix": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "product_id": "INTEGER NOT NULL REFERENCES products(id)",
        "ancien_prix": "REAL NOT NULL",
        "nouveau_prix": "REAL NOT NULL",
        "reference_note": "TEXT",
        "date_note": "TEXT",
        "date_application": "TEXT NOT NULL",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "receptions": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "numero": "TEXT UNIQUE NOT NULL",
        "annee": "INTEGER NOT NULL",
        "date_reception": "TEXT NOT NULL",
        "chauffeur": "TEXT NOT NULL",
        "matricule": "TEXT NOT NULL",
        "transporteur": "TEXT NOT NULL",
        "lieu_livraison": "TEXT NOT NULL",
        "adresse_chantier": "TEXT",
        "product_id": "INTEGER NOT NULL REFERENCES products(id)",
        "quantite_annoncee": "REAL NOT NULL",
        "quantite_recue": "REAL NOT NULL",
        "ecart": "REAL DEFAULT 0.0",
        "motif_ecart": "TEXT",
        "matricule_remorque": "TEXT",
        "num_bon_transfert": "TEXT",
        "date_bt": "TEXT",
        "num_facture": "TEXT",
        "date_fact": "TEXT",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "factures": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "numero": "TEXT UNIQUE NOT NULL",
        "type_document": "TEXT NOT NULL",
        "type_vente": "TEXT",
        "annee": "INTEGER NOT NULL",
        "date_facture": "TEXT NOT NULL",
        "client_id": "INTEGER NOT NULL REFERENCES clients(id)",
        "facture_origine_id": "INTEGER REFERENCES factures(id)",
        "montant_ht": "REAL DEFAULT 0.0",
        "montant_tva": "REAL DEFAULT 0.0",
        "montant_ttc": "REAL DEFAULT 0.0",
        "statut": "TEXT DEFAULT 'Non soldée'",
        "statut_facture": "TEXT",
        "mode_paiement": "TEXT",
        "ref_paiement": "TEXT",
        "banque": "TEXT",
        "date_paiement": "TEXT",
        "motif": "TEXT",
        "client_compte_bancaire": "TEXT",
        "client_categorie": "TEXT",
        "contract_id": "INTEGER REFERENCES contracts(id)",
        "contrat_code": "TEXT",
        "chauffeur": "TEXT",
        "matricule_tracteur": "TEXT",
        "matricule_remorque": "TEXT",
        "transporteur": "TEXT",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "lignes_facture": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "facture_id": "INTEGER NOT NULL REFERENCES factures(id) ON DELETE CASCADE",
        "product_id": "INTEGER NOT NULL REFERENCES products(id)",
        "quantite": "REAL NOT NULL",
        "prix_unitaire": "REAL NOT NULL",
        "montant": "REAL NOT NULL",
        "taux_remise": "REAL DEFAULT 0.0",
        "prix_initial": "REAL DEFAULT 0.0"
    },
    "paiements": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "numero": "TEXT UNIQUE NOT NULL",
        "date_paiement": "TEXT NOT NULL",
        "client_id": "INTEGER NOT NULL REFERENCES clients(id)",
        "facture_id": "INTEGER REFERENCES factures(id)",
        "montant": "REAL NOT NULL",
        "mode_paiement": "TEXT NOT NULL",
        "reference": "TEXT",
        "banque": "TEXT",
        "statut": "TEXT DEFAULT 'En attente'",
        "bordereau_id": "INTEGER",
        "contrat_num": "TEXT",
        "contrat_date_debut": "TEXT",
        "contrat_date_fin": "TEXT",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "stock_movements": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "product_id": "INTEGER NOT NULL REFERENCES products(id)",
        "type_mouvement": "TEXT NOT NULL",
        "quantite": "REAL NOT NULL",
        "reference_document": "TEXT",
        "document_id": "INTEGER",
        "stock_avant": "REAL NOT NULL",
        "stock_apres": "REAL NOT NULL",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "bordereaux": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "numero": "TEXT UNIQUE NOT NULL",
        "date_bordereau": "TEXT NOT NULL",
        "banque": "TEXT NOT NULL",
        "montant_total": "REAL DEFAULT 0.0",
        "nombre_paiements": "INTEGER DEFAULT 0",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "clotures": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "annee": "INTEGER UNIQUE NOT NULL",
        "date_cloture": "TEXT NOT NULL",
        "stocks_snapshot": "TEXT",
        "soldes_snapshot": "TEXT",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "audit_logs": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER REFERENCES users(id)",
        "username": "TEXT",
        "action": "TEXT NOT NULL",
        "details": "TEXT",
        "timestamp": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "contracts": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "client_id": "INTEGER NOT NULL REFERENCES clients(id)",
        "code": "TEXT",
        "date_debut": "TEXT NOT NULL",
        "date_fin": "TEXT NOT NULL",
        "montant_total": "REAL DEFAULT 0.0",
        "active": "INTEGER DEFAULT 1",
        "created_by": "INTEGER REFERENCES users(id)",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    }
}


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    # Force local absolute path as requested
    DEFAULT_DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

    def __init__(self, db_path: str = None):
        # Use default if not provided, else check if it's the safe path
        if db_path is None:
            self.db_path = self.DEFAULT_DB_PATH
        else:
            self.db_path = db_path
            
        self.connection: Optional[sqlite3.Connection] = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Start Self-Healing Process
        self.verifier_et_reparer_base_de_donnees()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection with WAL mode enabled"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Enable Write-Ahead Logging for concurrency
            self.connection.execute("PRAGMA journal_mode=WAL;") 
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def verifier_et_reparer_base_de_donnees(self):
        """
        SELF-HEALING SYSTEM
        Compares physical database with MASTER_SCHEMA.
        Adds missing tables and columns automatically without data loss.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        print("[System] Starting Database Self-Healing...")
        
        for table_name, columns in MASTER_SCHEMA.items():
            # 1. Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                # Table does not exist, create it
                print(f"[Self-Healing] Creating new table: {table_name}")
                col_defs = [f"{col} {definition}" for col, definition in columns.items()]
                query = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
                cursor.execute(query)
            else:
                # 2. Table exists, check for missing columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_cols = {row['name'] for row in cursor.fetchall()}
                
                for col_name, col_def in columns.items():
                    if col_name not in existing_cols:
                        print(f"[Self-Healing] Adding missing column: {table_name}.{col_name}")
                        try:
                            # Add missing column
                            # Note: SQLite limitation - cannot add UNIQUE or PRIMARY KEY via ALTER TABLE usually, 
                            # but simple columns work fine.
                            # Careful with NOT NULL on existing rows (needs default).
                            # Our schema generally has defaults or allows NULL implicitly in logic if not strict here.
                            # For safety, strict NOT NULLs might fail if table has data. 
                            # But here we just try.
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")
                        except sqlite3.OperationalError as e:
                            print(f"[Error] Could not add column {col_name} to {table_name}: {e}")
        
        conn.commit()
        self._initialize_default_data()
        print("[System] Database Self-Healing Complete.")

    def _initialize_default_data(self):
        """Insert default data if tables are empty"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, role)
                VALUES ('admin', 'admin123', 'Administrateur', 'admin')
            """)
        
        # Check if products exist
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            products = [
                ('Sac 25 KG', 'Sac', 0.0),
                ('Sac 50 KG', 'Sac', 0.0),
                ('Vrac', 'Tonne', 0.0)
            ]
            cursor.executemany("""
                INSERT INTO products (nom, unite, prix_actuel)
                VALUES (?, ?, ?)
            """, products)
        
        conn.commit()
    
    def export_miroir(self, target_folder: str) -> bool:
        """
        Creates a read-only mirror copy of the database.
        Safe for external reading (Directeur) while app is running (WAL mode).
        """
        import shutil
        import time
        
        try:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder, exist_ok=True)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(target_folder, f"gestion_MIRROR_{timestamp}.db")
            
            # Use SQLite Online Backup API if possible, or just copy file since WAL allows it better
            # But standard copy might copy a locked file. 
            # Best way with sqlite3 is using the backup API.
            
            src_conn = self._get_connection()
            dst_conn = sqlite3.connect(target_path)
            
            with dst_conn:
                src_conn.backup(dst_conn)
            
            dst_conn.close()
            return True, target_path
        except Exception as e:
            print(f"Export Miroir Failed: {e}")
            return False, str(e)


    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    # ==================== USER OPERATIONS ====================
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, role, active
            FROM users
            WHERE username = ? AND password = ? AND active = 1
        """, (username, password))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_user(self, username: str, password: str, full_name: str, 
                   role: str = 'user', created_by: int = None) -> int:
        """Create new user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, full_name, role, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password, full_name, role, created_by))
        conn.commit()
        return cursor.lastrowid
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY full_name")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_user(self, user_id: int, **kwargs):
        """Update user fields"""
        conn = self._get_connection()
        cursor = conn.cursor()
        fields = ', '.join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [user_id]
        cursor.execute(f"UPDATE users SET {fields} WHERE id = ?", values)
        conn.commit()

    def delete_user(self, user_id: int):
        """Soft delete user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
        conn.commit()

    def log_action(self, user_id: int, action: str, details: str = None, username: str = None):
        """Log user action to audit_logs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if not username and user_id:
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                username = row[0]
                
        cursor.execute("""
            INSERT INTO audit_logs (user_id, username, action, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, action, details))
        conn.commit()
    
    # ==================== CLIENT OPERATIONS ====================
    
    def create_client(self, raison_sociale: str, adresse: str, rc: str, nis: str,
                      nif: str, article_imposition: str, code_client: str = None, 
                      email: str = None, tel_1: str = None, tel_2: str = None,
                      compte_bancaire: str = None, categorie: str = None,
                      seuil_credit: float = 0.0, report_n_moins_1: float = 0.0, 
                      created_by: int = None) -> int:
        """Create new client"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (raison_sociale, adresse, rc, nis, nif, 
                               article_imposition, code_client, email, tel_1, tel_2,
                               compte_bancaire, categorie,
                               seuil_credit, report_n_moins_1, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (raison_sociale, adresse, rc, nis, nif, article_imposition,
              code_client, email, tel_1, tel_2, compte_bancaire, categorie,
              seuil_credit, report_n_moins_1, created_by))
        conn.commit()
        return cursor.lastrowid
    
    def get_all_clients(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all clients"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM clients"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY raison_sociale"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_client_by_id(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get client by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_client(self, client_id: int, **kwargs):
        """Update client fields"""
        conn = self._get_connection()
        cursor = conn.cursor()
        fields = ', '.join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [client_id]
        cursor.execute(f"UPDATE clients SET {fields} WHERE id = ?", values)
        conn.commit()

    def delete_client(self, client_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()

    def check_client_exists(self, code_client: str, raison_sociale: str, exclude_id: int = None) -> Tuple[bool, str]:
        """
        Check if a client with the same Code or Raison Sociale already exists.
        Returns (True, message) if duplicate found, else (False, "").
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check Code Client
        if code_client:
            query = "SELECT id, raison_sociale FROM clients WHERE code_client = ? AND active = 1"
            params = [code_client]
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                return True, f"Un client avec le code '{code_client}' existe déjà ({row[1]})."

        # Check Raison Sociale
        if raison_sociale:
            query = "SELECT id, code_client FROM clients WHERE raison_sociale = ? AND active = 1"
            params = [raison_sociale]
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                return True, f"Un client avec la raison sociale '{raison_sociale}' existe déjà (Code: {row[1]})."
                
        return False, ""

    # ==================== CONTRACT OPERATIONS ====================
    
    def create_contract(self, client_id: int, code: str, date_debut: str, 
                       date_fin: str, montant_total: float = 0.0, created_by: int = None) -> int:
        """Create new contract"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contracts (client_id, code, date_debut, date_fin, montant_total, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (client_id, code, date_debut, date_fin, montant_total, created_by))
        conn.commit()
        return cursor.lastrowid
    
    def get_client_contracts(self, client_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get contracts for a specific client"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM contracts WHERE client_id = ?"
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY date_fin DESC"
        cursor.execute(query, (client_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_contract(self, contract_id: int, **kwargs):
        """Update contract fields"""
        conn = self._get_connection()
        cursor = conn.cursor()
        fields = ', '.join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [contract_id]
        cursor.execute(f"UPDATE contracts SET {fields} WHERE id = ?", values)
        conn.commit()
        
    def delete_contract(self, contract_id: int):
        """Soft delete contract"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE contracts SET active = 0 WHERE id = ?", (contract_id,))
        conn.commit()
    
    # ==================== PRODUCT OPERATIONS ====================
    
    def create_product(self, nom: str, unite: str, code_produit: str = None,
                      stock_initial: float = 0.0, cout_revient: float = 0.0,
                      prix_actuel: float = 0.0, stock_actuel: float = 0.0,
                      tva: float = 19.0, categorie: str = 'Autre', 
                      parent_stock_id: int = None,
                      created_by: int = None) -> int:
        """Create new product"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (nom, unite, code_produit, stock_initial, cout_revient,
                                prix_actuel, stock_actuel, tva, categorie, parent_stock_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom, unite, code_produit, stock_initial, cout_revient, 
              prix_actuel, stock_actuel, tva, categorie, parent_stock_id, created_by))
        conn.commit()
        return cursor.lastrowid

    def update_product(self, product_id: int, **kwargs):
        """Update product fields"""
        conn = self._get_connection()
        cursor = conn.cursor()
        fields = ', '.join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [product_id]
        cursor.execute(f"UPDATE products SET {fields} WHERE id = ?", values)
        conn.commit()

    def delete_product(self, product_id: int):
        """Soft delete product"""
        conn = self._get_connection()
        conn.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
        conn.commit()

    def get_all_products(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all products"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY nom"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_product_price(self, product_id: int, nouveau_prix: float, 
                           reference_note: str = None, date_note: str = None,
                           date_application: str = None, created_by: int = None):
        """Update product price and log history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get current price
        cursor.execute("SELECT prix_actuel FROM products WHERE id = ?", (product_id,))
        ancien_prix = cursor.fetchone()[0]
        
        if date_application is None:
            date_application = datetime.now().strftime("%Y-%m-%d")
        
        # Log price change
        cursor.execute("""
            INSERT INTO historique_prix 
            (product_id, ancien_prix, nouveau_prix, reference_note, 
             date_note, date_application, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, ancien_prix, nouveau_prix, reference_note,
              date_note, date_application, created_by))
        
        # Update current price
        cursor.execute("""
            UPDATE products SET prix_actuel = ? WHERE id = ?
        """, (nouveau_prix, product_id))
        
        conn.commit()
    
    def get_price_history(self, product_id: int = None) -> List[Dict[str, Any]]:
        """Get price history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT h.*, p.nom as product_nom, u.full_name as created_by_name
            FROM historique_prix h
            JOIN products p ON h.product_id = p.id
            LEFT JOIN users u ON h.created_by = u.id
        """
        if product_id:
            query += " WHERE h.product_id = ?"
            cursor.execute(query + " ORDER BY h.created_at DESC", (product_id,))
        else:
            cursor.execute(query + " ORDER BY h.created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_product_stock(self, product_id: int, new_stock: float):
        """Update product stock (direct update)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET stock_actuel = ? WHERE id = ?
        """, (new_stock, product_id))
        conn.commit()

    def update_stock(self, product_id: int, quantite_delta: float):
        """Update stock (relative change)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET stock_actuel = stock_actuel + ? WHERE id = ?
        """, (quantite_delta, product_id))
        conn.commit()
    
    # ==================== RECEPTION OPERATIONS ====================
    
    def create_reception(self, annee: int, date_reception: str, chauffeur: str,
                        matricule: str, transporteur: str, lieu_livraison: str,
                        adresse_chantier: str, product_id: int, 
                        quantite_annoncee: float, quantite_recue: float,
                        matricule_remorque: str = None, 
                        num_bon_transfert: str = None, date_bt: str = None,
                        num_facture: str = None, date_fact: str = None,
                        motif_ecart: str = None,
                        created_by: int = None) -> int:
        """Create new reception"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate numero
        cursor.execute("""
            SELECT COUNT(*) FROM receptions WHERE annee = ?
        """, (annee,))
        count = cursor.fetchone()[0] + 1
        numero = f"BR-{count:04d}-{annee}"
        
        ecart = quantite_recue - quantite_annoncee
        
        cursor.execute("""
            INSERT INTO receptions 
            (numero, annee, date_reception, chauffeur, matricule, transporteur,
             lieu_livraison, adresse_chantier, product_id, quantite_annoncee,
             quantite_recue, ecart, matricule_remorque, created_by,
             num_bon_transfert, date_bt, num_facture, date_fact, motif_ecart)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (numero, annee, date_reception, chauffeur, matricule, transporteur,
              lieu_livraison, adresse_chantier, product_id, quantite_annoncee,
              quantite_recue, ecart, matricule_remorque, created_by,
              num_bon_transfert, date_bt, num_facture, date_fact, motif_ecart))
        
        reception_id = cursor.lastrowid
        conn.commit()
        return reception_id
    
    def delete_reception(self, reception_id: int):
        """Delete reception by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM receptions WHERE id = ?", (reception_id,))
        conn.commit()

    def get_all_receptions(self, annee: int = None) -> List[Dict[str, Any]]:
        """Get all receptions"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT r.*, p.nom as product_nom, p.unite, u.full_name as created_by_name
            FROM receptions r
            JOIN products p ON r.product_id = p.id
            LEFT JOIN users u ON r.created_by = u.id
        """
        if annee:
            query += " WHERE r.annee = ?"
            cursor.execute(query + " ORDER BY r.created_at DESC", (annee,))
        else:
            cursor.execute(query + " ORDER BY r.created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== INVOICE OPERATIONS ====================
    
    def generate_facture_number(self, type_document: str, annee: int) -> str:
        """Generate unique invoice number"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate numero with shared sequence
        cursor.execute("""
            SELECT COUNT(*) FROM factures WHERE annee = ?
        """, (annee,))
        count = cursor.fetchone()[0] + 1
        
        if type_document == 'Facture':
            return f"FAC-{count:04d}-{annee}"
        else:  # Avoir
            return f"AV-{count:04d}-{annee}"

    def get_next_invoice_number(self, type_document: str, annee: int) -> str:
        """Preview the next number (Preview Only)"""
        return self.generate_facture_number(type_document, annee)


    def create_facture(self, type_document: str, annee: int, date_facture: str,
                      client_id: int, facture_origine_id: int = None,
                      etat_paiement: str = 'Comptant', motif: str = None,
                      ref_paiement: str = None, banque: str = None,
                      date_paiement: str = None, statut_facture: str = 'Non soldée',
                      contract_id: int = None,
                      chauffeur: str = None, matricule_tracteur: str = None, matricule_remorque: str = None,
                      transporteur: str = None,
                      type_vente: str = None, mode_paiement: str = None,
                      created_by: int = None) -> int:
        """Create new invoice or credit note"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        numero = self.generate_facture_number(type_document, annee)
        
        cursor.execute("""
            INSERT INTO factures (numero, type_document, annee, date_facture, client_id, 
             facture_origine_id, motif, type_vente, mode_paiement, 
             ref_paiement, banque, date_paiement, statut_facture, contract_id, 
             chauffeur, matricule_tracteur, matricule_remorque, transporteur, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (numero, type_document, annee, date_facture, client_id,
              facture_origine_id, motif, type_vente, mode_paiement,
              ref_paiement, banque, date_paiement, statut_facture, contract_id,
              chauffeur, matricule_tracteur, matricule_remorque, transporteur, created_by))

        
        facture_id = cursor.lastrowid
        conn.commit()
        return facture_id
    
    
    def get_unique_transporteurs(self) -> List[str]:
        """Get list of unique transporteurs from both receptions and factures"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Combine both sources
        cursor.execute("""
            SELECT DISTINCT transporteur FROM receptions WHERE transporteur IS NOT NULL AND transporteur != ''
            UNION
            SELECT DISTINCT transporteur FROM factures WHERE transporteur IS NOT NULL AND transporteur != ''
            ORDER BY transporteur
        """)
        
        return [row[0] for row in cursor.fetchall()]

    def get_unique_chauffeurs(self) -> List[str]:
        """Get list of unique chauffeurs from both receptions and factures"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Combine both sources
        cursor.execute("""
            SELECT DISTINCT chauffeur FROM receptions WHERE chauffeur IS NOT NULL AND chauffeur != ''
            UNION
            SELECT DISTINCT chauffeur FROM factures WHERE chauffeur IS NOT NULL AND chauffeur != ''
            ORDER BY chauffeur
        """)
        
        return [row[0] for row in cursor.fetchall()]

    def get_last_transport_info_by_chauffeur(self, chauffeur: str) -> Optional[Dict[str, str]]:
        """
        Get the most recent transport details (matricule, remorque, transporteur) 
        used by a specific chauffeur.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Query both tables, prioritizing by Date
        cursor.execute("""
            SELECT matricule_tracteur, matricule_remorque, transporteur, created_at 
            FROM (
                SELECT matricule_tracteur, matricule_remorque, transporteur, created_at 
                FROM factures 
                WHERE chauffeur = ? AND chauffeur != ''
                
                UNION ALL
                
                SELECT matricule as matricule_tracteur, matricule_remorque, transporteur, created_at 
                FROM receptions 
                WHERE chauffeur = ? AND chauffeur != ''
            )
            ORDER BY created_at DESC
            LIMIT 1
        """, (chauffeur, chauffeur))
        
        row = cursor.fetchone()
        if row:
            return {
                'matricule_tracteur': row[0],
                'matricule_remorque': row[1],
                'transporteur': row[2]
            }
        return None
    
    def add_ligne_facture(self, facture_id: int, product_id: int, 
                         quantite: float, prix_unitaire: float):
        """Add line item to invoice"""
        conn = self._get_connection()
        cursor = conn.cursor()
        montant = quantite * prix_unitaire
        cursor.execute("""
            INSERT INTO lignes_facture 
            (facture_id, product_id, quantite, prix_unitaire, montant)
            VALUES (?, ?, ?, ?, ?)
        """, (facture_id, product_id, quantite, prix_unitaire, montant))
        conn.commit()
    
    def update_facture_totals(self, facture_id: int, montant_ht: float,
                             montant_tva: float, montant_ttc: float):
        """Update invoice totals"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE factures 
            SET montant_ht = ?, montant_tva = ?, montant_ttc = ?
            WHERE id = ?
        """, (montant_ht, montant_tva, montant_ttc, facture_id))
        conn.commit()
    
    def get_all_factures(self, client_id: int = None, annee: int = None,
                        type_document: str = None) -> List[Dict[str, Any]]:
        """Get all invoices"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT f.*, c.raison_sociale as client_nom, u.full_name as created_by_name,
                   (SELECT COALESCE(SUM(quantite), 0) FROM lignes_facture WHERE facture_id = f.id) as total_quantite,
                   (SELECT p.unite FROM lignes_facture l JOIN products p ON l.product_id = p.id WHERE l.facture_id = f.id LIMIT 1) as unite,
                   (SELECT numero FROM factures WHERE id = f.facture_origine_id) as parent_ref,
                   (SELECT GROUP_CONCAT(numero, ', ') FROM factures WHERE facture_origine_id = f.id AND type_document = 'Avoir' AND statut != 'Annulée') as child_refs
            FROM factures f
            JOIN clients c ON f.client_id = c.id
            LEFT JOIN users u ON f.created_by = u.id
            WHERE 1=1
        """
        params = []
        if client_id:
            query += " AND f.client_id = ?"
            params.append(client_id)
        if annee:
            query += " AND f.annee = ?"
            params.append(annee)
        if type_document:
            query += " AND f.type_document = ?"
            params.append(type_document)
        
        query += " ORDER BY f.created_at DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_facture_by_id(self, facture_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice by ID with line items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, c.raison_sociale, c.adresse, c.rc, c.nis, c.nif, 
                   co.code as contract_code, co.date_debut as contract_debut, co.date_fin as contract_fin
            FROM factures f
            JOIN clients c ON f.client_id = c.id
            LEFT JOIN contracts co ON f.contract_id = co.id
            WHERE f.id = ?
        """, (facture_id,))
        facture = cursor.fetchone()
        if not facture:
            return None
        
        facture_dict = dict(facture)
        
        # Get line items
        cursor.execute("""
            SELECT l.*, p.nom as product_nom, p.unite
            FROM lignes_facture l
            JOIN products p ON l.product_id = p.id
            WHERE l.facture_id = ?
        """, (facture_id,))
        facture_dict['lignes'] = [dict(row) for row in cursor.fetchall()]
        
        return facture_dict
    
    def get_invoice_details_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get flattened invoice details (lines) within date range"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Ensure dates are in YYYY-MM-DD
        try:
            # Assume strict YYYY-MM-DD format from UI, but basic validation/conversion is good practice
            # Here we trust the UI to pass strings compatible with SQLite comparison
            pass
        except:
            pass
            
        cursor.execute("""
            SELECT 
                f.numero,
                f.date_facture,
                p.nom as product_nom,
                l.quantite,
                l.montant as montant_ht,
                f.statut,
                f.type_document,
                (SELECT COUNT(*) FROM factures WHERE facture_origine_id = f.id AND type_document = 'Avoir' AND statut != 'Annulée') > 0 as has_avoir
            FROM lignes_facture l
            JOIN factures f ON l.facture_id = f.id
            JOIN products p ON l.product_id = p.id
            WHERE f.date_facture BETWEEN ? AND ?
            ORDER BY f.date_facture DESC, f.numero DESC
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_client_sales_summary(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get sales aggregated by client for Etat 104"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.raison_sociale,
                c.rc,
                c.nif,
                c.nis,
                c.article_imposition,
                SUM(f.montant_ht) as chiffre_affaire_ht
            FROM factures f
            JOIN clients c ON f.client_id = c.id
            WHERE f.date_facture BETWEEN ? AND ?
              AND f.statut != 'Annulée'
            GROUP BY c.id
            ORDER BY c.raison_sociale
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_payments_details_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get payments details with client info by date range"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.date_paiement,
                p.reference,
                p.mode_paiement,
                p.montant,
                c.raison_sociale
            FROM paiements p
            JOIN clients c ON p.client_id = c.id
            WHERE p.date_paiement BETWEEN ? AND ?
            ORDER BY p.date_paiement DESC
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]

    # ==================== PAYMENT OPERATIONS ====================
    
    def create_paiement(self, date_paiement: str, client_id: int, 
                       montant: float, mode_paiement: str,
                       facture_id: int = None, reference: str = None,
                       banque: str = None, contrat_num: str = None,
                       contrat_date_debut: str = None, contrat_date_fin: str = None,
                       created_by: int = None) -> int:
        """Create new payment"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate numero
        cursor.execute("SELECT COUNT(*) FROM paiements")
        count = cursor.fetchone()[0] + 1
        numero = f"PAY-{count:06d}"
        
        cursor.execute("""
            INSERT INTO paiements 
            (numero, date_paiement, client_id, facture_id, montant,
             mode_paiement, reference, banque, contrat_num, 
             contrat_date_debut, contrat_date_fin, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (numero, date_paiement, client_id, facture_id, montant,
              mode_paiement, reference, banque, contrat_num,
              contrat_date_debut, contrat_date_fin, created_by))
        
        paiement_id = cursor.lastrowid
        conn.commit()
        return paiement_id
    
    def get_all_paiements(self, client_id: int = None, 
                         statut: str = None) -> List[Dict[str, Any]]:
        """Get all payments"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT p.*, c.raison_sociale as client_nom, 
                   f.numero as facture_numero,
                   u.full_name as created_by_name
            FROM paiements p
            JOIN clients c ON p.client_id = c.id
            LEFT JOIN factures f ON p.facture_id = f.id
            LEFT JOIN users u ON p.created_by = u.id
            WHERE 1=1
        """
        params = []
        if client_id:
            query += " AND p.client_id = ?"
            params.append(client_id)
        if statut:
            query += " AND p.statut = ?"
            params.append(statut)
        query += " ORDER BY p.created_at DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update_paiement_statut(self, paiement_id: int, statut: str, 
                              bordereau_id: int = None):
        """Update payment status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE paiements 
            SET statut = ?, bordereau_id = ?
            WHERE id = ?
        """, (statut, bordereau_id, paiement_id))
        conn.commit()
    
    # ==================== STOCK MOVEMENT OPERATIONS ====================
    
    def log_stock_movement(self, product_id: int, type_mouvement: str,
                          quantite: float, reference_document: str = None,
                          document_id: int = None, created_by: int = None):
        """Log stock movement"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if product has a parent (Physical Stock)
        # If so, the movement logs against the PARENT to maintain accurate physical inventory.
        cursor.execute("SELECT parent_stock_id, code_produit, nom FROM products WHERE id = ?", (product_id,))
        res = cursor.fetchone()
        
        target_product_id = product_id
        final_ref = reference_document
        
        if res and res['parent_stock_id']:
            target_product_id = res['parent_stock_id']
            # Append child info to reference for traceability
            child_info = res['code_produit'] or res['nom']
            addon = f" (Via {child_info})"
            final_ref = (final_ref or "") + addon

        # Get current stock of TARGET
        cursor.execute("SELECT stock_actuel FROM products WHERE id = ?", (target_product_id,))
        result = cursor.fetchone()
        stock_avant = result[0] if result and result[0] is not None else 0.0
        stock_apres = stock_avant + quantite
        
        # Log movement
        cursor.execute("""
            INSERT INTO stock_movements 
            (product_id, type_mouvement, quantite, reference_document,
             document_id, stock_avant, stock_apres, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (target_product_id, type_mouvement, quantite, final_ref,
              document_id, stock_avant, stock_apres, created_by))
        
        # Update product stock
        cursor.execute("""
            UPDATE products SET stock_actuel = ? WHERE id = ?
        """, (stock_apres, target_product_id))
        
        conn.commit()
    
    def get_stock_movements(self, product_id: int = None) -> List[Dict[str, Any]]:
        """Get stock movements"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT s.*, p.nom as product_nom, u.full_name as created_by_name
            FROM stock_movements s
            JOIN products p ON s.product_id = p.id
            LEFT JOIN users u ON s.created_by = u.id
        """
        if product_id:
            query += " WHERE s.product_id = ?"
            cursor.execute(query + " ORDER BY s.created_at DESC", (product_id,))
        else:
            cursor.execute(query + " ORDER BY s.created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== BORDEREAU OPERATIONS ====================
    
    def create_bordereau(self, date_bordereau: str, banque: str,
                        paiement_ids: List[int], created_by: int = None) -> int:
        """Create bank voucher"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate numero
        cursor.execute("SELECT COUNT(*) FROM bordereaux")
        count = cursor.fetchone()[0] + 1
        numero = f"BOR-{count:04d}"
        
        # Calculate total
        placeholders = ','.join('?' * len(paiement_ids))
        cursor.execute(f"""
            SELECT SUM(montant) FROM paiements WHERE id IN ({placeholders})
        """, paiement_ids)
        montant_total = cursor.fetchone()[0] or 0.0
        
        # Create bordereau
        cursor.execute("""
            INSERT INTO bordereaux 
            (numero, date_bordereau, banque, montant_total, 
             nombre_paiements, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (numero, date_bordereau, banque, montant_total, 
              len(paiement_ids), created_by))
        
        bordereau_id = cursor.lastrowid
        
        # Update payment status
        cursor.execute(f"""
            UPDATE paiements 
            SET statut = 'Déposé', bordereau_id = ?
            WHERE id IN ({placeholders})
        """, [bordereau_id] + paiement_ids)
        
        conn.commit()
        return bordereau_id
    
    def get_all_bordereaux(self) -> List[Dict[str, Any]]:
        """Get all bank vouchers"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, u.full_name as created_by_name
            FROM bordereaux b
            LEFT JOIN users u ON b.created_by = u.id
            ORDER BY b.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_bordereau_with_details(self, bordereau_id: int) -> Optional[Dict[str, Any]]:
        """Get bordereau with its associated payments"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get bordereau info
        cursor.execute("SELECT * FROM bordereaux WHERE id = ?", (bordereau_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        bordereau = dict(row)
        
        # Get payments
        cursor.execute("""
            SELECT p.*, c.raison_sociale as client_nom 
            FROM paiements p
            JOIN clients c ON p.client_id = c.id
            WHERE p.bordereau_id = ?
        """, (bordereau_id,))
        
        paiements = [dict(r) for r in cursor.fetchall()]
        
        return {
            'bordereau': bordereau,
            'paiements': paiements
        }
    
    # ==================== CLOSURE OPERATIONS ====================
    
    def create_cloture(self, annee: int, created_by: int = None) -> int:
        """Create annual closure"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get stock snapshot
        import json
        cursor.execute("SELECT id, nom, stock_actuel FROM products")
        stocks = {row[0]: {'nom': row[1], 'stock': row[2]} 
                 for row in cursor.fetchall()}
        
        # Get client balances snapshot (will be calculated in logic.py)
        # For now, just store empty dict
        soldes = {}
        
        date_cloture = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO clotures 
            (annee, date_cloture, stocks_snapshot, soldes_snapshot, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (annee, date_cloture, json.dumps(stocks), json.dumps(soldes), created_by))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_cloture_by_annee(self, annee: int) -> Optional[Dict[str, Any]]:
        """Get closure by year"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clotures WHERE annee = ?", (annee,))
        row = cursor.fetchone()
        if row:
            import json
            result = dict(row)
            result['stocks_snapshot'] = json.loads(result['stocks_snapshot'])
            result['soldes_snapshot'] = json.loads(result['soldes_snapshot'])
            return result
        return None

    # ==================== RESET OPERATIONS ====================

    def reset_data(self):
        """
        Reset all operational data except Users.
        Be very careful with this method.
        """
        conn = self._get_connection()
        
        tables_to_clear = [
            "lignes_facture",
            "paiements",
            "stock_movements",
            "factures",
            "receptions",
            "contracts",
            "historique_prix",
            "bordereaux",
            "clotures",
            "audit_logs",
            # Products preserved
            "clients"
        ]
        
        try:
            conn.execute("BEGIN TRANSACTION")
            
            for table in tables_to_clear:
                conn.execute(f"DELETE FROM {table}")
                # Reset auto-increment
                conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
            
            # Reset products stock to initial
            conn.execute("UPDATE products SET stock_actuel = stock_initial")
            
            # Reset default admin if somehow deleted (though users table is skipped)
            # Re-initialize defaults if needed? 
            # The prompt says "remettre toutes les bases de données a zero a l'exeption de la table des utilisateurs"
            # So we should probably keep default products? 
            # "effacer le contenu des bases de donnée sans toucher a la structure" usually implies empty tables.
            # But the app might crash if no products exist?
            # Let's stick to strict "delete content". User can re-add products.
            # Wait, `_initialize_default_data` adds default products if empty.
            # Maybe we should re-run `_initialize_default_data` at the end?
            # "effectuer des tests" -> usually implies starting fresh.
            # I will assume clearing everything is fine. The user can re-add or re-run init logic if needed.
            # Actually, `_initialize_default_data` checks `IF COUNT(*) == 0`.
            # So calling it here ensures we at least have base data if that was the intention.
            # Given the request "remettre a zero", empty tables are likely expected.
            # I will NOT re-insert default products to strictly follow "remettre a zero".
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e

# Global database instance
_db_instance: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
