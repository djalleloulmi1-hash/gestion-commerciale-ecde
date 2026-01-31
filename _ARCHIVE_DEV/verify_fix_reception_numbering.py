
import sqlite3
import os
import sys

# Setup imports
sys.path.append("c:\\GICA_PROJET")
from database import get_db

def verify_fix():
    print("--- Verifying Reception Numbering Fix ---")
    
    # Use a temporary test database to avoid messing up real data
    db_path = "c:\\GICA_PROJET\\test_reception_fix.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    # Initialize DB (this creates tables via Self-Healing)
    from database import DatabaseManager, MASTER_SCHEMA
    
    # Patch DatabaseManager to use our test DB for this run
    # Actually, let's just instantiate it directly
    db_manager = DatabaseManager(db_path)
    
    try:
        # Create user for FK
        user_id = db_manager.create_user("tester", "pass", "Tester")
        
        # Create product for FK
        prod_id = db_manager.create_product("Test Prod", "U")
        
        print("1. Creating Reception A (Should be BR-0001-2026)")
        id1 = db_manager.create_reception(2026, "2026-01-01", "C1", "M1", "T1", "L1", "A1", prod_id, 10, 10, created_by=user_id)
        
        print("2. Creating Reception B (Should be BR-0002-2026)")
        id2 = db_manager.create_reception(2026, "2026-01-02", "C2", "M2", "T2", "L2", "A2", prod_id, 10, 10, created_by=user_id)
        
        # Check numbers
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT numero FROM receptions WHERE id=?", (id1,))
        num1 = cursor.fetchone()[0]
        cursor.execute("SELECT numero FROM receptions WHERE id=?", (id2,))
        num2 = cursor.fetchone()[0]
        
        print(f"   Reception A: {num1}")
        print(f"   Reception B: {num2}")
        
        assert num1 == "BR-0001-2026"
        assert num2 == "BR-0002-2026"
        
        print("3. Deleting Reception A")
        db_manager.delete_reception(id1)
        
        print("4. Creating Reception C (Should be BR-0003-2026)")
        # If logic is COUNT(*) + 1: Count is 1 (only B exists). Next is 2. Collision with B!
        # If logic is MAX(numero) + 1: Max is 2 (B). Next is 3. Success.
        
        try:
            id3 = db_manager.create_reception(2026, "2026-01-03", "C3", "M3", "T3", "L3", "A3", prod_id, 10, 10, created_by=user_id)
            cursor.execute("SELECT numero FROM receptions WHERE id=?", (id3,))
            num3 = cursor.fetchone()[0]
            print(f"   Reception C: {num3}")
            
            if num3 == "BR-0003-2026":
                print("SUCCESS: Reception C got the correct next number (3). Logic is using MAX.")
            else:
                print(f"FAILURE: Reception C got {num3}. Expected BR-0003-2026.")
                
        except sqlite3.IntegrityError as e:
            print(f"CRITICAL FAILURE: Integrity Error (Collision). Logic is likely still using COUNT. Error: {e}")
            
    finally:
        db_manager.close()
        # Clean up
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(db_path + "-shm"):
                os.remove(db_path + "-shm")
            if os.path.exists(db_path + "-wal"):
                os.remove(db_path + "-wal")
        except:
            pass

if __name__ == "__main__":
    verify_fix()
