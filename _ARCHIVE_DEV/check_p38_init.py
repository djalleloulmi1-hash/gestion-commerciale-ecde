import sqlite3

def check_base_stock():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    # Check Product 38
    cursor.execute("SELECT id, nom, stock_initial FROM products WHERE id=38")
    p = cursor.fetchone()
    if p:
        print(f"Product {p[0]} ({p[1]}): Stock Initial = {p[2]}")
    else:
        print("Product 38 not found")
        
    conn.close()

if __name__ == "__main__":
    check_base_stock()
