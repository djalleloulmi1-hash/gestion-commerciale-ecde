from logic import BusinessLogic, get_logic
from database import get_db
from reports import generate_stock_valuation_excel, generate_stock_valuation_pdf
import os
from datetime import datetime

def test_valuation():
    print("Testing Stock Valuation logic...")
    db = get_db()
    logic = get_logic()
    logic.db = db # Ensure connection
    
    # 1. Setup Test Data
    # Create product
    pid = db.create_product("Test Val Product", "Unit", "TEST-VAL", 100.0, 50.0, 200.0, 100.0)
    print(f"Created Product ID: {pid}")
    
    # Create reception (Sur Stock) - Day 1
    db.create_reception(2025, "2025-01-01", "Chauffeur", "Mat", "Trans", "Sur Stock", "Adr", pid, 10.0, 10.0)
    
    # Create Sale - Day 2
    # Create Client
    cid = db.create_client("Test Client", "Adr", "RC", "NIS", "NIF", "Art")
    
    # Create Facture
    fid = db.create_facture("Facture", 2025, "2025-01-02", cid)
    cursor = db._get_connection().cursor()
    cursor.execute("INSERT INTO lignes_facture (facture_id, product_id, quantite, prix_unitaire, montant) VALUES (?, ?, ?, ?, ?)", 
                   (fid, pid, 5.0, 200.0, 1000.0))
    db.log_action(1, "TEST", "Created test data")
    db._get_connection().commit()
    
    # 2. Run Logic
    print("Running calculation...")
    data = logic.get_stock_valuation_data(pid, "2025-01-01", "2025-01-03")
    
    print("Data retrieved.")
    for day in data['data']:
        print(f"Date: {day['date']}, Init: {day['stock_initial_qty']}, Rec: {day['reception_qty']}, Vente: {day['vente_qty']}, Final: {day['stock_final_qty']}")
        
    # Verify values
    # Initial Stock = 100.
    # Day 1: Rec 10. Stock -> 110. (Depending on if logic counts movements within range. Logic starts with calculated initial BEFORE range)
    # Range starts 2025-01-01.
    # Initial (before 01-01) = 100.
    # Day 01-01: Rec 10. Sale 0. Final 110.
    # Day 01-02: Rec 0. Sale 5. Final 105.
    
    # 3. Generate Excel
    print("Generating Excel...")
    generate_stock_valuation_excel(data, "test_valuation.xlsx")
    
    if os.path.exists("test_valuation.xlsx"):
        print("Excel created successfully.")
    else:
        print("Excel creation failed.")

    # 4. Generate PDF
    print("Generating PDF...")
    generate_stock_valuation_pdf(data, "test_valuation.pdf")
    
    if os.path.exists("test_valuation.pdf"):
        print("PDF created successfully.")
    else:
        print("PDF creation failed.")

if __name__ == "__main__":
    try:
        test_valuation()
        print("Test Complete.")
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
