
import os
from logic import BusinessLogic
from utils import export_clients_to_excel

def test_export():
    print("Initializing logic...")
    logic = BusinessLogic()
    
    print("Fetching client export data...")
    data = logic.get_clients_export_data()
    
    if not data:
        print("No clients found or empty data.")
        return

    print(f"Retrieved {len(data)} clients.")
    print("Sample Data (First Client):")
    print(data[0])
    
    filename = "test_export_clients.xlsx"
    print(f"Generating Excel: {filename}...")
    try:
        export_clients_to_excel(data, filename)
        print("Excel generated successfully.")
        
        # Optional: Print file size
        size = os.path.getsize(filename)
        print(f"File size: {size} bytes")
        
    except Exception as e:
        print(f"FAILED to generate Excel: {e}")

if __name__ == "__main__":
    test_export()
