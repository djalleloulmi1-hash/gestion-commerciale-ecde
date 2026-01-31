import inspect
from logic import BusinessLogic
from database import DatabaseManager

print("Methods in BusinessLogic:")
for name, method in inspect.getmembers(BusinessLogic, predicate=inspect.isfunction):
    print(f"- {name}")

# Try to replicate the calculation for a client with negative balance
# We need to find one first
db = DatabaseManager()
conn = db._get_connection()
c = conn.cursor()
c.execute("SELECT id, raison_sociale, report_n_moins_1 FROM clients")
clients = c.fetchall()

found = False
for client in clients:
    if client['report_n_moins_1'] and client['report_n_moins_1'] < 0:
        print(f"\nAnalyzing Client: {client['raison_sociale']} (ID: {client['id']})")
        print(f"Report N-1: {client['report_n_moins_1']}")
        
        logic = BusinessLogic()
        
        # 1. Call standard balance
        try:
            bal = logic.calculate_client_balance(client['id'])
            print(f"Standard Balance: {bal}")
        except AttributeError:
            print("calculate_client_balance NOT FOUND")
        
        # 2. Call new annual logic
        start_year = "2026-01-01" # Assuming 2026
        import datetime
        date_n = datetime.datetime.now().strftime("%Y-%m-%d")
        
        data = logic.get_annual_receivables_data(date_n)
        for row in data['data']:
            if row['raison_sociale'] == client['raison_sociale']:
                print(f"Annual Report Calculation: {row}")
                found = True
                break
        if found: break

if not found:
    print("No client with negative report found for testing.")
