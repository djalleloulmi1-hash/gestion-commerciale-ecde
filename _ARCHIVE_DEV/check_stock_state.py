
import sqlite3
import pandas as pd

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def check_stock():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- DIAGNOSTIC STOCK ---")
    
    # 1. Get Products
    cursor.execute("SELECT id, nom, stock_initial, stock_actuel, parent_stock_id FROM products WHERE active=1")
    products = cursor.fetchall()
    
    print(f"{'ID':<4} | {'NOM':<30} | {'INIT (DB)':<10} | {'ACTUEL (DB)':<12} | {'CALC INIT (UI)'}")
    print("-" * 80)
    
    for p in products:
        pid = p['id']
        nom = p['nom']
        init_db = p['stock_initial']
        curr_db = p['stock_actuel']
        
        # 2. Get Movements (Simulate UI Logic)
        # UI Logic: sales_movements = [m['quantite'] for m in movements if m['type_mouvement'] in ['Vente', 'Retour Avoir']]
        # UI Logic: reception_movements = [m['quantite'] for m in movements if m['type_mouvement'] in ['Réception', 'Annulation Réception']]
        
        cursor.execute("SELECT type_mouvement, quantite FROM stock_movements WHERE product_id=?", (pid,))
        movements = cursor.fetchall()
        
        sales_qty = sum([m['quantite'] for m in movements if m['type_mouvement'] in ['Vente', 'Retour Avoir', 'Annulation Facture']])
        recep_qty = sum([m['quantite'] for m in movements if m['type_mouvement'] in ['Réception', 'Annulation Réception']])
        
        total_in = recep_qty
        total_out = abs(sales_qty) # Abs because sales are negative
        
        # UI Calculation for "Stock Initial" column
        # stock_initial = stock_final - total_in + total_out
        calc_ui_init = curr_db - total_in + total_out
        
        print(f"{pid:<4} | {nom:<30} | {init_db:<10} | {curr_db:<12} | {calc_ui_init:<10}")
        
        if abs(calc_ui_init - init_db) > 0.01:
            print(f"   >>> DISCREPANCY DETECTED! UI shows {calc_ui_init} vs DB {init_db}")
            print(f"       Movements found: IN={total_in}, OUT={total_out}")
            
            # Check physical Receptions table
            cursor.execute("SELECT SUM(quantite_recue) FROM receptions WHERE product_id=? AND lieu_livraison='Sur Stock'", (pid,))
            res = cursor.fetchone()
            real_receptions = res[0] if res and res[0] else 0.0
            print(f"       Real Receptions (Table): {real_receptions}")
            
            if abs(real_receptions - total_in) > 0.01:
                 print(f"       >>> BUG: Receptions Table ({real_receptions}) != Stock Movements Receptions ({total_in})")

    print("-" * 80)
    conn.close()

if __name__ == "__main__":
    check_stock()
