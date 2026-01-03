
import sqlite3
import os

DB_PATH = "gestion_commerciale.db"

def reset_database_partial():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF") # Disable FK to allow truncation in any order
    cursor = conn.cursor()
    
    # List of tables to CLEAR
    tables_to_clear = [
        "factures",
        "lignes_facture",
        "receptions",
        "paiements",
        "bordereaux",
        "stock_movements",
        "audit_logs",
        "contracts",
        "clotures",
        "historique_prix", 
        "clients" # User asked for "base de donnée a l'exception des produits", usually implies clients are gone too.
                  # If they wanted clients, they would say "produits et clients".
                  # I will assume clients should be deleted as they are "transactional" entities in a fresh start context, or at least linked to balances.
    ]
    
    print("Clearing tables...")
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'") # Reset auto-increment
            print(f"  - {table}: Cleared")
        except sqlite3.Error as e:
            print(f"  - {table}: Error {e}")
            
    # Reset Stock for Products
    # Since we deleted receptions and sales, actual stock should be 0 (or stock_initial).
    # We will reset to stock_initial if it exists, or 0.
    # Checking schema from previous steps: products has 'stock_initial' and 'stock_actuel'.
    # If we clear everything, stock_actuel should logically revert to stock_initial.
    # However, if 'stock_initial' itself was a migration record, maybe just 0?
    # Usually 'Stock Initial' is a static value representing start-of-year or start-of-time stock.
    # Let's set stock_actuel = stock_initial.
    
    print("Resetting product stock...")
    try:
        cursor.execute("UPDATE products SET stock_actuel = stock_initial")
        print("  - Products: Stock reset to Initial Stock")
    except sqlite3.Error as e:
        print(f"  - Products: Error updating stock {e}")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()
    
    print("Partial reset complete. Products and Users preserved.")

if __name__ == "__main__":
    reset_database_partial()
