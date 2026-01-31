import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

from database import get_db

def reset_data():
    print("--- STARTING DATABASE RESET ---")
    print("Warning: This will delete all transactions (Sales, Receptions, Payments, Stock Movements) and reset stocks to 0.")
    
    # Simple check to avoid accidental run purely interactive if possible, 
    # but run_command handles user approval.
    
    db = get_db()
    conn = db._get_connection()
    c = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # 1. DELETE TRANSACTIONS
        tables_to_clear = [
            'receptions', 
            'factures', 
            'lignes_facture', # Usually cascades but explicit is safe
            'paiements',
            'stock_movements',
            'bordereaux',
            'bordereau_items', # If exists
            'closures'
        ]
        
        for table in tables_to_clear:
             try:
                # Check if table exists first (in case of dynamic schemas)
                 c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                 if c.fetchone():
                     print(f"Clearing table: {table}...")
                     c.execute(f"DELETE FROM {table}")
                     # Reset auto-increment
                     c.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
             except Exception as ex:
                 print(f"Skipping {table}: {ex}")

        # 2. RESET STOCKS (Actuel & Initial)
        print("Resetting all products stock (Initial & Actuel) to 0...")
        c.execute("UPDATE products SET stock_initial = 0, stock_actuel = 0")
        
        conn.commit()
        print("--- RESET COMPLETE ---")
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise e

if __name__ == "__main__":
    reset_data()
