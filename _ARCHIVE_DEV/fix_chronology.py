from database import DatabaseManager
from datetime import datetime
import json
import traceback

def fix_chronology():
    # Use DatabaseManager to ensure correct DB path
    db = DatabaseManager()
    conn = db._get_connection()
    # conn.row_factory = sqlite3.Row # DatabaseManager might not set this or returns custom objects?
    # DatabaseManager usually sets row_factory to sqlite3.Row in _get_connection/init
    # Let's verify or set it.
    import sqlite3
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Connected to DB: {db.db_path}")
    print("Starting Chronological Stock Repair...")
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Snapshot Manual Adjustments (if any)
        # We need to preserve movements that are NOT Receptions or Factures
        # ...
        
        # 2. Clear Stock Movements
        print("Clearing stock movements...")
        cursor.execute("DELETE FROM stock_movements")
        
        # 3. Reset Product Stocks to Initial
        print("Resetting product stocks...")
        cursor.execute("UPDATE products SET stock_actuel = COALESCE(stock_initial, 0)")
        
        # 4. Fetch All Valid Actions
        actions = []
        
        # 4a. Receptions
        print("Fetching Receptions...")
        cursor.execute("SELECT * FROM receptions WHERE lieu_livraison = 'Sur Stock'")
        receptions = cursor.fetchall()
        for r in receptions:
            date_mv = r['date_reception']
            # Fallback if date is missing
            if not date_mv: date_mv = r['created_at'][:10]
            
            actions.append({
                'date': date_mv,
                'created_at': r['created_at'],
                'type': 'Réception',
                'product_id': r['product_id'],
                'quantite': r['quantite_recue'],
                'ref': f"BL {r['numero']}",
                'doc_id': r['id'],
                'user': r['created_by']
            })
            
        # 4b. Factures (Sales) - EXCLUDING Cancelled
        print("Fetching Sales...")
        cursor.execute("SELECT * FROM factures WHERE statut != 'ANNULEE'")
        factures = cursor.fetchall()
        
        for f in factures:
            date_mv = f['date_facture']
            if not date_mv: date_mv = f['created_at'][:10]
            
            # Fetch lines
            cursor.execute("SELECT * FROM lignes_facture WHERE facture_id = ?", (f['id'],))
            lignes = cursor.fetchall()
            
            for l in lignes:
                qty = l['quantite']
                mvm_type = 'Vente'
                sign = -1
                
                if f['type_document'] == 'Avoir':
                    mvm_type = 'Retour Avoir'
                    sign = 1
                
                actions.append({
                    'date': date_mv,
                    'created_at': f['created_at'],
                    'type': mvm_type,
                    'product_id': l['product_id'],
                    'quantite': qty * sign,
                    'ref': f"Fact {f['numero']}",
                    'doc_id': f['id'],
                    'user': f['created_by']
                })

        # 5. Sort Actions
        # Primary: Date, Secondary: Created_At (to keep order within same day)
        print(f"Sorting {len(actions)} actions...")
        actions.sort(key=lambda x: (x['date'], x['created_at']))
        
        # 6. Replay Actions
        print("Replaying actions...")
        count = 0
        for action in actions:
            pid = action['product_id']
            
            # Resolve Parent/Child logic
            # Use database logic: if child, move to parent
            cursor.execute("SELECT parent_stock_id, code_produit, nom FROM products WHERE id = ?", (pid,))
            res = cursor.fetchone()
            target_pid = pid
            ref_addon = ""
            
            if res and res['parent_stock_id']:
                target_pid = res['parent_stock_id']
                child_info = res['code_produit'] or res['nom']
                ref_addon = f" (Via {child_info})"
            
            # Get Current Stock (of target)
            cursor.execute("SELECT stock_actuel FROM products WHERE id = ?", (target_pid,))
            cur_stock = cursor.fetchone()[0] or 0.0
            
            new_stock = cur_stock + action['quantite']
            
            # Insert Movement
            cursor.execute("""
                INSERT INTO stock_movements
                (product_id, type_mouvement, quantite, reference_document, 
                 document_id, stock_avant, stock_apres, created_by, date_mouvement, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                target_pid, 
                action['type'], 
                action['quantite'], 
                action['ref'] + ref_addon,
                action['doc_id'],
                cur_stock, 
                new_stock, 
                action['user'], 
                action['date'],
                action['created_at'] # Preserve original timestamp for audit
            ))
            
            # Update Product
            cursor.execute("UPDATE products SET stock_actuel = ? WHERE id = ?", (new_stock, target_pid))
            count += 1
            
        conn.commit()
        print(f"Success! Replayed {count} movements.")
        
    except Exception as e:
        conn.rollback()
        print(f"FAILED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    fix_chronology()
