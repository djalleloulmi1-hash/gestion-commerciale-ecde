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
        
        # Update 11/01/2026 -> 10/01/2026
        target_date_1 = "2026-01-11"
        new_date_1 = "2026-01-10"
        
        cursor.execute("SELECT COUNT(*) FROM receptions WHERE date_reception = ?", (target_date_1,))
        count_1 = cursor.fetchone()[0]
        
        cursor.execute("UPDATE receptions SET date_reception = ? WHERE date_reception = ?", (new_date_1, target_date_1))
        affected_1 = cursor.rowcount
        
        print(f"Update 1: Changed {affected_1} rows from {target_date_1} to {new_date_1} (Found {count_1})")

        # Update 13/01/2026 -> 12/01/2026
        target_date_2 = "2026-01-13"
        new_date_2 = "2026-01-12"
        
        cursor.execute("SELECT COUNT(*) FROM receptions WHERE date_reception = ?", (target_date_2,))
        count_2 = cursor.fetchone()[0]
        
        cursor.execute("UPDATE receptions SET date_reception = ? WHERE date_reception = ?", (new_date_2, target_date_2))
        affected_2 = cursor.rowcount
        
        print(f"Update 2: Changed {affected_2} rows from {target_date_2} to {new_date_2} (Found {count_2})")
        
        conn.commit()
        print("Updates committed successfully.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_dates()
