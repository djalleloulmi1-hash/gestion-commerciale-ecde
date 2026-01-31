
import sqlite3
import os

DB_PATH = os.path.join("c:\\GICA_PROJET", "gestion_commerciale.db")

def check_data():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check raw data
        cursor.execute("SELECT COUNT(*) FROM receptions")
        total = cursor.fetchone()[0]
        print(f"Total receptions: {total}")
        
        cursor.execute("SELECT transporteur, COUNT(*) FROM receptions GROUP BY transporteur")
        rows = cursor.fetchall()
        print("Transporteur distribution:")
        for r in rows:
            print(f"'{r[0]}': {r[1]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
