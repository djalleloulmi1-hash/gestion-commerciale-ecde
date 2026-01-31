
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def update_dates():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check existing records to be updated
        cursor.execute("SELECT id, numero, date_facture FROM factures WHERE date_facture = '2026-01-14'")
        to_update = cursor.fetchall()
        
        print(f"Found {len(to_update)} invoices with date 2026-01-14:")
        for row in to_update:
            print(f" - ID: {row[0]}, Num: {row[1]}, Date: {row[2]}")

        if not to_update:
            print("No invoices found to update.")
            return

        # Perform update
        cursor.execute("UPDATE factures SET date_facture = '2026-01-12' WHERE date_facture = '2026-01-14'")
        conn.commit()
        
        print(f"\nSuccessfully updated {cursor.rowcount} invoices to 2026-01-12.")
        
        # Verify
        cursor.execute("SELECT id, numero, date_facture FROM factures WHERE date_facture = '2026-01-12' AND id IN ({})".format(','.join([str(r[0]) for r in to_update])))

        verified = cursor.fetchall()
        print(f"Verified {len(verified)} updated records.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_dates()
