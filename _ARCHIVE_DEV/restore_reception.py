
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(r"c:\GICA_PROJET")

from database import DatabaseManager

def restore_reception():
    print("Restoring reception BR-0011-2026...")
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Data from backup scan
    data = {
        'numero': 'BR-0011-2026',
        'annee': 2026,
        'date_reception': '2026-01-14',
        'chauffeur': '',
        'matricule': '',
        'transporteur': '',
        'lieu_livraison': 'Sur Stock',
        'adresse_chantier': '',
        'product_id': 38,
        'quantite_annoncee': 120.0,
        'quantite_recue': 120.0,
        'ecart': 0.0,
        'motif_ecart': '',
        'matricule_remorque': '',
        'created_at': '2026-01-14 18:52:34',
        'created_by': 1,
        'num_bon_transfert': '',
        'date_bt': '2026-01-14',
        'num_facture': '',
        'date_fact': '2026-01-14',
        'statut': 'ANNULEE' # KEY CHANGE
    }
    
    # Check if already exists to prevent duplicate (in case double run)
    cursor.execute("SELECT id FROM receptions WHERE numero = ?", (data['numero'],))
    if cursor.fetchone():
        print("Reception already exists! Skipping.")
        return

    # Insert with explicit columns to capture created_at for sorting
    cursor.execute("""
        INSERT INTO receptions 
        (numero, annee, date_reception, chauffeur, matricule, transporteur,
         lieu_livraison, adresse_chantier, product_id, quantite_annoncee,
         quantite_recue, ecart, matricule_remorque, created_by,
         num_bon_transfert, date_bt, num_facture, date_fact, motif_ecart, 
         created_at, statut)
        VALUES (:numero, :annee, :date_reception, :chauffeur, :matricule, :transporteur,
         :lieu_livraison, :adresse_chantier, :product_id, :quantite_annoncee,
         :quantite_recue, :ecart, :matricule_remorque, :created_by,
         :num_bon_transfert, :date_bt, :num_facture, :date_fact, :motif_ecart, 
         :created_at, :statut)
    """, data)
    
    rec_id = cursor.lastrowid
    conn.commit()
    print(f"SUCCESS: Restored reception. ID: {rec_id}, Numero: {data['numero']}, Statut: {data['statut']}")
    
    # Verify no stock impact?
    # Logic: Since we only inserted into Receptions (and not StockMovements), 
    # and statut is ANNULEE, it should be effectively invisible to calculations.
    # The user wanted it "non comptabilisé".
    
    # Verify stats (Optional, but good practice)
    # Fetch stats for product 38
    p_stats_all = db.get_all_products_with_stats()
    p = next((p for p in p_stats_all if p['id'] == 38), None)
    if p:
        print(f"Verification - Product {p['nom']} Total Receptions: {p.get('total_receptions', 'N/A')}")
        # Note: We don't know the exact previous total, but we know this shouldn't add 120.
    else:
        print("Warning: Product 38 not found in active products.")

if __name__ == "__main__":
    restore_reception()
