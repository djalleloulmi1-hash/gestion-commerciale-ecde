
import sqlite3
import os

DB_PATH = "gestion_commerciale.db"

def reset_db_except_receptions():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Disable Foreign Keys
        print("Disabling foreign keys...")
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 2. Tables to TRUNCATE (DELETE ALL)
        tables_to_clear = [
            "lignes_facture",
            "factures",
            "paiements",
            "bordereaux",
            "stock_movements",
            "clients",
            "contracts",
            "historique_prix",
            "clotures",
            "audit_logs"
        ]
        
        print("Clearing tables...")
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  - Cleared {table}")
            except sqlite3.OperationalError as e:
                print(f"  - Error clearing {table}: {e}")

        # 3. Recalculate Stock
        print("Recalculating Primary Stock from Receptions...")
        
        # Reset all stock to Initial Stock first
        cursor.execute("UPDATE products SET stock_actuel = stock_initial")
        
        # Get all receptions
        cursor.execute("SELECT product_id, quantite_recue FROM receptions")
        receptions = cursor.fetchall()
        
        product_stock_map = {}
        
        for rec in receptions:
            pid = rec['product_id']
            qty = rec['quantite_recue']
            product_stock_map[pid] = product_stock_map.get(pid, 0.0) + qty
            
        # Update products
        for pid, total_recue in product_stock_map.items():
            # Add received quantity to current stock (which is now just initial)
            cursor.execute("""
                UPDATE products 
                SET stock_actuel = stock_actuel + ? 
                WHERE id = ?
            """, (total_recue, pid))
            
        print(f"  - Updated stock for {len(product_stock_map)} products based on receptions.")

        # 4. Cleanup
        print("Committing changes...")
        conn.commit()
        
        print("Vacuuming database...")
        cursor.execute("VACUUM")
        
        print("Re-enabling foreign keys...")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("Reset Complete.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    reset_db_except_receptions()
