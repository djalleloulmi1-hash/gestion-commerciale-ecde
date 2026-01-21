
import sqlite3
import os
import sys

def find_reception(backup_path):
    if not os.path.exists(backup_path):
        print(f"Backup not found: {backup_path}")
        return None
        
    try:
        conn = sqlite3.connect(backup_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM receptions WHERE numero = 'BR-0011-2026'")
        row = cursor.fetchone()
        
        if row:
            print(f"\n[FOUND] in {backup_path}")
            data = dict(row)
            print(data)
            return data
        else:
            # print(f"Not found in {backup_path}")
            return None
            
    except Exception as e:
        print(f"Error reading {backup_path}: {e}")
        return None

def main():
    backup_dir = r"c:\GICA_PROJET\Backups"
    # List backups reversed (newest first)
    files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')], reverse=True)
    
    found_data = None
    
    print(f"Scanning {len(files)} backups...")
    
    for f in files:
        path = os.path.join(backup_dir, f)
        data = find_reception(path)
        if data:
            found_data = data
            break # Stop at first find (Assuming newest backup has most recent version before delete)
            
    if found_data:
        print("\n--- RECEPTION REPORT ---")
        print(f"Numero: {found_data['numero']}")
        print(f"Date: {found_data['date_reception']}")
        print(f"Produit ID: {found_data['product_id']}")
        print(f"Quantité Reçue: {found_data['quantite_recue']}")
        print(f"Lieu: {found_data['lieu_livraison']}")
        print(f"Chauffeur: {found_data['chauffeur']}")
        print(f"Matricule: {found_data['matricule']}")
        
        # Save to file for easy reading by agent
        with open("reception_found.txt", "w", encoding='utf-8') as f:
            f.write(str(found_data))
    else:
        print("Reception BR-0011-2026 NOT FOUND in any backup.")

if __name__ == "__main__":
    main()
