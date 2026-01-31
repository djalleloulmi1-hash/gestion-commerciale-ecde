import sqlite3

DB_PATH = "gestion_commerciale.db"

def list_receptions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Listing ALL Receptions:")
    cursor.execute("SELECT id, numero, product_id, quantite_recue FROM receptions")
    rows = cursor.fetchall()
    
    for row in rows:
        print(dict(row))
        
    print(f"Total rows: {len(rows)}")
    conn.close()

if __name__ == "__main__":
    list_receptions()
