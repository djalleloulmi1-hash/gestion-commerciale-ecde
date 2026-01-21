import sqlite3
from logic import BusinessLogic
# Mock DB Wrapper
class MockDB:
    def __init__(self):
        self.conn = sqlite3.connect('gestion_commerciale.db')
    def _get_connection(self):
        return self.conn

def verify_logic():
    print("--- Verifying Real-Time Logic ---")
    mock_db = MockDB()
    logic = BusinessLogic()
    logic.db = mock_db # Inject mock
    
    # 1. Pick a product (e.g. 38)
    pid = 38
    cursor = mock_db.conn.cursor()
    
    # 2. Get True calc
    cursor.execute("SELECT SUM(quantite) FROM stock_movements WHERE product_id=?", (pid,))
    true_stock = cursor.fetchone()[0]
    print(f"True Stock (Movements): {true_stock}")
    
    # 3. Sabotage Cache
    fake_stock = -999.0
    cursor.execute("UPDATE products SET stock_actuel = ? WHERE id = ?", (fake_stock, pid))
    mock_db.conn.commit()
    print(f"Sabotaged Cache to: {fake_stock}")
    
    # 4. Run Logic
    print("Running get_real_time_stock()...")
    result = logic.get_real_time_stock(pid)
    print(f"Result returned: {result}")
    
    # 5. Check if healed
    cursor.execute("SELECT stock_actuel FROM products WHERE id = ?", (pid,))
    new_cache = cursor.fetchone()[0]
    print(f"New Cache Value: {new_cache}")
    
    if abs(new_cache - true_stock) < 0.001 and abs(result - true_stock) < 0.001:
        print("SUCCESS: Logic correctly calculated real stock and healed the cache.")
    else:
        print("FAILURE: System did not heal or calculate correctly.")

if __name__ == "__main__":
    verify_logic()
