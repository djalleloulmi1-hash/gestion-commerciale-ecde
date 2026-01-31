from database import DatabaseManager

db = DatabaseManager()
# Invoice 5 was created in verify_contracts.py linked to a contract
inv = db.get_facture_by_id(5)

if inv:
    print("Contract Code:", inv.get('contract_code'))
    print("Contract Start:", inv.get('contract_debut'))
    print("Contract End:", inv.get('contract_fin'))
    
    if inv.get('contract_code'):
        print("SUCCESS: Contract fields found.")
    else:
        print("FAILURE: Contract fields missing.")
else:
    print("Invoice 5 not found (maybe verify_contracts.py cleared DB or used different IDs).")
