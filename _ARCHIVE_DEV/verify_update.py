import sys
import os
import sqlite3

# Force path to include current directory
sys.path.append(r"C:\GICA_PROJET")

from database import DatabaseManager

def test_self_healing():
    print("Testing Self-Healing Database...")
    
    # 1. Initialize DB (should create tables if not exist)
    db = DatabaseManager()
    
    # 2. Check if new columns exist (e.g., 'banque' in clients)
    conn = db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(clients)")
    columns = {row['name'] for row in cursor.fetchall()}
    
    if 'banque' in columns:
        print("SUCCESS: Column 'banque' found in 'clients'.")
    else:
        print("FAILURE: Column 'banque' NOT found in 'clients'.")
        
    cursor.execute("PRAGMA table_info(products)")
    prod_columns = {row['name'] for row in cursor.fetchall()}
    
    if 'parent_stock_id' in prod_columns:
        print("SUCCESS: Column 'parent_stock_id' found in 'products'.")
    else:
        print("FAILURE: Column 'parent_stock_id' NOT found in 'products'.")

    # 3. Check WAL Mode
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    print(f"Journal Mode: {mode}")
    if mode.upper() == 'WAL':
        print("SUCCESS: WAL mode enabled.")
    else:
        print("FAILURE: WAL mode NOT enabled.")

    db.close()

if __name__ == "__main__":
    test_self_healing()
