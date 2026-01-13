
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def inspect_product_and_receptions(product_name_part):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"Searching for products matching: '{product_name_part}'")
    cursor.execute("SELECT * FROM products WHERE nom LIKE ?", (f"%{product_name_part}%",))
    products = cursor.fetchall()

    if not products:
        print("No products found.")
        return

    for p in products:
        print(f"\n--- Product: {p['nom']} (ID: {p['id']}) ---")
        print(f"  Code: {p['code_produit']}")
        print(f"  Stock Actuel: {p['stock_actuel']}")
        print(f"  Stock Initial: {p['stock_initial']}")
        print(f"  Parent ID: {p['parent_stock_id']}")
        
        if p['parent_stock_id']:
            cursor.execute("SELECT * FROM products WHERE id = ?", (p['parent_stock_id'],))
            parent = cursor.fetchone()
            if parent:
                print(f"  -> Parent: {parent['nom']} (ID: {parent['id']}), Stock: {parent['stock_actuel']}")
            else:
                print(f"  -> Parent ID {p['parent_stock_id']} NOT FOUND!")

        print("\n  Recent Receptions:")
        cursor.execute("SELECT * FROM receptions WHERE product_id = ? ORDER BY created_at DESC LIMIT 5", (p['id'],))
        receptions = cursor.fetchall()
        for r in receptions:
            print(f"    - ID: {r['id']}, Num: {r['numero']}, Date: {r['date_reception']}, Qté Reçue: {r['quantite_recue']}, Lieu: {r['lieu_livraison']}")
            
            # Check for stock movements for this reception
            cursor.execute("SELECT * FROM stock_movements WHERE document_id = ? AND type_mouvement = 'Réception' AND product_id = ?", (r['id'], p['id']))
            mv = cursor.fetchone()
            if mv:
                print(f"      [Movement Found] ID: {mv['id']}, Qté: {mv['quantite']}, Stock Après: {mv['stock_apres']}")
            else:
                 # Check if movement is on parent
                if p['parent_stock_id']:
                     cursor.execute("SELECT * FROM stock_movements WHERE document_id = ? AND type_mouvement = 'Réception' AND product_id = ?", (r['id'], p['parent_stock_id']))
                     mv_parent = cursor.fetchone()
                     if mv_parent:
                         print(f"      [Movement Found on Parent] ID: {mv_parent['id']}, Qté: {mv_parent['quantite']}, Stock Après: {mv_parent['stock_apres']}")
                     else:
                         print("      [WARNING] No Stock Movement found!")
                else:
                    print("      [WARNING] No Stock Movement found!")

    conn.close()

if __name__ == "__main__":
    inspect_product_and_receptions("CEMII")
