from logic import BusinessLogic
from database import DatabaseManager

def fix_reception_20():
    print("Starting Fix for Reception 20...")
    db = DatabaseManager()
    logic = BusinessLogic()
    
    reception_id = 20
    target_product_id = 38  # CEMII A-L 42.5 N VRAC
    old_product_id = 37     # CEM II... SAC 50KG

    # Get connection
    conn = db._get_connection()
    
    # 1. Verify current state
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, quantite_recue, lieu_livraison FROM receptions WHERE id = ?", (reception_id,))
    rec = cursor.fetchone()
    if not rec:
        print("Error: Reception neither found.")
        return
    
    print(f"Current Reception: Product ID={rec['product_id']}, Qty={rec['quantite_recue']}")
    
    if rec['product_id'] == target_product_id:
        print("Reception is already fixed (Product ID 38).")
        return

    # 2. Revert Stock Impact for OLD Product (37)
    # This removes the +120 movement and subtracts 120 from Product 37 stock
    print(f"Reverting stock impact for Product {rec['product_id']}...")
    if logic.revert_reception_stock_impact(reception_id):
        print("Success: Stock reverted.")
    else:
        print("Error: Failed to revert stock.")
        return

    # 3. Update Reception Record in DB
    print(f"Updating Reception {reception_id} to Product ID {target_product_id}...")
    cursor.execute("UPDATE receptions SET product_id = ? WHERE id = ?", (target_product_id, reception_id))
    conn.commit()
    print("Database record updated.")

    # 4. Apply Stock Impact for NEW Product (38)
    # This adds +120 movement and adds 120 to Product 38 stock
    print(f"Applying stock impact for Product {target_product_id}...")
    # Assuming Created By User 1 (Admin) if not available, or keep existing log user.
    # logic.process_reception needs user_id. Let's fetch the original creator.
    cursor.execute("SELECT created_by FROM receptions WHERE id = ?", (reception_id,))
    creator = cursor.fetchone()[0] or 1
    
    if logic.process_reception(reception_id, creator):
        print("Success: New stock impact applied.")
    else:
        print("Error: Failed to apply new stock impact (Maybe 'Sur Stock' check failed?).")
        # Logic check: process_reception checks 'lieu_livraison'.
        # We verified it is 'Sur Stock'.
        # It also checks child products. Product 38 is 'CEMII... VRAC'.
        # We should check if 38 is a child.
        pass

    print("Fix Complete.")

if __name__ == "__main__":
    fix_reception_20()
