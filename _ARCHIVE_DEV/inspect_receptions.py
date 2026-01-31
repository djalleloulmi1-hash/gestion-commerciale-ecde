import sqlite3

DB_PATH = "gestion_commerciale.db"

def check_receptions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Inspecting Receptions for 'None' or NULL entries...")
    
    # Check for numero = 'None' or NULL
    cursor.execute("SELECT * FROM receptions WHERE numero = 'None' OR numero IS NULL")
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} row(s) with numero = 'None' or NULL:")
        for row in rows:
            print(dict(row))
    else:
        print("No rows found with numero = 'None' or NULL.")
        
        # Check other columns just in case
        print("Checking first 5 rows to see what data looks like:")
        cursor.execute("SELECT * FROM receptions LIMIT 5")
        for row in cursor.fetchall():
            print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_receptions()
