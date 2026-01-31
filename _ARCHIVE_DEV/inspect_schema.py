
import sqlite3

conn = sqlite3.connect('gestion.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(factures)")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
