
import sqlite3
import os

DB_PATH = os.path.join("c:\\GICA_PROJET", "gestion_commerciale.db")

def check_column():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(factures)")
        columns = cursor.fetchall()
        
        found = False
        for col in columns:
            # col[1] is name
            if col[1] == 'transporteur':
                found = True
                print(f"Column 'transporteur' FOUND: {col}")
                break
        
        if not found:
            print("Column 'transporteur' NOT FOUND in 'factures' table.")
            print("Existing columns:", [c[1] for c in columns])
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_column()
