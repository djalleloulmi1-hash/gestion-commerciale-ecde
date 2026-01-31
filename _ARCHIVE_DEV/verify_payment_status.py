import sqlite3
import datetime
import os

DB_NAME = os.path.abspath("gestion_commerciale.db")

def check_status(facture_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT numero, etat_paiement, montant_ttc FROM factures WHERE id = ?", (facture_id,))
    row = c.fetchone()
    conn.close()
    if row:
        print(f"Facture {row[0]}: Status='{row[1]}' (Total: {row[2]})")
    else:
        print("Facture not found")
    return row[1] if row else None

# We can't easily query logic from here without full app setup (imports etc might be tricky with UI deps).
# So we will verify manually or mock?
# logic.py imports ui sometimes? No, ui imports logic.
# logic.py imports database, utils, reports.
# It should be safe to import logic if we mock the app/db.

import sys
import os
sys.path.append(os.getcwd())

from database import DatabaseManager
DatabaseManager.DEFAULT_DB_PATH = os.path.abspath("gestion_commerciale.db")
from logic import BusinessLogic

class MockApp:
    def __init__(self):
        self.db = DatabaseManager(DB_NAME)
        self.user = {'id': 1, 'username': 'admin'} # Assume admin exists

app = MockApp()
app = MockApp()
# Initialize logic with default DB (might fail if path issue)
# Hack: Bypass init if needed or just try.
# If get_db() fails, we might need to patch it.
# Let's try init, and if it fails, catch it?
# Or clearer:
try:
    logic = BusinessLogic()
except Exception:
    # If init fails due to path, recreate just to object
    logic = BusinessLogic.__new__(BusinessLogic)
    logic.db = None

# Override with our absolute-path DB
logic.db = app.db

print("--- START VERIFICATION ---")

# 1. Get Existing Client (ID 1 usually exists)
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("SELECT id FROM clients LIMIT 1")
row = c.fetchone()
conn.close()
if not row:
    print("No clients found. Cannot test.")
    exit(1)
client_id = row[0]
print(f"Using Client ID: {client_id}")

try:
    # 2. Create Invoice 'A Terme'
    print("\n[Test 1] Creating Invoice 'A Terme'...")
    # Manually calling create_invoice_with_validation is complex due to args.
    # Let's assume we can call it.
    
    # Get a valid product
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM products LIMIT 1")
    row = c.fetchone()
    conn.close()
    if not row:
        print("No products found in DB. Cannot test invoice.")
        exit(1)
    
    pid = row[0]
    
    # Inject Sock
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE products SET stock_actuel = stock_actuel + 1000 WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    
    lignes = [{'product_id': pid, 'quantite': 1, 'prix_unitaire': 1000, 'montant': 1000}]
    
    success, msg, fid = logic.create_invoice_with_validation(
        type_document='Facture',
        client_id=client_id,
        lignes=lignes,
        user_id=1,
        type_vente='A terme',
        statut_final='Validée'
    )
    
    if not success:
        print(f"Failed to create invoice: {msg}")
        exit(1)
        
    status = check_status(fid)
    if status != 'A Terme':
        print(f"FAILURE: Expected 'A Terme', got '{status}'")
    else:
        print("SUCCESS: Initial status is 'A Terme'")

    # 3. Add Partial Payment (5000)
    print("\n[Test 2] Adding Partial Payment (5000)...")
    logic.create_payment(
        client_id=client_id,
        montant=5000,
        mode_paiement='Espèces',
        facture_id=fid,
        user_id=1
    )
    
    status = check_status(fid)
    if status != 'Non soldée':
        print(f"FAILURE: Expected 'Non soldée', got '{status}'")
    else:
         print("SUCCESS: Status updated to 'Non soldée'")

    # 4. Add Remaining Payment (Total around 10000 + TVA?)
    # Calculate Total TTC
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT montant_ttc FROM factures WHERE id = ?", (fid,))
    ttc = c.fetchone()[0]
    remaining = ttc - 5000
    conn.close()
    
    print(f"\n[Test 3] Adding Remaining Payment ({remaining})...")
    logic.create_payment(
        client_id=client_id,
        montant=remaining,
        mode_paiement='Espèces',
        facture_id=fid,
        user_id=1
    )
    status = check_status(fid)
    if status != 'Payée':
        print(f"FAILURE: Expected 'Payée', got '{status}'")
    else:
         print("SUCCESS: Status updated to 'Payée'")
         
except Exception as e:
    print(f"EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("\n--- END VERIFICATION ---")
