import sqlite3
from database import DatabaseManager

def check_products():
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    print("--- Products List ---")
    cursor.execute("SELECT id, nom, code_produit, stock_initial, stock_actuel FROM products")
    products = cursor.fetchall()
    for p in products:
        print(dict(p))

if __name__ == "__main__":
    check_products()
