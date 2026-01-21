import sqlite3

def fix_invoice_date():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    FAC_NUM = 'FAC-0025-2026' # Assuming user meant this by "N 0025", but I should verify if they use ID or Number. usually Number.
    # User said "facture N 0025", likely FAC-0025-2026.
    
    # 1. Check existence
    cursor.execute("SELECT id, date_facture FROM factures WHERE numero LIKE '%0025%'")
    fac = cursor.fetchone()
    
    if not fac:
        print(f"Invoice {FAC_NUM} not found!")
        return

    fid, old_date = fac
    print(f"Found Invoice {fid}: Date={old_date}")
    
    NEW_DATE = '2026-01-15'
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Update Invoice
        cursor.execute("UPDATE factures SET date_facture = ? WHERE id = ?", (NEW_DATE, fid))
        print(f"Updated Invoice Date to {NEW_DATE}")
        
        # Update Movement
        cursor.execute("UPDATE stock_movements SET date_mouvement = ? WHERE document_id = ? AND reference_document LIKE '%0025%'", (NEW_DATE, fid))
        print("Updated Stock Movement Date")
        
        conn.commit()
        print("Success")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    fix_invoice_date()
