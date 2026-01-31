import sqlite3

def fix_stock():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    product_name = "CEMII A-L 42.5 N VRAC"
    
    # 1. Get Product ID
    cursor.execute("SELECT id, stock_actuel FROM products WHERE nom LIKE ?", (f"%{product_name}%",))
    res = cursor.fetchone()
    if not res:
        print("Product not found")
        return
    pid, current_stock = res
    print(f"Target Product: {product_name} (ID: {pid})")
    print(f"Current Stock: {current_stock}")
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # 2. Identify and Delete the Zombie Movement (BR-0011-2026)
        # We know from analysis it is associated with a cancelled reception.
        # Find cancelled receptions for this product
        cursor.execute("SELECT id, numero FROM receptions WHERE product_id = ? AND statut = 'ANNULEE'", (pid,))
        cancelled_receptions = cursor.fetchall()
        
        deleted_count = 0
        for rid, rnum in cancelled_receptions:
            print(f"Checking cancelled reception: {rnum} (ID: {rid})")
            
            # Find movements linked to this reception
            cursor.execute("SELECT id, quantite FROM stock_movements WHERE document_id = ? AND type_mouvement = 'Réception'", (rid,))
            mvs = cursor.fetchall()
            
            for mvid, quantity in mvs:
                print(f"  FOUND ZOMBIE MOVEMENT: ID={mvid}, Qty={quantity}. DELETING...")
                cursor.execute("DELETE FROM stock_movements WHERE id = ?", (mvid,))
                deleted_count += 1
                
        if deleted_count == 0:
            print("No zombie movements found for cancelled receptions. Checking manually for BR-0011...")
            # Fallback by reference
            cursor.execute("SELECT id FROM stock_movements WHERE reference_document LIKE '%BR-0011%' AND product_id = ?", (pid,))
            mvs = cursor.fetchall()
            for mvid, in mvs:
                 print(f"  FOUND ZOMBIE MOVEMENT BY REF: ID={mvid}. DELETING...")
                 cursor.execute("DELETE FROM stock_movements WHERE id = ?", (mvid,))
                 deleted_count += 1

        # 3. Recalculate Stock from Scratch
        # Sum all remaining movements
        cursor.execute("SELECT SUM(quantite) FROM stock_movements WHERE product_id = ?", (pid,))
        sum_qty = cursor.fetchone()[0] or 0.0
        
        # Get Initial Stock
        cursor.execute("SELECT stock_initial FROM products WHERE id = ?", (pid,))
        stock_init = cursor.fetchone()[0] or 0.0
        
        new_stock = stock_init + sum_qty
        
        print("-" * 30)
        print(f"Recalculated Stock: {new_stock}")
        print(f"Old Stock: {current_stock}")
        
        if abs(new_stock - current_stock) > 0.01:
            print(f"Updating Stock... ({current_stock} -> {new_stock})")
            cursor.execute("UPDATE products SET stock_actuel = ? WHERE id = ?", (new_stock, pid))
            conn.commit()
            print("Update Successful.")
        else:
            print("Stock is already correct (orphaned movement might have been expected?). No.")
            # If we deleted something, we MUST update stock if it was counting it.
            # Wait, if we deleted a movement, sum_qty changes.
            # So new_stock will be different from what it WOULD have been.
            # But compare to DB stock.
            conn.commit()
            print("Fix applied.")
            
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_stock()
