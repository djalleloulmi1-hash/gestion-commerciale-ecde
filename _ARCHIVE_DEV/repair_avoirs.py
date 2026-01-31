
import sqlite3
from database import DatabaseManager

def repair_avoir_signs():
    db = DatabaseManager()
    conn = db._get_connection()
    c = conn.cursor()
    
    print("--- Repairing Avoir Stock Movements ---")
    
    # Select wrong movements (Retour Avoir < 0)
    c.execute("SELECT id, quantite FROM stock_movements WHERE type_mouvement = 'Retour Avoir' AND quantite < 0")
    rows = c.fetchall()
    
    count = 0
    if rows:
        print(f"Found {len(rows)} incorrect records.")
        for row in rows:
            mid = row[0]
            wrong_qty = row[1]
            correct_qty = -wrong_qty # Float flip
            
            # Need to update also product stock_actuel because the negative value DECREASED stock improperly
            # We need to ADD back:
            # 1. Cancel the wrong decrement: +abs(wrong)
            # 2. Apply the correct increment: +abs(wrong)
            # So total stock adjustment = +2 * abs(wrong)
            
            # Wait, let's verify.
            # Stock was updated via logic.py implicitly via manual update or logic?
            # logic.py: self.db.log_stock_movement(...)
            # database.py log_stock_movement triggers: UPDATE products SET stock_actuel = stock_actuel + ?
            
            # So if we passed -400. Stock became X - 400.
            # But it should have been X + 400.
            # So we need to add 800 to fix it. (Add 2 * 400).
            
            # 1. Update Movement
            c.execute("UPDATE stock_movements SET quantite = ? WHERE id = ?", (correct_qty, mid))
            
            # 2. Fix Product Stock
            # Get product id
            c.execute("SELECT product_id FROM stock_movements WHERE id = ?", (mid,))
            pid = c.fetchone()[0]
            
            correction = correct_qty * 2 # Add double the amount
            c.execute("UPDATE products SET stock_actuel = stock_actuel + ? WHERE id = ?", (correction, pid))
            
            count += 1
            print(f"Fixed ID {mid}: Changed {wrong_qty} to {correct_qty}. Adjusted Product {pid} stock by +{correction}.")
            
        conn.commit()
        print(f"Successfully repaired {count} records.")
    else:
        print("No incorrect records found.")

if __name__ == "__main__":
    repair_avoir_signs()
