import sqlite3
from database import DatabaseManager

def inspect_jan_11():
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    start_date = '2026-01-11'
    end_date = '2026-01-11'
    
    print(f"--- Receptions ({start_date}) ---")
    cursor.execute("""
        SELECT r.id, r.date_reception, r.numero, r.lieu_livraison, r.quantite_recue, r.product_id, p.nom as product
        FROM receptions r
        JOIN products p ON r.product_id = p.id
        WHERE r.date_reception = ?
    """, (start_date,))
    
    for r in cursor.fetchall():
        print(dict(r))
        
    print(f"\n--- Sales ({start_date}) ---")
    cursor.execute("""
        SELECT f.id, f.date_facture, f.numero, lf.quantite, lf.product_id, p.nom as product
        FROM factures f
        JOIN lignes_facture lf ON f.id = lf.facture_id
        JOIN products p ON lf.product_id = p.id
        WHERE f.date_facture = ? AND f.type_document = 'Facture' AND f.statut != 'Annulée'
    """, (start_date,))
    
    for s in cursor.fetchall():
        print(dict(s))

if __name__ == "__main__":
    inspect_jan_11()
