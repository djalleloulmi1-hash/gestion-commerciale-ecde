
import os
import sqlite3
from datetime import datetime
from database import DatabaseManager

# Setup Test DB
if os.path.exists("test_dashboard_ca.db"):
    os.remove("test_dashboard_ca.db")

db = DatabaseManager("test_dashboard_ca.db")
conn = db._get_connection()

# Create dummy data
user_id = db.create_user("tester", "test", "Tester")
client_id = db.create_client("Client Test", "Adresse", "RC", "NIS", "NIF", "ART", 10000.0, user_id)
prod_id = db.create_product("Prod Test", "U", "P1", 100.0, 1000.0, 100.0, 1000.0, 19.0, "Ciment", user_id)

# 1. Valid Invoice (1000 TTC)
# We mock using direct SQL for speed or use create_invoice if possible, but create_invoice is complex.
# Let's insert directly to control status and amounts easily.
c = conn.cursor()

def create_facture_direct(num, type_doc, montant_ttc, status):
    c.execute("""
        INSERT INTO factures (numero, type_document, type_vente, annee, date_facture, 
        client_id, montant_ht, montant_tva, montant_ttc, statut, created_by)
        VALUES (?, ?, 'Comptant', 2025, ?, ?, 0, 0, ?, ?, ?)
    """, (num, type_doc, datetime.now().strftime("%Y-%m-%d"), client_id, montant_ttc, status, user_id))
    return c.lastrowid

# Invoice 1: 1000 DA, Valid
create_facture_direct("F001", "Facture", 1000.0, "Soldée")

# Invoice 2: 2000 DA, Cancelled
create_facture_direct("F002", "Facture", 2000.0, "Annulée")

# Avoir 1: 300 DA, Valid
create_facture_direct("AV001", "Avoir", 300.0, "Remboursée")

# Avoir 2: 50 DA, Cancelled
create_facture_direct("AV002", "Avoir", 50.0, "Annulée")

conn.commit()

# Run Logic (Mimic DashboardFrame._build)
factures = db.get_all_factures()

valid_factures = [f for f in factures if f['type_document'] == 'Facture' and f['statut'] != 'Annulée']
valid_avoirs = [f for f in factures if f['type_document'] == 'Avoir' and f['statut'] != 'Annulée']

total_sales = sum(f['montant_ttc'] for f in valid_factures)
total_returns = sum(f['montant_ttc'] for f in valid_avoirs)
total_ca = total_sales - total_returns

print(f"Total Sales (Valid): {total_sales}")
print(f"Total Returns (Valid): {total_returns}")
print(f"Net CA: {total_ca}")

# Expected: 1000 - 300 = 700
assert total_sales == 1000.0
assert total_returns == 300.0
assert total_ca == 700.0

print("Verification Passed!")

db.close()
# os.remove("test_dashboard_ca.db")
