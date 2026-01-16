import sqlite3

# Hardcoded DB Name
DB_NAME = "gestion_commerciale.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

print("Migrating schema: Adding 'etat_paiement' to 'factures'...")

try:
    # 1. Add Column
    try:
        c.execute("ALTER TABLE factures ADD COLUMN etat_paiement TEXT DEFAULT 'A Terme'")
        print("Column 'etat_paiement' added.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'etat_paiement' already exists.")
        else:
            raise e

    # 2. Update existing rows (just to be sure if default didn't apply to everything for some reason, though DEFAULT does for new cols usually)
    # Actually, for existing rows, SQLite adds the column with the default value or NULL if not specified? 
    # With ADD COLUMN ... DEFAULT 'A Terme', existing rows get 'A Terme'.
    # But let's force update 'N/A' or NULL just in case.
    
    c.execute("UPDATE factures SET etat_paiement = 'A Terme' WHERE etat_paiement IS NULL OR etat_paiement = 'N/A'")
    conn.commit()
    print(f"Ensured data consistency (Rows updated: {c.rowcount})")
    
    # 3. Verify
    print("\n--- Verification ---")
    c.execute("SELECT id, numero, etat_paiement FROM factures LIMIT 5")
    for r in c.fetchall():
        print(r)

except Exception as e:
    print(f"Error during migration: {e}")
    
conn.close()
