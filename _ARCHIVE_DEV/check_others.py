import sqlite3

DB_PATH = "gestion_commerciale.db"

def check_others():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Checking Products for None code:")
    cursor.execute("SELECT * FROM products WHERE code_produit IS NULL OR code_produit = 'None' OR code_produit = ''")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"Product ID {row['id']} has code: {row['code_produit']}")
    else:
        print("No products with None/Empty code.")

    print("\nChecking Clients for None code:")
    cursor.execute("SELECT * FROM clients WHERE code_client IS NULL OR code_client = 'None' OR code_client = ''")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"Client ID {row['id']} has code: {row['code_client']}")
    else:
        print("No clients with None/Empty code.")
        
    conn.close()

if __name__ == "__main__":
    check_others()
