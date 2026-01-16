
from logic import BusinessLogic

def fix_stocks():
    print("Running Global Stock Recalculation...")
    logic = BusinessLogic()
    stats = logic.recalculate_global_stock()
    print("Recalculation Complete.")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    fix_stocks()
