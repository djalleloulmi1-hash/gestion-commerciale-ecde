
import sqlite3
from logic import BusinessLogic
from database import DatabaseManager

# Initialize Logic
# Note: logic.py uses get_db() which might need proper setup, 
# but BusinessLogic class initializes with get_db()
# We need to make sure we can instantiate it.

# mocking get_db if needed or just use DatabaseManager directly
# logic.py: from database import get_db

def verify_balance():
    logic = BusinessLogic()
    client_id = 1
    
    print(f"--- Calculating Balance for Client ID: {client_id} ---")
    
    try:
        # Get detailed breakdown
        balance_info = logic.calculate_client_balance(client_id)
        
        print(f"Report N-1: {balance_info['report']:,.2f}")
        print(f"Total Paiements: {balance_info['total_paiements']:,.2f}")
        print(f"Total Avoirs: {balance_info['total_avoirs']:,.2f}")
        print(f"Total Factures: {balance_info['total_factures']:,.2f}")
        print(f"Solde Calculé: {balance_info['solde']:,.2f}")
        
        # Get Client Details from DB to compare
        client = logic.db.get_client_by_id(client_id)
        print(f"Solde Cache (DB): {client['solde_creance']:,.2f}")
        print(f"Seuil Crédit: {client['seuil_credit']:,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_balance()
