import sqlite3

def recalc_stock():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    PRODUCT_ID = 38
    
    print("--- DIAGNOSTIC ---")
    cursor.execute("SELECT nom, stock_actuel FROM products WHERE id=?", (PRODUCT_ID,))
    row = cursor.fetchone()
    print(f"Product Table Stock: {row[1]}")
    
    cursor.execute("SELECT SUM(quantite) FROM stock_movements WHERE product_id=?", (PRODUCT_ID,))
    calc = cursor.fetchone()[0]
    print(f"Movements Sum: {calc}")
    
    if abs(row[1] - calc) > 0.001:
        print(">>> DISCREPANCY DETECTED! Fixing...")
        cursor.execute("UPDATE products SET stock_actuel = ? WHERE id = ?", (calc, PRODUCT_ID))
        conn.commit()
        print(f"Stock Updated to {calc}")
    else:
        print("Stock is synchronized.")
        
    conn.close()

if __name__ == "__main__":
    recalc_stock()
