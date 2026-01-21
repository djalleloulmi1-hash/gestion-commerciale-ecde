import sqlite3
import datetime

def debug_product_38():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    # 1. Total Sum check
    cursor.execute("SELECT SUM(quantite) FROM stock_movements WHERE product_id = 38")
    stock_sum = cursor.fetchone()[0]
    print(f"DEBUG: P38 Current Sum = {stock_sum}")
    
    # 2. List all movements
    cursor.execute("SELECT id, type_mouvement, quantite, date_mouvement, reference_document FROM stock_movements WHERE product_id = 38 ORDER BY date_mouvement")
    mvs = cursor.fetchall()
    
    print("--- Detailed Movements P38 ---")
    for m in mvs:
        print(f"ID: {m[0]} | Type: {m[1]} | Qty: {m[2]} | Date: {m[3]} | Ref: {m[4]}")
        
    conn.close()

if __name__ == "__main__":
    debug_product_38()
