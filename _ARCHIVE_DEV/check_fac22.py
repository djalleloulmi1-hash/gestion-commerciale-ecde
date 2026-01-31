import sqlite3

def check_fac22():
    conn = sqlite3.connect('gestion_commerciale.db')
    cursor = conn.cursor()
    
    print("--- HEADERS ---")
    cursor.execute("SELECT id, numero, montant_ttc FROM factures WHERE numero='FAC-0022-2026'")
    fac = cursor.fetchone()
    print(fac)
    
    if fac:
        fid = fac[0]
        print("--- LINES ---")
        cursor.execute("SELECT * FROM lignes_facture WHERE facture_id=?", (fid,))
        print(cursor.fetchall())
        
    conn.close()

if __name__ == "__main__":
    check_fac22()
