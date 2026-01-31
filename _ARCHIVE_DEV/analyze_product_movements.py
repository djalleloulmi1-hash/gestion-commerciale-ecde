import sqlite3
import pandas as pd

def analyze_movements():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    # 1. Find Product ID
    search_term = "CEMII A-L 42.5 N VRAC"
    cursor.execute("SELECT id, nom, stock_initial, stock_actuel FROM products WHERE nom LIKE ?", (f"%{search_term}%",))
    product = cursor.fetchone()
    
    if not product:
        print(f"Product '{search_term}' not found.")
        return
        
    pid, nom, stock_init, stock_actuel = product
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(f"Product Found: ID={pid}, Name='{nom}'\n")
        f.write(f"Stock Initial: {stock_init}, Stock Actuel (in DB): {stock_actuel}\n")
        f.write("-" * 50 + "\n")
        
        # 2. Get Stock Movements
        f.write("\n--- Stock Movements Table ---\n")
        cursor.execute("""
            SELECT 
                id, type_mouvement, quantite, reference_document, 
                document_id, created_at, date_mouvement 
            FROM stock_movements 
            WHERE product_id = ? 
            ORDER BY created_at
        """, (pid,))
        movements = cursor.fetchall()
        
        calculated_stock = stock_init
        
        f.write(f"{'ID':<5} | {'Date/Time':<20} | {'Type':<20} | {'Ref':<15} | {'Qty':<10} | {'Run. Stock':<10}\n")
        f.write("-" * 90 + "\n")
        
        for mv in movements:
            mid, mtype, qty, ref, doc_id, created_at, date_mv = mv
            eff_date = date_mv if date_mv else created_at
            calculated_stock += qty
            f.write(f"{mid:<5} | {eff_date:<20} | {mtype:<20} | {ref:<15} | {qty:<10.2f} | {calculated_stock:<10.2f}\n")
            
        f.write("-" * 90 + "\n")
        f.write(f"Calculated Final Stock based on Movements: {calculated_stock}\n")
        f.write(f"Discrepancy: {calculated_stock - stock_actuel}\n")
        
        # 3. Cross Check with Receptions
        f.write("\n--- Receptions (Source of Truth for Inflows) ---\n")
        cursor.execute("""
            SELECT id, numero, date_reception, quantite_recue, lieu_livraison, statut 
            FROM receptions 
            WHERE product_id = ? 
            ORDER BY date_reception
        """, (pid,))
        receptions = cursor.fetchall()
        
        total_recepted = 0
        for r in receptions:
            rid, num, date_r, qty, lieu, statut = r
            if statut == 'ANNULEE':
                f.write(f"Reception {num} (ID: {rid}) - ANNULEE - Qty: {qty} (Ignored)\n")
                continue
            if lieu != 'Sur Stock':
                f.write(f"Reception {num} (ID: {rid}) - Dest: {lieu} - Qty: {qty} (Ignored)\n")
                continue
                
            f.write(f"Reception {num} (ID: {rid}) - Date: {date_r} - Qty: {qty} - Add to Stock\n")
            total_recepted += qty
            
        f.write(f"Total Valid Receptions: {total_recepted}\n")

        # 4. Cross Check with Sales (Factures)
        f.write("\n--- Sales (Source of Truth for Outflows) ---\n")
        cursor.execute("""
            SELECT f.id, f.numero, f.date_facture, lf.quantite, f.type_document, f.statut
            FROM lignes_facture lf
            JOIN factures f ON lf.facture_id = f.id
            WHERE lf.product_id = ?
            ORDER BY f.date_facture
        """, (pid,))
        sales = cursor.fetchall()
        
        total_sold = 0
        total_returned = 0
        
        for s in sales:
            fid, num, date_f, qty, type_doc, statut = s
            if statut == 'Annulée' or statut == 'ANNULEE':
                 f.write(f"{type_doc} {num} (ID: {fid}) - ANNULEE - Qty: {qty} (Ignored)\n")
                 continue
                 
            if type_doc == 'Facture':
                f.write(f"Facture {num} (ID: {fid}) - Date: {date_f} - Qty: {qty} - Subtract Stock\n")
                total_sold += qty
            elif type_doc == 'Avoir':
                f.write(f"Avoir {num} (ID: {fid}) - Date: {date_f} - Qty: {qty} - Add to Stock\n")
                total_returned += qty
                
        f.write(f"Total Sold: {total_sold}\n")
        f.write(f"Total Returned: {total_returned}\n")
        
        net_change = total_recepted - total_sold + total_returned
        theoretical_stock = stock_init + net_change
        
        f.write("\n--- Final Verification ---\n")
        f.write(f"Stock Initial: {stock_init}\n")
        f.write(f"Total In (Receptions): +{total_recepted}\n")
        f.write(f"Total Out (Sales): -{total_sold}\n")
        f.write(f"Total Returns (Avoirs): +{total_returned}\n")
        f.write(f"Theoretical Stock: {theoretical_stock}\n")
        f.write(f"Stock Actuel in Product Table: {stock_actuel}\n")
        f.write(f"Stock Calculated from Movements History: {calculated_stock}\n")

    
    conn.close()

if __name__ == "__main__":
    analyze_movements()
