import sqlite3
from database import DatabaseManager

def inspect_receptions():
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    start_date = '2026-01-12'
    end_date = '2026-01-12'
    
    print(f"--- Receptions ({start_date} to {end_date}) for CEMII ---")
    cursor.execute("""
        SELECT r.id, r.date_reception, r.numero, r.lieu_livraison, r.quantite_recue, p.nom as product
        FROM receptions r
        JOIN products p ON r.product_id = p.id
        WHERE r.date_reception BETWEEN ? AND ?
    """, (start_date, end_date))
    
    receptions = cursor.fetchall()
    if not receptions:
        print("No receptions found for this date.")
    for r in receptions:
        print(dict(r))

if __name__ == "__main__":
    inspect_receptions()
