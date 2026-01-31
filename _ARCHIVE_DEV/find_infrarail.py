import sqlite3

def find_invoice():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    print("Searching for INFRARAIL invoices...")
    cursor.execute("""
        SELECT f.id, f.numero, f.date_facture, c.raison_sociale, lf.product_id, lf.quantite, lf.prix_unitaire 
        FROM factures f 
        JOIN clients c ON f.client_id = c.id 
        JOIN lignes_facture lf ON f.id = lf.facture_id 
        WHERE c.raison_sociale LIKE '%INFRARAIL%'
    """)
    results = cursor.fetchall()
    
    for row in results:
        fid, num, date, client, pid, qty, price = row
        print(f"Facture {num} (ID: {fid}) - Client: {client} - Date: {date} - Qty: {qty} - Price: {price}")
        
    conn.close()

if __name__ == "__main__":
    find_invoice()
