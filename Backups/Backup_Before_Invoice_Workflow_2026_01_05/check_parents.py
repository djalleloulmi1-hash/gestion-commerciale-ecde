
import sqlite3
import os

db_path = "gestion_commerciale.db"
if not os.path.exists(db_path):
    print("DB not found")
    exit()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- Products & Parent Stock ---")
cursor.execute("SELECT id, nom, parent_stock_id, stock_actuel FROM products")
products = cursor.fetchall()
for p in products:
    parent_info = "None"
    if p['parent_stock_id']:
        cursor.execute("SELECT nom FROM products WHERE id=?", (p['parent_stock_id'],))
        parent = cursor.fetchone()
        parent_info = f"{p['parent_stock_id']} ({parent['nom'] if parent else 'NOT FOUND'})"
        
    print(f"ID: {p['id']}, Nom: {p['nom']}, Parent: {parent_info}, Stock: {p['stock_actuel']}")

conn.close()
