import os
import sqlite3
from datetime import datetime, timedelta
from database import DatabaseManager, get_db
from logic import BusinessLogic, get_logic

# Setup
db = get_db()
logic = get_logic()

print("=== STARTING CONTRACT VERIFICATION ===")

# 1. Create Test Client
client_data = {
    'raison_sociale': 'CONTRACT TEST CLIENT',
    'adresse': 'Test Address',
    'rc': 'RC-TEST',
    'nis': 'NIS-TEST',
    'nif': 'NIF-TEST',
    'article_imposition': 'AI-TEST',
    'seuil_credit': 100000.0,
    'created_by': 1
}
try:
    client_id = db.create_client(**client_data)
    print(f"[OK] Created Client ID: {client_id}")
except Exception as e:
    print(f"[FAIL] Client Creation: {e}")
    exit(1)

# 2. Create Test Product
try:
    product_id = db.create_product(nom='Ciment Test', unite='Sac', prix_actuel=100.0, stock_initial=1000, stock_actuel=1000.0, created_by=1)
    print(f"[OK] Created Product ID: {product_id}")
except Exception as e:
    # Maybe product exists?
    product_id = 1
    print(f"[WARN] Using Product ID: {product_id}")

# 3. Create Active Contract
today = datetime.now()
start_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
end_date = (today + timedelta(days=365)).strftime("%Y-%m-%d")

active_contract_id = db.create_contract(client_id, "CONV-ACTIVE", start_date, end_date, 1000000, created_by=1)
print(f"[OK] Created Active Contract ID: {active_contract_id}")

# 4. Create Expired Contract
expired_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")
expired_start = (today - timedelta(days=100)).strftime("%Y-%m-%d")

expired_contract_id = db.create_contract(client_id, "CONV-EXPIRED", expired_start, expired_end, 1000000, created_by=1)
print(f"[OK] Created Expired Contract ID: {expired_contract_id}")

# 5. Test Invoice with Active Contract
lignes = [{
    'product_id': product_id,
    'quantite': 10,
    'prix_unitaire': 100.0,
    'montant': 1000.0
}]

success, msg, fid = logic.create_invoice_with_validation(
    type_document='Facture',
    client_id=client_id,
    lignes=lignes,
    type_vente='Au comptant',
    mode_paiement='Espèces',
    contract_id=active_contract_id,
    user_id=1
)

if success:
    print(f"[PASS] Active Contract Invoice Created: {fid}")
    # Verify DB Link
    conn = db._get_connection()
    cur = conn.cursor()
    cur.execute("SELECT contract_id FROM factures WHERE id=?", (fid,))
    row = cur.fetchone()
    if row and row[0] == active_contract_id:
        print(f"[PASS] Database Link Verified: contract_id={row[0]}")
    else:
        print(f"[FAIL] Database Link Missing or Wrong: {row}")
else:
    print(f"[FAIL] Active Contract Invoice Failed: {msg}")

# 6. Test Invoice with Expired Contract
success, msg, fid = logic.create_invoice_with_validation(
    type_document='Facture',
    client_id=client_id,
    lignes=lignes,
    type_vente='Au comptant',
    mode_paiement='Espèces',
    contract_id=expired_contract_id,
    user_id=1
)

if not success:
    print(f"[PASS] Expired Contract Blocked: {msg}")
else:
    print(f"[FAIL] Expired Contract ALLOWED! ID: {fid}")

# Cleanup (Optional)
# db.delete_client(client_id)
print("=== VERIFICATION COMPLETE ===")
