
import os
import sys
from datetime import datetime

# Adjust path if needed
sys.path.append(r"C:\GICA_PROJET")

try:
    from logic import get_logic
    from reports import generate_global_consumption_pdf, generate_global_consumption_excel
    
    print("Dependencies loaded.")
    
    # 1. Test Data Retrieval
    logic = get_logic()
    test_date = "2026-01-11" # We know we have data around here from previous tasks
    
    print(f"Fetching data for {test_date}...")
    data = logic.get_global_consumption_data(test_date)
    
    # Check structure
    if "data" in data and isinstance(data["data"], list):
        print(f"Data retrieved successfully. {len(data['data'])} products found.")
        # Print sample
        if len(data['data']) > 0:
            print("Sample Product Data:", data['data'][0])
    else:
        print("ERROR: Invalid data structure returned.")
        sys.exit(1)

    # 2. Test Report Generation (PDF)
    print("Generating PDF...")
    try:
        pdf_path = generate_global_consumption_pdf(test_date)
        if os.path.exists(pdf_path):
            print(f"PDF generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
        else:
            print("ERROR: PDF file not found after generation.")
    except Exception as e:
        print(f"ERROR generating PDF: {e}")

    # 3. Test Report Generation (Excel)
    print("Generating Excel...")
    try:
        excel_path = generate_global_consumption_excel(test_date)
        if os.path.exists(excel_path):
            print(f"Excel generated: {excel_path} ({os.path.getsize(excel_path)} bytes)")
        else:
            print("ERROR: Excel file not found after generation.")
    except Exception as e:
        print(f"ERROR generating Excel: {e}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
