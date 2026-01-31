
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def check_types():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT type_mouvement FROM stock_movements")
        rows = cursor.fetchall()
        print("Movement Types found:")
        for row in rows:
            print(f"- {row[0]}")
    except Exception as e:
        print(e)
    finally:
        conn.close()

if __name__ == "__main__":
    check_types()
