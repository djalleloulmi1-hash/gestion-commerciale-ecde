import sqlite3
import os
from datetime import datetime

DB_PATH = "gestion_commerciale.db"

def reset_invoices():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        print("Starting invoice reset process...")
        
        # 1. Delete Invoice Lines (lignes_facture)
        # Although ON DELETE CASCADE might exist, explicit deletion is safer
        cursor.execute("DELETE FROM lignes_facture")
        lines_deleted = cursor.rowcount
        print(f"Deleted {lines_deleted} invoice lines.")

        # 2. Delete Payments linked to invoices
        cursor.execute("DELETE FROM paiements WHERE facture_id IS NOT NULL")
        payments_deleted = cursor.rowcount
        print(f"Deleted {payments_deleted} payments linked to invoices.")

        # 3. Delete Stock Movements related to invoices or credit notes
        # We look for movements where document_id points to a facture and type/reference matches
        cursor.execute("""
            DELETE FROM stock_movements 
            WHERE reference_document LIKE 'FACT%' 
               OR reference_document LIKE 'AVOIR%'
               OR reference_document LIKE 'AV-%'  -- Handle AV- prefix
               OR type_mouvement IN ('Vente', 'Avoir', 'Annulation Facture', 'Retour Avoir')
        """)
        movements_deleted = cursor.rowcount
        print(f"Deleted {movements_deleted} stock movements related to sales.")

        # 4. Delete Invoices (factures)
        cursor.execute("DELETE FROM factures")
        invoices_deleted = cursor.rowcount
        print(f"Deleted {invoices_deleted} invoices.")

        conn.commit()
        print("Data deletion committed.")

        # 5. Recalculate Global Stock
        print("Recalculating global stock...")
        
        # Reset stock to initial stock first
        cursor.execute("UPDATE products SET stock_actuel = stock_initial")
        print("Reset all products to stock_initial.")

        # Add amounts from Receptions (only those confirmed/verified if applicable, but usually all receptions add to stock)
        # Note: In this system, receptions seem to be the primary source of adding stock besides initial.
        # We need to be careful if 'receptions' update stock directly or via movements.
        # The logic.py usually creates a movement for receptions. 
        # But since we kept reception movements (we only deleted sales movements), check if we should trust movements or rebuild.
        
        # Safest approach: 
        # 1. Clear ALL stock movements? No, we want to keep Reception movements.
        # 2. But if we reset stock_actuel to stock_initial, we need to re-apply Reception movements.
        # 3. OR we assume 'stock_movements' for Receptions are still valid and we just sum them up?
        
        # Let's check logic.py approach: 'recalculate_global_stock'
        # It resets to initial, then iterates movements.
        
        # Since I deleted sales movements, the remaining movements should be Receptions and other manual adjustments.
        # So I can just re-sum the remaining movements.
        
        # However, to be absolutely sure, let's recalculate from base data if possible.
        # But 'stock_movements' is the audit trail.
        # If I only deleted sales movements, the remaining movements are valid Receptions/Adjustments.
        
        # Let's reset stock_actuel to stock_initial + Sum(movements)
        
        # Get all products
        cursor.execute("SELECT id, stock_initial FROM products")
        products = cursor.fetchall()
        
        for prod_id, initial in products:
            cursor.execute("SELECT SUM(quantite) FROM stock_movements WHERE product_id = ?", (prod_id,))
            result = cursor.fetchone()[0]
            movement_sum = result if result else 0.0
            
            new_stock = initial + movement_sum
            
            cursor.execute("UPDATE products SET stock_actuel = ? WHERE id = ?", (new_stock, prod_id))
            print(f"Product ID {prod_id}: Initial {initial} + Movs {movement_sum} = New Stock {new_stock}")

        conn.commit()
        print("Stock recalculation complete.")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    reset_invoices()
