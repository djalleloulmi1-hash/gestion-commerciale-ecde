import sqlite3
from database import DB_NAME

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Check distinct values
print("\n--- Distinct etat_paiement ---")
try:
    c.execute("SELECT DISTINCT etat_paiement FROM factures")
    rows = c.fetchall()
    for row in rows:
        print(row)
except Exception as e:
    print(e)
    
conn.close()
