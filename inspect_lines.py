
import sqlite3

def check_lines():
    conn = sqlite3.connect("gestion_commerciale.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("--- INVOICE LINES DETAIL ---")
    c.execute("""
        SELECT f.type_document, f.numero, l.quantite, l.montant 
        FROM lignes_facture l 
        JOIN factures f ON l.facture_id = f.id
        LIMIT 10
    """)
    for r in c.fetchall():
        print(f"Type: {r['type_document']}, Num: {r['numero']}, Qty: {r['quantite']}, Montant: {r['montant']}")

if __name__ == "__main__":
    check_lines()
