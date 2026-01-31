
import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = "gestion_commerciale.db"
BACKUP_DIR = "Backups"

def reset_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # 1. Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_BEFORE_RESET_{timestamp}.db")
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_path)
        print(f"DATABASE BACKUP CREATED: {backup_path}")
    else:
        print("DATABASE NOT FOUND!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("STARTING DATABASE RESET...")
        
        # 2. Disable Foreign Keys temporarily to avoid cascading issues during delete
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 3. Tables to DELETE CONTENT (Transactions)
        tables_to_clear = [
            "lignes_facture",
            "factures",
            "stock_movements",
            "receptions",
            "paiements",
            "bordereaux",
            "clotures", 
            "contracts" # Assuming contracts are client-specific transaction data
        ]
        
        # 4. Tables to CLEAR (Reference Data requested to be cleared)
        # User said: "remet a zero toutes les tables ... a l exception de la table (produits)"
        # This implies Clients should be deleted too.
        tables_to_clear.append("clients") 
        
        # Execution
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                # Reset AutoIncrement?
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                print(f"CLEARED TABLE: {table}")
            except Exception as e:
                print(f"Error clearing {table}: {e}")

        # 5. Handle PRODUCTS (Preserve table, Reset Stock)
        print("RESETTING PRODUCT STOCKS...")
        # Reset stock_actuel to 0.0
        cursor.execute("UPDATE products SET stock_actuel = 0.0")
        
        # Optional: Reset stock_initial?
        # If this is a real trial start, maybe stock_initial should be 0 
        # and they will input initial stock via a Reception or Adjustment?
        # User said "n'oublie pas les stocks". Usually means reset them.
        cursor.execute("UPDATE products SET stock_initial = 0.0")
        print("PRODUCTS STOCK RESET TO 0")

        # 6. Re-enable Foreign Keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("DATABASE RESET SUCCESSFUL.")
        
    except Exception as e:
        conn.rollback()
        print(f"CRITICAL ERROR DURING RESET: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    confirmation = input("TYPE 'RESET' TO CONFIRM DELETION OF ALL DATA EXCEPT PRODUCTS/USERS: ")
    if confirmation == "RESET":
        reset_database()
    else:
        print("OPERATION CANCELLED.")
