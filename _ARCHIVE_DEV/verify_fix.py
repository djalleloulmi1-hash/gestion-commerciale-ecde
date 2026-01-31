
import sqlite3
import os
import sys

# Ensure we can import from current directory
sys.path.append(os.getcwd())

import database
from database import DatabaseManager

TEST_DB = "test_healing.db"

def run_test():
    print(f"Starting Self-Healing Test on {TEST_DB}...")
    
    # Clean up previous run
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    # Save original schema
    ORIGINAL_SCHEMA = database.MASTER_SCHEMA.copy()
    
    try:
        # 1. Define initial schema
        print("\n[Step 1] Initializing with Version 1 Schema...")
        # We must include 'users' and 'products' because _initialize_default_data expects them
        TEST_SCHEMA_V1 = {
            "users": database.MASTER_SCHEMA["users"],
            "products": database.MASTER_SCHEMA["products"],
            "test_users": {
                "id": "INTEGER PRIMARY KEY",
                "username": "TEXT"
            }
        }
        database.MASTER_SCHEMA = TEST_SCHEMA_V1
        
        # Initialize DB
        db = DatabaseManager(TEST_DB)
        db.close()
        
        # Verify V1
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(test_users)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        print(f"Columns found: {columns}")
        if "username" in columns and "id" in columns:
            print("V1 Verification: PASS ✅")
        else:
            print(f"V1 Verification: FAIL ❌ {columns}")
            return

        # 2. Update schema (Add column)
        print("\n[Step 2] Updating to Version 2 Schema (Adding 'email')...")
        TEST_SCHEMA_V2 = TEST_SCHEMA_V1.copy()
        TEST_SCHEMA_V2["test_users"] = {
            "id": "INTEGER PRIMARY KEY",
            "username": "TEXT",
            "email": "TEXT" # New column
        }
        database.MASTER_SCHEMA = TEST_SCHEMA_V2
        
        # Re-initialize DB (should trigger self-healing)
        db = DatabaseManager(TEST_DB)
        db.close()
        
        # Verify V2
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(test_users)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        print(f"Columns found: {columns}")
        if "email" in columns:
            print("V2 Verification (Column Addition): PASS ✅")
        else:
            print(f"V2 Verification: FAIL ❌ {columns}")
            return
            
        # 3. Add new table
        print("\n[Step 3] Updating to Version 3 Schema (Adding new table)...")
        TEST_SCHEMA_V3 = TEST_SCHEMA_V2.copy()
        TEST_SCHEMA_V3["test_posts"] = {
            "id": "INTEGER PRIMARY KEY",
            "content": "TEXT"
        }
        database.MASTER_SCHEMA = TEST_SCHEMA_V3
        
        db = DatabaseManager(TEST_DB)
        db.close()
        
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_posts'")
        if cursor.fetchone():
            print("V3 Verification (Table Creation): PASS ✅")
        else:
            print("V3 Verification: FAIL ❌")
            return
            
        print("\nALL TESTS PASSED ✅")

    except Exception as e:
        print(f"\nTest FAILED with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore schema
        database.MASTER_SCHEMA = ORIGINAL_SCHEMA
        # Cleanup
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except:
                pass

if __name__ == "__main__":
    run_test()
