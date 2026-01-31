
import sqlite3

def dump_mv():
    conn = sqlite3.connect(r"C:\GICA_PROJET\gestion_commerciale.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Target Product 40
    print("--- RAW MOVEMENTS PRODUCT 40 ---")
    c.execute("SELECT * FROM stock_movements WHERE product_id=40")
    rows = c.fetchall()
    
    total = 0
    for r in rows:
        print(f"ID={r['id']} | Type={r['type_mouvement']} | Qty={r['quantite']} | Ref={r['reference_document']}")
        total += r['quantite']
        
    print(f"TOTAL SUM: {total}")
    
    conn.close()

if __name__ == "__main__":
    dump_mv()
