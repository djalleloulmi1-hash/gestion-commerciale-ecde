
import sqlite3

def verify_reset():
    conn = sqlite3.connect("gestion_commerciale.db")
    cursor = conn.cursor()
    
    tables = ["factures", "clients", "receptions", "products"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count}")
        
    cursor.execute("SELECT nom, stock_actuel FROM products LIMIT 5")
    print("\nSample Stock:")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    conn.close()

if __name__ == "__main__":
    verify_reset()
