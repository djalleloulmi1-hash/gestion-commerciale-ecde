import os
import sqlite3
from datetime import datetime
from database import get_db, DatabaseManager
from utils import generate_reception_pdf

# Setup DB
if os.path.exists("test_decimals.db"):
    os.remove("test_decimals.db")
    
db = DatabaseManager("test_decimals.db")
conn = db._get_connection()

# Create dummy user and product
user_id = db.create_user("tester", "test", "Tester")
prod_id = db.create_product("Ciment Test", "Tonne", "CIM001", 100.0, 500.0, 600.0, 100.0, 19.0, "Ciment", user_id)

# Create Reception with 3 decimals
q_ann = 10.123
q_rec = 9.987
ecart = q_rec - q_ann # -0.136

rec_id = db.create_reception(
    2025, datetime.now().strftime("%Y-%m-%d"), "Chauffeur", "12345", "Transp", "Stock", "", 
    prod_id, q_ann, q_rec, matricule_remorque="67890", created_by=user_id
)

# Read back
conn = db._get_connection()
c = conn.cursor()
c.execute("SELECT * FROM receptions WHERE id=?", (rec_id,))
row = c.fetchone()
r = dict(row)

print(f"Stored Annoncee: {r['quantite_annoncee']}")
print(f"Stored Recue: {r['quantite_recue']}")
print(f"Stored Ecart: {r['ecart']}")

assert abs(r['quantite_annoncee'] - 10.123) < 0.00001
assert abs(r['quantite_recue'] - 9.987) < 0.00001

# Add product name for PDF
r['product_nom'] = "Ciment Test"

# Generate PDF
filename = "test_reception_decimal.pdf"
try:
    generate_reception_pdf(r, filename)
    print(f"PDF Generated: {filename}")
    if os.path.exists(filename):
        print("PDF file exists.")
    else:
        print("PDF file missing!")
except Exception as e:
    print(f"PDF Generation Failed: {e}")

# Cleanup
db.close()
# os.remove("test_decimals.db")
