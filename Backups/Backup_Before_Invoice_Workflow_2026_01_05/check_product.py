import sqlite3

DB_PATH = "gestion_commerciale.db"

def check_product():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Checking Product ID 12:")
    cursor.execute("SELECT * FROM products WHERE id = 12")
    row = cursor.fetchone()
    if row:
        print(dict(row))
    else:
        print("Product 12 not found")
    conn.close()

if __name__ == "__main__":
    check_product()
