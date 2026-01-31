import sqlite3
import os
from database import get_db
from logic import get_logic
from datetime import datetime

def verify_manual_contract():
    print("Verifying Manual Contract Entry...")
    
    # 1. Reset/Ensure DB Schema
    db = get_db()
    conn = db._get_connection()
    c = conn.cursor()
    
    # Check column
    c.execute("PRAGMA table_info(factures)")
    cols = [info[1] for info in c.fetchall()]
    if 'contrat_code' not in cols:
        print("FAIL: contrat_code column missing in factures.")
        return
    print("PASS: contrat_code column exists.")
    
    # 2. Create Invoice with Manual Contract via Logic
    logic = get_logic()
    
    # Ensure client and product exist
    try:
        # Create Dummy Client
        client_id = db.create_client(
            raison_sociale="Client Test Manual",
            adresse="Adre", rc="1", nis="1", nif="1", article_imposition="1"
        )
    except Exception:
        # Might exist or constraints, try fetching first
        clients = db.get_all_clients()
        if clients:
            client_id = clients[0]['id']
        else:
            print("FAIL: Could not create or find client")
            return

    # Create Dummy Product
    try:
        prod_id = db.create_product(nom="Product Test Manual", unite="U", prix_actuel=100, stock_actuel=1000, stock_initial=1000)
        product = db.get_product_by_id(prod_id)
    except Exception:
        products = db.get_all_products()
        if products:
            product = products[0]
            # Force update stock to ensure enough for test
            db.update_product_stock(product['id'], 1000)
        else:
            print("FAIL: No products available")
            return
            
    lignes = [{
        'product_id': product['id'],
        'quantite': 10,
        'prix_unitaire': 100,
        'montant': 1000
    }]
    
    manual_contract = "CONTRAT-MANUEL-TEST-2025"
    
    success, msg, fid = logic.create_invoice_with_validation(
        type_document='Facture',
        client_id=client_id,
        lignes=lignes,
        user_id=1,
        type_vente='Au comptant',
        mode_paiement='Espèces',
        contrat_code=manual_contract # The key parameter we added
    )
    
    if success:
        print("PASS: Invoice created successfully.")
        
        # 3. Verify Data Persistence
        # Force select
        c.execute("SELECT contrat_code FROM factures WHERE id=?", (fid,))
        stored_code = c.fetchone()[0]
        
        if stored_code == manual_contract:
            print(f"PASS: Contract Code '{stored_code}' persisted correctly.")
        else:
            print(f"FAIL: Contract Code mismatch. Expected '{manual_contract}', got '{stored_code}'")
            
    else:
        print(f"FAIL: Invoice creation failed: {msg}")

if __name__ == "__main__":
    verify_manual_contract()
