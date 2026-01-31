
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def verify_changes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- Verification Results ---")

    # 1. Check old date (should be 0)
    old_date = "2026-01-12"
    cursor.execute("SELECT COUNT(*) FROM receptions WHERE date_reception = ?", (old_date,))
    count_old_rec = cursor.fetchone()[0]
    print(f"Receptions with old date ({old_date}): {count_old_rec} (Expected: 0)")

    cursor.execute("SELECT COUNT(*) FROM factures WHERE date_facture = ?", (old_date,))
    count_old_fac = cursor.fetchone()[0]
    print(f"Factures with old date ({old_date}): {count_old_fac} (Expected: 0)")

    # 2. Check new date (should be present)
    new_date = "2026-01-11"
    cursor.execute("SELECT COUNT(*) FROM receptions WHERE date_reception = ?", (new_date,))
    count_new_rec = cursor.fetchone()[0]
    print(f"Receptions with new date ({new_date}): {count_new_rec}")

    cursor.execute("SELECT COUNT(*) FROM factures WHERE date_facture = ?", (new_date,))
    count_new_fac = cursor.fetchone()[0]
    print(f"Factures with new date ({new_date}): {count_new_fac}")

    # 3. Check Test Client Invoices (should be 0)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM factures f 
        JOIN clients c ON f.client_id = c.id 
        WHERE c.raison_sociale LIKE 'Test Client'
    """)
    count_test = cursor.fetchone()[0]
    print(f"Invoices for 'Test Client': {count_test} (Expected: 0)")
    
    conn.close()

if __name__ == "__main__":
    verify_changes()
