
import sqlite3
import os

db_path = "gestion_commerciale.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT count(*) FROM products")
    print(f"Product count: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT id, nom FROM products")
    for r in cursor.fetchall():
        print(f"P: {r[0]} - {r[1]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
