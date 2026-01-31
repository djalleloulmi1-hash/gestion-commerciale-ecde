import sqlite3

def check_zeros():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    print("--- Searching for ANY invoice line with Quantity = 0 ---")
    cursor.execute("""
        SELECT f.id, f.numero, c.raison_sociale, lf.quantite, lf.prix_unitaire
        FROM factures f 
        JOIN clients c ON f.client_id = c.id 
        JOIN lignes_facture lf ON f.id = lf.facture_id 
        WHERE lf.quantite = 0
    """)
    results = cursor.fetchall()
    
    if not results:
        print("No lines with Quantity = 0 found.")
    else:
        for row in results:
             print(f"FOUND: Facture {row[1]} - Client {row[2]} - Qty: {row[3]}")

    print("\n--- Detailed INFRARAIL Check ---")
    cursor.execute("""
        SELECT f.id, f.numero, f.date_facture, c.raison_sociale, lf.product_id, lf.quantite, lf.prix_unitaire 
        FROM factures f 
        JOIN clients c ON f.client_id = c.id 
        JOIN lignes_facture lf ON f.id = lf.facture_id 
        WHERE c.raison_sociale LIKE '%INFRARAIL%'
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    check_zeros()
