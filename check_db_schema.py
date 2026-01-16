
import sqlite3
import os

db_path = "gestion_commerciale.db"

if not os.path.exists(db_path):
    print(f"Database file {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Checking 'factures' table info:")
    cursor.execute("PRAGMA table_info(factures)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns: {columns}")
    
    if 'statut' in columns:
        print("PASS: 'statut' column exists.")
    else:
        print("FAIL: 'statut' column MISSING.")
        
    if 'motif_annulation' in columns:
        print("PASS: 'motif_annulation' column exists.")
    else:
        print("FAIL: 'motif_annulation' column MISSING.")

    print("\nChecking 'journal_annulations' table:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_annulations'")
    if cursor.fetchone():
        print("PASS: 'journal_annulations' table exists.")
    else:
        print("FAIL: 'journal_annulations' table MISSING.")
        
    conn.close()
