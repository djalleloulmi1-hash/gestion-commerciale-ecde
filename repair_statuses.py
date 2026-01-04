
import sqlite3
import os

DB_NAME = 'gestion_commerciale.db'

def repair_statuses():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("Checking for invoices with incorrect statuses...")

    # Find all Invoices
    c.execute("SELECT id, numero, montant_ttc, statut FROM factures WHERE type_document = 'Facture' AND statut != 'Annulée'")
    invoices = c.fetchall()
    
    repaired_count = 0

    for inv in invoices:
        inv_id = inv['id']
        inv_ttc = inv['montant_ttc']
        current_status = inv['statut']
        
        # Calculate Total Avoirs
        c.execute("SELECT COALESCE(SUM(montant_ttc), 0) FROM factures WHERE facture_origine_id = ? AND type_document = 'Avoir' AND statut != 'Annulée'", (inv_id,))
        total_avoirs = c.fetchone()[0]
        
        # Logic Check
        new_status = current_status # Default keep same unless change needed
        
        # If there are avoirs
        if total_avoirs != 0:
            if abs(total_avoirs) >= (inv_ttc - 0.01):
                new_status = 'Remboursée'
            elif abs(total_avoirs) > 0:
                new_status = 'Partiellement remboursée'
        else:
            # If currently marked partially refunded but has no active avoirs? (Unlikely but possible if avoir cancelled)
            if 'remboursée' in current_status.lower() and total_avoirs == 0:
                # Revert to 'Non payée' or 'Payée'?? Hard to know if it was paid.
                # Safer to leave unless we are sure. But the main issue is Partiel -> Total.
                pass

        if new_status != current_status:
            print(f"Reparing {inv['numero']}: Status '{current_status}' -> '{new_status}' (Invoice: {inv_ttc}, Avoirs: {total_avoirs})")
            c.execute("UPDATE factures SET statut = ? WHERE id = ?", (new_status, inv_id))
            repaired_count += 1
            
    conn.commit()
    conn.close()
    print(f"Repair complete. {repaired_count} invoices updated.")

if __name__ == "__main__":
    repair_statuses()
