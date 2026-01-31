
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def check_dates_updated():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Target: 12/01/2026 -> 2026-01-12
    target_date = "2026-01-12" 
    
    print(f"\n--- Checking for date: {target_date} ---")
    cursor.execute("SELECT COUNT(*), date_reception FROM receptions WHERE date_reception = ? GROUP BY date_reception", (target_date,))
    rows_rec = cursor.fetchall()
    print(f"Receptions to update: {rows_rec}")
    
    cursor.execute("SELECT COUNT(*), date_facture FROM factures WHERE date_facture = ? GROUP BY date_facture", (target_date,))
    rows_fac = cursor.fetchall()
    print(f"Factures to update: {rows_fac}")

    print("\n--- Searching for Clients like '%TEST%' ---")
    cursor.execute("SELECT id, code_client, raison_sociale FROM clients WHERE raison_sociale LIKE '%TEST%' OR code_client LIKE '%TEST%'")
    clients = cursor.fetchall()
    print(f"Found {len(clients)} clients:")
    for c in clients:
        print(f" - ID: {c[0]}, Code: {c[1]}, Name: {c[2]}")
        
        # Check invoices for this client
        cursor.execute("SELECT id, numero, date_facture FROM factures WHERE client_id = ?", (c[0],))
        inv = cursor.fetchall()
        print(f"   Invoices ({len(inv)}): {[i[1] for i in inv]}")

    conn.close()

if __name__ == "__main__":
    check_dates_updated()
