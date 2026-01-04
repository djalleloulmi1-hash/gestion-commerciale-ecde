
import sqlite3
import os

db_path = "gestion_commerciale.db"

def inspect():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("--- INVOICES ---")
    c.execute("SELECT id, numero, date_facture, type_document, statut, montant_ttc FROM factures")
    rows = c.fetchall()
    for r in rows:
        print(dict(r))

    print("\n--- INVOICE LINES (Sample) ---")
    c.execute("SELECT f.numero, l.quantite, l.product_id FROM lignes_facture l JOIN factures f ON l.facture_id = f.id LIMIT 10")
    for r in rows:
        pass # just checking join

    conn.close()

if __name__ == "__main__":
    inspect()
