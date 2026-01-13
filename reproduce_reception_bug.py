import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

from database import get_db
from logic import get_logic

def reproduce_issue():
    print("--- STARTING REPRODUCTION ---")
    db = get_db()
    logic = get_logic()
    
    # Use the existing problematic reception ID: 38
    reception_id = 38
    print(f"Targeting Reception ID: {reception_id}")
    
    # 1. Verify it exists
    conn = db._get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM receptions WHERE id=?", (reception_id,))
    row = c.fetchone()
    if not row:
        print("ERROR: Reception 38 not found! Cannot reproduce exactly.")
        # Create a dummy one
        print("Creating dummy reception...")
        rid = db.create_reception(
            annee=2026,
            date_reception="2026-01-11",
            chauffeur="Test",
            matricule="00000",
            transporteur="Test Trans",
            lieu_livraison="Sur Stock",
            adresse_chantier="",
            product_id=38, # 422VRAC
            quantite_annoncee=100,
            quantite_recue=40,
            created_by=1
        )
        reception_id = rid
        print(f"Created Dummy Reception ID: {reception_id}")
    else:
        print("Reception 38 found.")
        # Check if stock movement exists already?
        c.execute("SELECT * FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (reception_id,))
        mv = c.fetchone()
        if mv:
            print("WARNING: Stock movement ALREADY EXISTS for 38. Deleting it to force reproduction.")
            c.execute("DELETE FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (reception_id,))
            conn.commit()
    
    # 2. Call process_reception
    print(f"Calling logic.process_reception({reception_id}, 1)...")
    result = logic.process_reception(reception_id, 1)
    print(f"Result: {result}")
    
    # 3. Check result
    c.execute("SELECT * FROM stock_movements WHERE document_id=? AND type_mouvement='Réception'", (reception_id,))
    mv = c.fetchone()
    if mv:
        print("SUCCESS? Stock movement created.")
        print(dict(mv))
    else:
        print("FAILURE: No stock movement created.")

if __name__ == "__main__":
    reproduce_issue()
