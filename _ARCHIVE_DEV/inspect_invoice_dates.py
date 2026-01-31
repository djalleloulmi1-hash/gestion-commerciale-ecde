
import sqlite3
import os

DB_PATH = r"C:\GICA_PROJET\gestion_commerciale.db"

def inspect_dates():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("--- All unique date formats found in factures ---")
        cursor.execute("SELECT DISTINCT date_facture FROM factures ORDER BY date_facture DESC LIMIT 20")
        dates = cursor.fetchall()
        for row in dates:
            print(f"Date: '{row[0]}'")

        print("\n--- Checking for part of the string '2026' ---")
        cursor.execute("SELECT id, numero, date_facture FROM factures WHERE date_facture LIKE '%2026%' LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Num: {row[1]}, Date: '{row[2]}'")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_dates()
