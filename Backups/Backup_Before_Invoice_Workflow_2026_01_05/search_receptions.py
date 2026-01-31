import sqlite3

DB_PATH = "gestion_commerciale.db"

def search_receptions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Searching ALL columns in Receptions for 'None' or '(None)'...")
    
    cursor.execute("SELECT * FROM receptions")
    columns = [description[0] for description in cursor.description]
    
    found_count = 0
    for row in cursor.fetchall():
        row_dict = dict(row)
        found_in_row = False
        for col, val in row_dict.items():
            s_val = str(val)
            if "None" in s_val or "(None)" in s_val:
                print(f"Found match in ID {row['id']}, Column '{col}': {val}")
                found_in_row = True
        
        if found_in_row:
            print(f"Full Row: {row_dict}")
            found_count += 1
            print("-" * 40)
            
    if found_count == 0:
        print("No matches found for 'None' in any column.")

    conn.close()

if __name__ == "__main__":
    search_receptions()
