import sqlite3
import datetime

def fix_fac22():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    # Constants
    FAC_NUM = 'FAC-0022-2026'
    FAC_ID = 27
    PRODUCT_ID = 38 # CEMII A-L 42.5 N VRAC
    QTY = 40.0
    PRICE_UNIT = 6214.0 # From FAC-0020
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Insert Line
        print("Inserting Line Item...")
        date_facture = '2026-01-15' # From Image
        montant_ht = QTY * PRICE_UNIT
        montant_tva = montant_ht * 0.19
        montant_ttc = montant_ht + montant_tva
        
        cursor.execute("""
            INSERT INTO lignes_facture (facture_id, product_id, quantite, prix_unitaire, montant)
            VALUES (?, ?, ?, ?, ?)
        """, (FAC_ID, PRODUCT_ID, QTY, PRICE_UNIT, montant_ht))
        
        # 2. Update Header Totals
        print("Updating Invoice Totals...")
        cursor.execute("""
            UPDATE factures 
            SET montant_ht = ?, montant_tva = ?, montant_ttc = ?
            WHERE id = ?
        """, (montant_ht, montant_tva, montant_ttc, FAC_ID))
        
        # 3. Create Stock Movement
        print("Creating Stock Movement...")
        # Check if already exists to be safe
        cursor.execute("SELECT id FROM stock_movements WHERE document_id = ? AND type_mouvement='Vente'", (FAC_ID,))
        if cursor.fetchone():
            print("Movement already exists! Skipping.")
        else:
             cursor.execute("""
                INSERT INTO stock_movements 
                (product_id, type_mouvement, quantite, reference_document, document_id, date_mouvement, created_by, stock_avant, stock_apres)
                VALUES (?, 'Vente', ?, ?, ?, ?, 1, 0, 0)
            """, (PRODUCT_ID, -QTY, FAC_NUM, FAC_ID, date_facture))
             
             # Also update Prod Stock?
             # Logic usually does this. Let's do it to be safe.
             print("Updating Product Stock...")
             cursor.execute("UPDATE products SET stock_actuel = stock_actuel - ? WHERE id = ?", (QTY, PRODUCT_ID))

        conn.commit()
        print("Fix Successful!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    fix_fac22()
