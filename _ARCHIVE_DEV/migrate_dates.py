from database import DatabaseManager
from datetime import datetime

print("Starting Date Migration...")
db = DatabaseManager()
conn = db._get_connection()
cursor = conn.cursor()

try:
    conn.execute("BEGIN TRANSACTION")
    
    # 1. Update from Receptions
    print("Migrating Receptions...")
    cursor.execute("""
        UPDATE stock_movements 
        SET date_mouvement = (
            SELECT date_reception 
            FROM receptions 
            WHERE receptions.id = stock_movements.document_id
        )
        WHERE type_mouvement = 'Réception' 
          AND document_id IS NOT NULL
    """)
    
    # 2. Update from Factures (Vente)
    print("Migrating Sales...")
    cursor.execute("""
        UPDATE stock_movements 
        SET date_mouvement = (
            SELECT date_facture 
            FROM factures 
            WHERE factures.id = stock_movements.document_id
        )
        WHERE type_mouvement IN ('Vente', 'Avoir') 
          AND document_id IS NOT NULL
    """)
    
    # 3. Update 'Annulation Facture' and 'Annulation Réception'
    # These should use the date of the original document to properly revert it at that point in time?
    # OR the date of cancellation? 
    # Logic: If I cancel a reception from Jan 10th on Jan 14th, does the stock disappear on Jan 10th or 14th?
    # Accounting view: Reversal on 14th.
    # Physical view: If it was an error, it never existed?
    # Standard: Use cancellation date (created_at). 
    # BUT user wants "Chronology". If I revert a Jan 10 sale, stock should be back on Jan 10?
    # "pour éviter les chevauchements... se referé aux dates reception et ventes"
    # User implies correcting the PAST. 
    # Let's set date_mouvement to created_at (Date of Action) for now for cancellations, 
    # OR maybe the date of the document being cancelled?
    # For now, fallback to created_at (extract YYYY-MM-DD) for anything NULL.
    
    print("Setting defaults...")
    cursor.execute("""
        UPDATE stock_movements 
        SET date_mouvement = SUBSTR(created_at, 1, 10)
        WHERE date_mouvement IS NULL
    """)
    
    conn.commit()
    print("Migration Complete.")
    
except Exception as e:
    conn.rollback()
    print(f"Migration Failed: {e}")
