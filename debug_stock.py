
import sqlite3
import os

db_path = "gestion_commerciale.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find product
cursor.execute("SELECT * FROM products WHERE nom LIKE '%Vrac%'")
product = cursor.fetchone()

if product:
    print("Product Found:")
    print(dict(product))
    pid = product['id']
    
    print("\nStock Movements:")
    cursor.execute("SELECT * FROM stock_movements WHERE product_id = ?", (pid,))
    movements = cursor.fetchall()
    for m in movements:
        print(dict(m))

    print("\nReceptions:")
    cursor.execute("SELECT * FROM receptions WHERE product_id = ?", (pid,))
    receptions = cursor.fetchall()
    for r in receptions:
        print(dict(r))
else:
    print("Product 'Vrac CRS' not found")

conn.close()
