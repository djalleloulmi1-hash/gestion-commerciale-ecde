import sqlite3

# Hardcoded DB Name because import failed
DB_NAME = "gestion_commerciale.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

print("Migrating 'N/A' to 'A Terme'...")
try:
    c.execute("UPDATE factures SET etat_paiement = 'A Terme' WHERE etat_paiement = 'N/A' OR etat_paiement IS NULL")
    conn.commit()
    print(f"Updated {c.rowcount} rows.")
    
    # Verify
    print("\n--- Remaining Values ---")
    c.execute("SELECT DISTINCT etat_paiement FROM factures")
    for r in c.fetchall():
        print(r)
        
except Exception as e:
    print(f"Error: {e}")
    
conn.close()
