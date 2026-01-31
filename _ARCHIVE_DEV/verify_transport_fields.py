import sys
import os
import sqlite3
from datetime import datetime

# Adjust path to import modules
sys.path.append(os.getcwd())

from database import DatabaseManager
from logic import BusinessLogic

def verify():
    print("Verifying Transport Fields Implementation...")
    
    # 1. Initialize DB and Logic
    db = DatabaseManager('gestion_commerciale.db')
    logic = BusinessLogic(db)
    
    # 2. Check Columns
    print("Checking 'factures' table columns...")
    conn = db._get_connection()
    c = conn.cursor()
    c.execute("PRAGMA table_info(factures)")
    columns = [row[1] for row in c.fetchall()]
    
    required = ['chauffeur', 'matricule_tracteur', 'matricule_remorque']
    missing = [col for col in required if col not in columns]
    
    if missing:
        print(f"FAILED: Missing columns: {missing}")
        return
    else:
        print("SUCCESS: All columns present.")

    # 3. Test Insertion via Logic
    print("Testing create_invoice_with_validation...")
    
    # Create dummy client if needed or get first
    c.execute("SELECT id FROM clients LIMIT 1")
    row = c.fetchone()
    if not row:
        print("Creating dummy client...")
        db.create_client("Test Client", "Add", "Tel", "000000", 0)
        c.execute("SELECT id FROM clients LIMIT 1")
        client_id = c.fetchone()[0]
    else:
        client_id = row[0]
        
    # Get a product
    c.execute("SELECT id, prix_actuel FROM products LIMIT 1")
    p_row = c.fetchone()
    if not p_row:
         print("Creating dummy product...")
         db.create_product("Prod Test", "U", "CODE001", "Ciment", 100, 100, 120, 19, 1)
         c.execute("SELECT id, prix_actuel FROM products LIMIT 1")
         p_row = c.fetchone()
    
    pid, price = p_row
    
    lignes = [{
        'product_id': pid,
        'quantite': 1,
        'prix_unitaire': price,
        'montant': price
    }]
    
    # Test Data
    chauffeur = "John Doe"
    mat_trac = "12345-111-16"
    mat_rem = "54321-222-16"
    
    success, msg, fid = logic.create_invoice_with_validation(
        type_document='Facture',
        client_id=client_id,
        lignes=lignes,
        type_vente='Au comptant',
        mode_paiement='Espèces',
        chauffeur=chauffeur,
        matricule_tracteur=mat_trac,
        matricule_remorque=mat_rem
    )
    
    if not success:
        print(f"FAILED: Logic call failed: {msg}")
        return
        
    print(f"Invoice created with ID: {fid}")
    
    # 4. Verify Data in DB
    print("Verifying inserted data...")
    facture = db.get_facture_by_id(fid)
    
    print(f"Chauffeur: {facture.get('chauffeur')} (Expected: {chauffeur})")
    print(f"Matricule Tracteur: {facture.get('matricule_tracteur')} (Expected: {mat_trac})")
    print(f"Matricule Remorque: {facture.get('matricule_remorque')} (Expected: {mat_rem})")
    
    if (facture.get('chauffeur') == chauffeur and 
        facture.get('matricule_tracteur') == mat_trac and 
        facture.get('matricule_remorque') == mat_rem):
        print("SUCCESS: Data verification passed!")
    else:
        print("FAILED: Data mismatch.")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
