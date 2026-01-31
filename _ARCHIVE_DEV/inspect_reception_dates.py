import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def inspect_dates():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, date_reception FROM receptions LIMIT 10")
        rows = cursor.fetchall()
        
        print("Sample dates in DB:")
        for row in rows:
            print(f"ID: {row[0]}, Date: {row[1]}")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_dates()
