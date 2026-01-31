import os
import sqlite3
import datetime
from database import DatabaseManager
from logic import BusinessLogic

TEST_DB = "simulation_test.db"

def run_simulation():
    print("=== STARTING SIMULATION ===")
    
    # 1. Setup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    db_manager = DatabaseManager(TEST_DB)
    
    # 1.5 Inject Test DB into global singleton
    import database
    database._db_instance = db_manager
    
    logic = BusinessLogic()
    db = db_manager # Local alias
    user_id = 1 # Admin
    
    anomalies = []
    
    try:
        # 2. Create Product
        print("[1] Creating Product...")
        db.create_product(nom="Ciment Test", unite="Sacs", code_produit="P001", 
                         stock_initial=10.0, cout_revient=0.0, prix_actuel=1000.0, stock_actuel=0.0, created_by=user_id)
        # prod = db.get_product_by_code("P001") # Method does not exist
        products = db.get_all_products()
        prod = next((p for p in products if p['code_produit'] == "P001"), None)
        if not prod: raise Exception("Product creation failed")
        
        # 3. Reception (Stock Entry)
        print("[2] Receiving Stock...")
        # Simulate params for reception
        db.create_reception(2026, "2026-01-01", "Chauf1", "MAT1", "Trans1", "Sur Stock", "", 
                           prod['id'], 100.0, 100.0, "MAT_REM1", "BT01", "2026-01-01", "FAC_REC01", "2026-01-01", "", user_id)
        
        # Logic process reception updates stock?
        # logic.process_reception usually handles this? Verify logic.py
        # Assuming simple DB triggers or logic calls needed. 
        # Checking logic.process_reception interaction if strictly required. 
        # In this app, it seems UI calls db.create_reception then logic.process?? No, UI handles it.
        # Let's check stock.
        prod = db.get_product_by_id(prod['id'])
        if prod['stock_actuel'] != 100.0:
            # Maybe logic.process_reception wasn't called.
            # UI calls: rid = db.create_reception(...); get_logic().process_reception(rid, ...)
            # We must simulate that.
            receptions = db.get_all_receptions()
            rid = receptions[0]['id']
            logic.process_reception(rid, user_id)
            
            prod = db.get_product_by_id(prod['id'])
            if prod['stock_actuel'] != 100.0:
                 anomalies.append(f"Stock mismatch after reception. Expected 100, got {prod['stock_actuel']}")

        # 4. Create Client
        print("[3] Creating Client...")
        db.create_client("Client Test", "Adresse Test", "0555", "RC1", "NIF1", "NIS1", "AI1", 0.0, 0.0, created_by=user_id)
        clients = db.get_all_clients()
        client = clients[0]

        # 5. Create Invoice (Sale)
        print("[4] Creating Invoice...")
        # Create draft
        fid = db.create_facture(
            type_document="Facture", annee=2026, date_facture="2026-01-02", 
            client_id=client['id'], 
            type_vente="Vente", mode_paiement="Especes",
            created_by=user_id
        )
        # Add line
        # Add line using correct method
        db.add_ligne_facture(fid, prod['id'], 10.0, 1200.0) # 10 units @ 1200
        # Finalize
        logic.process_facture_stock(fid, user_id)
        # Manually update totals since we bypassed logic.create_invoice_with_validation
        db.update_facture_totals(fid, 12000.0, 2280.0, 14280.0)
        
        # Check Stock (Should be 90)
        prod = db.get_product_by_id(prod['id'])
        if prod['stock_actuel'] != 90.0:
             anomalies.append(f"Stock mismatch after sale. Expected 90, got {prod['stock_actuel']}")
             
        # Check Client Balance
        bal = logic.calculate_client_balance(client['id'])
        # Solde = (Report + Paiements + Avoirs) - Factures
        # 0 + 0 + 0 - 14280 = -14280
        if abs(bal['solde'] - (-14280.0)) > 0.01:
             anomalies.append(f"Client Balance mismatch. Expected -14280, got {bal['solde']}")

        # 6. Payment
        print("[5] Adding Payment...")
        db.create_paiement(date_paiement="2026-01-03", client_id=client['id'], montant=5000.0, 
                          mode_paiement="Espèces", reference="REF_PAY1", banque="BNA", created_by=user_id)
        # Validate payment (if needed? Status is 'En attente' usually counts? Logic says 'active_only'?)
        # Logic usually counts all payments unless cancelled?
        
        bal = logic.calculate_client_balance(client['id'])
        # -14280 + 5000 = -9280
        if abs(bal['solde'] - (-9280.0)) > 0.01:
             anomalies.append(f"Client Balance mismatch after payment. Expected -9280, got {bal['solde']}")

        # 7. Avoir (Credit Note) - Full refund of invoice
        print("[6] Creating Credit Note (Avoir)...")
        aid = db.create_facture(
             type_document="Avoir", annee=2026, date_facture="2026-01-04",
             client_id=client['id'],
             facture_origine_id=fid,
             created_by=user_id
        )
        db.add_ligne_facture(aid, prod['id'], 10.0, 1200.0)
        logic.process_facture_stock(aid, user_id)
        db.update_facture_totals(aid, 12000.0, 2280.0, 14280.0)

        # Check Stock (Should be back to 100)
        prod = db.get_product_by_id(prod['id'])
        if prod['stock_actuel'] != 100.0:
             anomalies.append(f"Stock mismatch after Avoir. Expected 100, got {prod['stock_actuel']}")

        # Check Client Balance
        # Solde = (0 + 5000 + 14280) - 14280 = 5000
        bal = logic.calculate_client_balance(client['id'])
        if abs(bal['solde'] - 5000.0) > 0.01:
             anomalies.append(f"Client Balance mismatch after Avoir. Expected 5000, got {bal['solde']}")

    except Exception as e:
        anomalies.append(f"CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== SIMULATION REPORT ===")
    if anomalies:
        print(f"FAILED. Found {len(anomalies)} anomalies:")
        for a in anomalies:
            print(f"- {a}")
    else:
        print("SUCCESS. All logic checks passed.")
    
    # Cleanup
    db.close()
    if os.path.exists(TEST_DB):
        try: os.remove(TEST_DB)
        except: pass

if __name__ == "__main__":
    run_simulation()
