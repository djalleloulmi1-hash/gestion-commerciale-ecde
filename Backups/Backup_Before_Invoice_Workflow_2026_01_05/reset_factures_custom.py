import sqlite3
import os
from database import get_db
from logic import BusinessLogic

def reset_factures():
    print("Starting Invoices Reset...")
    
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Delete Invoice Lines (Cascade should handle, but being explicit)
        cursor.execute("DELETE FROM lignes_facture")
        print("- Cleared lignes_facture")
        
        # 2. Delete Payments linked to Invoices
        # Note: This might leave some payments that were "advances" (no invoice link).
        # We will keep them as they are not "Factures".
        cursor.execute("DELETE FROM paiements WHERE facture_id IS NOT NULL")
        print("- Cleared payments linked to invoices")
        
        # 3. Delete Avoirs (Credit Notes) & Factures
        cursor.execute("DELETE FROM factures")
        print("- Cleared factures")
        
        # 4. Clean Stock Movements related to Sales/Returns
        cursor.execute("DELETE FROM stock_movements WHERE type_mouvement IN ('Vente', 'Retour Avoir')")
        print("- Cleared stock movements for sales")
        
        # 5. Reset Client Balances
        print("- Recalculating client balances...")
        cursor.execute("SELECT id, report_n_moins_1 FROM clients")
        clients = cursor.fetchall()
        
        for client in clients:
            client_id = client['id']
            report = client['report_n_moins_1'] or 0.0
            
            # Sum remaining payments (Advances)
            cursor.execute("SELECT COALESCE(SUM(montant), 0) FROM paiements WHERE client_id = ?", (client_id,))
            total_paiements = cursor.fetchone()[0]
            
            # Debt = Initial Debt - Payments (since invoices are 0)
            new_balance_debt = report - total_paiements
            
            cursor.execute("UPDATE clients SET solde_creance = ? WHERE id = ?", (new_balance_debt, client_id))
            
        print("- Client balances updated")

        # 6. Reset Sequences
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='factures'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='lignes_facture'")
        except:
            pass
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error executing SQL: {e}")
        return

    # 7. Recalculate Stock
    print("- Recalculating stock...")
    bl = BusinessLogic()
    try:
        stats = bl.recalculate_global_stock()
        print(f"  Stock Recalculated: {stats}")
    except Exception as e:
        print(f"Error recalculating stock: {e}")
        
    print("Reset Complete.")

if __name__ == "__main__":
    reset_factures()
