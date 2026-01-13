
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def modify_database():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting Database Modification...")
        
        # 1. Update Receptions
        target_date = '2026-01-12'
        new_date = '2026-01-11'
        
        cursor.execute("SELECT COUNT(*) FROM receptions WHERE date_reception = ?", (target_date,))
        count = cursor.fetchone()[0]
        print(f"Found {count} receptions with date {target_date}")
        
        if count > 0:
            cursor.execute("UPDATE receptions SET date_reception = ? WHERE date_reception = ?", (new_date, target_date))
            print(f"Updated {cursor.rowcount} receptions to {new_date}")
            
        # 2. Update Factures
        cursor.execute("SELECT COUNT(*) FROM factures WHERE date_facture = ?", (target_date,))
        count = cursor.fetchone()[0]
        print(f"Found {count} factures with date {target_date}")
        
        if count > 0:
            cursor.execute("UPDATE factures SET date_facture = ? WHERE date_facture = ?", (new_date, target_date))
            print(f"Updated {cursor.rowcount} factures to {new_date}")
            
        # 3. Delete Test Client Invoices
        # Find clients to target first
        cursor.execute("SELECT id, raison_sociale FROM clients WHERE raison_sociale LIKE 'Test Client'")
        clients = cursor.fetchall()
        client_ids = [c[0] for c in clients]
        
        if client_ids:
            placeholders = ','.join('?' for _ in client_ids)
            # Count invoices first
            cursor.execute(f"SELECT COUNT(*) FROM factures WHERE client_id IN ({placeholders})", client_ids)
            inv_count = cursor.fetchone()[0]
            print(f"Found {inv_count} invoices for 'Test Client' (IDs: {client_ids})")
            
            if inv_count > 0:
                cursor.execute(f"DELETE FROM factures WHERE client_id IN ({placeholders})", client_ids)
                print(f"Deleted {cursor.rowcount} invoices")
        else:
            print("No 'Test Client' found.")

        conn.commit()
        print("Modification completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        print("Changes rolled back.")
    finally:
        conn.close()

if __name__ == "__main__":
    modify_database()
