import sqlite3

DB_PATH = "gestion_commerciale.db"

def check_movements():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Checking Movements for Product ID 24:")
    cursor.execute("SELECT * FROM stock_movements WHERE product_id = 24")
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print(dict(row))
    else:
        print("No movements for Product 24.")
    conn.close()

if __name__ == "__main__":
    check_movements()
