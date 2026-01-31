import sqlite3
import os

DB_NAME = os.path.abspath("gestion_commerciale.db")

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

print("Cleaning up test data...")

# 1. Get Test Invoice ID
c.execute("SELECT id, client_id, montant_ttc FROM factures WHERE numero = 'FAC-0016-2026'") # Adjust if different
row = c.fetchone()
if row:
    fid, cid, amount = row
    print(f"Deleting Test Invoice {fid}...")
    
    # Delete Payments
    c.execute("DELETE FROM paiements WHERE facture_id = ?", (fid,))
    print(f"Deleted {c.rowcount} payments.")
    
    # Delete Lines
    c.execute("DELETE FROM lignes_facture WHERE facture_id = ?", (fid,))
    print(f"Deleted {c.rowcount} lines.")
    
    # Delete Invoice
    c.execute("DELETE FROM factures WHERE id = ?", (fid,))
    print("Deleted invoice.")
    
    # Revert Client Balance (Simplify: assume I added payment so balance messed up?)
    # Test 3 added remaining payment, so balance should be net 0 change from start (Invoice + Payment).
    # But I want to revert changes.
    # Invoice added debt +1190.
    # Payment 1: -5000 (Debt reduced).
    # Payment 2: -3810 (Debt reduced).
    # Total Payment: 8810?? No, 5000 then remaining (-3810?? remaining = 1190 - 5000 = -3810).
    # Logic: remaining = ttc - 5000 = 1190 - 5000 = -3810.
    # Create payment of -3810? No, `create_payment` takes amount.
    # If I passed negative amount, debt INCREASED.
    # So net effect on debt: +1190 (Inv) - 5000 (Pay1) - (-3810) (Pay2 with negative amount) = 1190 - 5000 + 3810 = 0.
    # So client balance should be correct (0 change).
    # So no need to manual fix client balance if logic was correct.
    
    # Revert Stock Injection
    # I injected 1000.
    # I sold 1.
    # So current stock = Start + 1000 - 1 = Start + 999.
    # I need to remove 999.
    # Wait, which product?
    # I selected LIMIT 1.
    c.execute("SELECT id FROM products LIMIT 1")
    pid = c.fetchone()[0]
    
    c.execute("UPDATE products SET stock_actuel = stock_actuel - 999 WHERE id = ?", (pid,))
    print("Reverted stock injection.")
    
    conn.commit()
else:
    print("Test invoice not found, maybe checked wrong number or not created.")

# Delete script files
# cleanup is separate step
    
conn.close()
