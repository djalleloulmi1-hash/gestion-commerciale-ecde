import sqlite3

def check_infrarail_dependencies():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    # 1. Invoice Content
    print("--- INVOICE FAC-0020-2026 ---")
    cursor.execute("SELECT * FROM factures WHERE numero = 'FAC-0020-2026'")
    facture = cursor.fetchone()
    print(f"Facture Data: {facture}")
    
    if not facture:
        print("Facture not found!")
        return

    fid = facture[0] # Assumes ID is first col
    
    # 2. Line Items
    print("\n--- LINE ITEMS ---")
    cursor.execute("SELECT * FROM lignes_facture WHERE facture_id = ?", (fid,))
    lines = cursor.fetchall()
    for l in lines:
        print(f"Line: Product={l[2]}, Qty={l[3]}, Price={l[4]}")

    # 3. Stock Movements
    print("\n--- STOCK MOVEMENTS ---")
    cursor.execute("SELECT * FROM stock_movements WHERE document_id = ? AND type_mouvement IN ('Vente', 'Retour Avoir')", (fid,))
    mvs = cursor.fetchall()
    for m in mvs:
        print(f"Movement: ID={m[0]}, Type={m[2]}, Qty={m[3]}, Ref={m[4]}")
        
    conn.close()

if __name__ == "__main__":
    check_infrarail_dependencies()
