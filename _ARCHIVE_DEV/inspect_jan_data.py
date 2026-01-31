import sqlite3
import pandas as pd
from database import DatabaseManager

def inspect_data():
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    start_date = '2026-01-10'
    end_date = '2026-01-14'
    
    print(f"--- Receptions ({start_date} to {end_date}) ---")
    cursor.execute("""
        SELECT r.id, r.date_reception, r.numero, r.lieu_livraison, r.quantite_recue, p.nom as product
        FROM receptions r
        JOIN products p ON r.product_id = p.id
        WHERE r.date_reception BETWEEN ? AND ?
    """, (start_date, end_date))
    
    receptions = cursor.fetchall()
    for r in receptions:
        print(dict(r))
        
    print(f"\n--- Sales (Factures) ({start_date} to {end_date}) ---")
    cursor.execute("""
        SELECT f.id, f.date_facture, f.numero, f.type_document, lf.quantite, p.nom as product
        FROM factures f
        JOIN lignes_facture lf ON f.id = lf.facture_id
        JOIN products p ON lf.product_id = p.id
        WHERE f.date_facture BETWEEN ? AND ? AND f.type_document = 'Facture' AND f.statut != 'Annulée'
    """, (start_date, end_date))
    
    sales = cursor.fetchall()
    for s in sales:
        print(dict(s))

if __name__ == "__main__":
    inspect_data()
