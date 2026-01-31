
import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

try:
    from database import DatabaseManager
    print("Import successful.")
    
    print("Initializing DatabaseManager...")
    db = DatabaseManager()
    print("DatabaseManager initialized successfully.")
    
    # Check if a known table exists
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
    if cursor.fetchone():
        print("Table 'clients' verified.")
    else:
        print("Error: Table 'clients' not found.")
        
    print("Self-Healing Verification Passed ✅")
    
except Exception as e:
    print(f"Error during verification: {e}")
    sys.exit(1)
