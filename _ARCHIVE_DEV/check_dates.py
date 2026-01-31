
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def check_dates():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- Receptions (Sample) ---")
    cursor.execute("SELECT date_reception FROM receptions LIMIT 5")
    for row in cursor.fetchall():
        print(f"Reception Date: '{row[0]}'")

    print("\n--- Factures (Sample) ---")
    cursor.execute("SELECT date_facture FROM factures LIMIT 5")
    for row in cursor.fetchall():
        print(f"Facture Date: '{row[0]}'")

    print("\n--- Target Records Check ---")
    # Check for the specific dates requested
    target_date = "12/01/2026" 
    
    cursor.execute("SELECT COUNT(*) FROM receptions WHERE date_reception = ?", (target_date,))
    count_rec = cursor.fetchone()[0]
    print(f"Receptions to update (date='{target_date}'): {count_rec}")
    
    cursor.execute("SELECT COUNT(*) FROM factures WHERE date_facture = ?", (target_date,))
    count_fac = cursor.fetchone()[0]
    print(f"Factures to update (date='{target_date}'): {count_fac}")

    print("\n--- Test Client Invoices Check ---")
    cursor.execute("""
        SELECT f.id, f.numero, c.raison_sociale 
        FROM factures f 
        JOIN clients c ON f.client_id = c.id 
        WHERE c.raison_sociale = 'TEST CLIENT'
    """)
    rows = cursor.fetchall()
    print(f"Invoices for 'TEST CLIENT': {len(rows)}")
    for row in rows:
        print(f" - ID: {row[0]}, Num: {row[1]}, Client: {row[2]}")

    conn.close()

if __name__ == "__main__":
    check_dates()
