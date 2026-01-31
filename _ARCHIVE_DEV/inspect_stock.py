
import sqlite3
from database import DatabaseManager

def inspect_movements():
    db = DatabaseManager()
    conn = db._get_connection()
    c = conn.cursor()
    
    print("--- Stock Movements ---")
    c.execute("SELECT id, type_mouvement, quantite, reference_document, created_at FROM stock_movements ORDER BY created_at DESC")
    rows = c.fetchall()
    for row in rows:
        print(list(row))

if __name__ == "__main__":
    inspect_movements()
