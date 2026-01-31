import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

from database import get_db
from logic import get_logic

def verify_fix():
    print("--- STARTING VERIFICATION ---")
    db = get_db()
    logic = get_logic()
    user_id = 1
    
    # 1. Create a FRESH reception "Sur Chantier" (No stock impact)
    print("\n1. Creating 'Sur Chantier' reception (Stock should be 0 impact)...")
    rid = db.create_reception(
        annee=2026, date_reception="2026-01-11",
        chauffeur="Test Fix", matricule="99999", transporteur="Fix Trans",
        lieu_livraison="Sur Chantier", adresse_chantier="Site A",
        product_id=38, quantite_annoncee=100, quantite_recue=50,
        created_by=user_id
    )
    print(f"Created Reception ID: {rid}")
    
    # Check Stock Movement (Should be None)
    conn = db._get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (rid,))
    mv = c.fetchone()
    if mv:
        print("FAILURE: Movement found for Sur Chantier!")
    else:
        print("SUCCESS: No movement for Sur Chantier.")

    # 2. SIMULATE UI UPDATE to "Sur Stock"
    # The UI calls: revert -> update SQL -> process
    print("\n2. Simulating UI Update to 'Sur Stock' (Qty 50)...")
    
    # A. Revert (Should do nothing effectively as it was Sur Chantier)
    print("   Calling revert_reception_stock_impact...")
    logic.revert_reception_stock_impact(rid)
    
    # B. Update SQL
    print("   Executing UPDATE to 'Sur Stock'...")
    c.execute("UPDATE receptions SET lieu_livraison='Sur Stock' WHERE id=?", (rid,))
    conn.commit()
    
    # C. Process
    print("   Calling process_reception...")
    logic.process_reception(rid, user_id)
    
    # Check Stock Movement (Should EXIST now)
    c.execute("SELECT * FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (rid,))
    mv = c.fetchone()
    if mv:
        print("SUCCESS: Movement CREATED after update to Sur Stock.")
        print(dict(mv))
    else:
        print("FAILURE: No movement created after update!")
        
    # 3. SIMULATE UPDATE QTY (50 -> 80)
    print("\n3. Simulating Update Qty (50 -> 80)...")
    
    # A. Revert (Should remove the 50 movement)
    print("   Calling revert...")
    logic.revert_reception_stock_impact(rid)
    
    # Check if gone
    c.execute("SELECT * FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (rid,))
    if c.fetchone():
        print("FAILURE: Movement NOT deleted after revert!")
    else:
        print("SUCCESS: Movement deleted after revert.")
        
    # B. Update SQL
    print("   Executing UPDATE Qty=80...")
    c.execute("UPDATE receptions SET quantite_recue=80 WHERE id=?", (rid,))
    conn.commit()
    
    # C. Process
    print("   Calling process...")
    logic.process_reception(rid, user_id)
    
    # Check Stock Movement (Should be 80)
    c.execute("SELECT * FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (rid,))
    mv = c.fetchone()
    if mv and mv['quantite'] == 80.0:
        print(f"SUCCESS: Movement updated to {mv['quantite']}.")
    else:
        print(f"FAILURE: Movement is {mv['quantite'] if mv else 'None'}, expected 80.0")

if __name__ == "__main__":
    verify_fix()
