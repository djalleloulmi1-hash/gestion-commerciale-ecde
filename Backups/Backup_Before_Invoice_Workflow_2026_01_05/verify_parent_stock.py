
import sqlite3
from database import DatabaseManager
from logic import BusinessLogic

def test_parent_stock():
    print("--- Starting Parent Stock Verification ---")
    db = DatabaseManager("test_stock.db")
    # Reset for clean state
    db.reset_data()
    # Ensure migrations are applied (implied by init)
    
    logic = BusinessLogic()
    logic.db = db # Point to test db

    # 1. Create Parent Product
    print("\n1. Creating Parent Product...")
    parent_id = db.create_product(
        nom="Ciment Parent",
        unite="Tonne",
        stock_initial=100.0,
        stock_actuel=100.0,
        prix_actuel=1000.0,
        code_produit="P01"
    )
    print(f"Parent ID: {parent_id}, Stock: {db.get_product_by_id(parent_id)['stock_actuel']}")

    # 2. Create Child Product
    print("\n2. Creating Child Product (linked to Parent)...")
    child_id = db.create_product(
        nom="Ciment Child (Sac)",
        unite="Sac",
        stock_initial=0.0,
        stock_actuel=0.0,
        prix_actuel=50.0,
        code_produit="C01",
        parent_stock_id=parent_id
    )
    child = db.get_product_by_id(child_id)
    print(f"Child ID: {child_id}, Parent ID: {child.get('parent_stock_id')}")
    
    # 3. Check Stock Availability for Child
    print("\n3. Checking Stock Availability for Child...")
    # Should look at Parent Stock (100)
    avail, qty = logic.check_stock_availability(child_id, 10.0)
    print(f"Requested 10. Available? {avail}. Reported Stock: {qty}")
    
    if qty == 100.0 and avail:
        print("PASS: Correctly resolved to Parent Stock.")
    else:
        print(f"FAIL: Expected 100.0, got {qty}")

    # 4. Simulate Sale of Child Product
    print("\n4. Simulating Sale of 5 units of Child...")
    # This calls log_stock_movement
    db.log_stock_movement(
        product_id=child_id,
        type_mouvement="Vente",
        quantite=-5.0,
        reference_document="TEST-REF"
    )
    
    # 5. Verify Stocks
    print("\n5. Verifying Stocks after Sale...")
    parent_after = db.get_product_by_id(parent_id)
    child_after = db.get_product_by_id(child_id)
    
    print(f"Parent Stock: {parent_after['stock_actuel']}")
    print(f"Child Stock: {child_after['stock_actuel']}")
    
    if parent_after['stock_actuel'] == 95.0:
        print("PASS: Parent stock deducted correctly.")
    else:
        print(f"FAIL: Parent stock expected 95.0, got {parent_after['stock_actuel']}")
        
    if child_after['stock_actuel'] == 0.0:
        print("PASS: Child stock remains untouched (0.0).")
    else:
        print(f"FAIL: Child stock changed! Got {child_after['stock_actuel']}")

    # 6. Verify Movement Log
    print("\n6. Verifying Movement Log...")
    moves = db.get_stock_movements(parent_id)
    print(f"Parent Movements: {len(moves)}")
    if len(moves) > 0:
        last_mv = moves[0]
        print(f"Last Movement Ref: {last_mv['reference_document']}")
        if "Via C01" in last_mv['reference_document'] or "Via Ciment Child" in last_mv['reference_document']:
             print("PASS: Movement reference includes child info.")
        else:
             print("WARNING: Child info not in reference (Optional)")
             
    child_moves = db.get_stock_movements(child_id)
    print(f"Child Movements: {len(child_moves)} (Expected 0)")
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    try:
        test_parent_stock()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
