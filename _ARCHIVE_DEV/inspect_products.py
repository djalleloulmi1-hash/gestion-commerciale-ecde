import sqlite3

DB_PATH = "gestion_commerciale.db"

def list_products():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, code_produit, active, parent_stock_id, stock_actuel FROM products")
    rows = cursor.fetchall()
    
    print(f"{'ID':<5} | {'Nom':<30} | {'Code':<10} | {'Active':<6} | {'Parent':<6} | {'Stock':<10}")
    print("-" * 80)
    for row in rows:
        print(f"{row['id']:<5} | {row['nom']:<30} | {str(row['code_produit']):<10} | {row['active']:<6} | {str(row['parent_stock_id']):<6} | {row['stock_actuel']:<10}")
    conn.close()

if __name__ == "__main__":
    list_products()
