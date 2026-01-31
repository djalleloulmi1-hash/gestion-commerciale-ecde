import sqlite3

DB_NAME = "gestion_commerciale.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

print("--- statut_facture ---")
try:
    c.execute("SELECT DISTINCT statut_facture FROM factures")
    print(c.fetchall())
except Exception as e:
    print(e)
    
print("\n--- mode_paiement ---")
try:
    c.execute("SELECT DISTINCT mode_paiement FROM factures")
    print(c.fetchall())
except Exception as e:
    print(e)

conn.close()
