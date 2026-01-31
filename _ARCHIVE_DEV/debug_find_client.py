
import sqlite3
from datetime import datetime

DB_PATH = "gestion_commerciale.db"

def inspect_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("--- RECENT AUDIT LOGS (Clients) ---")
        try:
            cursor.execute("SELECT * FROM audit_logs WHERE action LIKE '%client%' ORDER BY timestamp DESC LIMIT 5")
            logs = cursor.fetchall()
            for log in logs:
                print(log)
        except Exception as e:
            print(f"Error reading logs: {e}")

        print("\n--- CLIENTS LIST (First 10) ---")
        cursor.execute("SELECT id, raison_sociale, seuil_credit, solde_creance FROM clients LIMIT 10")
        clients = cursor.fetchall()
        for c in clients:
            print(f"ID: {c[0]}, Name: {c[1]}, Seuil: {c[2]}, Solde (DB Cache): {c[3]}")
            
    except Exception as e:
        print(f"Database error: {e}")

inspect_data()
