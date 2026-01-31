import tkinter as tk
from tkinter import ttk
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

# Mock classes to allow instantiation
class MockDB:
    def get_all_products(self): return []
    def get_all_receptions(self): return []
    def get_all_factures(self): return []
    def get_all_clients(self): return [] # for clients frame if needed
    def get_stock_movements(self, *args): return []

class MockLogic:
    def calculate_client_balance(self, *args): return {'solde': 0}

class MockApp:
    def __init__(self, root):
        self.root = root
        self.db = MockDB()
        self.logic = MockLogic()
        self.user = {'role': 'admin', 'id': 1}

import ui

def verify_frame(frame_class, name):
    print(f"Verifying {name}...")
    root = tk.Tk()
    app = MockApp(root)
    try:
        frame = frame_class(root, app)
        tree = frame.tree
        xscroll = tree.cget("xscrollcommand")
        if xscroll:
            print(f"  [PASS] xscrollcommand is set: {xscroll}")
        else:
            print(f"  [FAIL] xscrollcommand is EMPTY")
    except Exception as e:
        print(f"  [ERROR] Could not instantiate: {e}")
    finally:
        root.destroy()

if __name__ == "__main__":
    print("--- SCROLLBAR VERIFICATION ---")
    verify_frame(ui.ProductsFrame, "ProductsFrame")
    verify_frame(ui.ReceptionsFrame, "ReceptionsFrame")
    verify_frame(ui.InvoicesFrame, "InvoicesFrame")
    # Verify ClientsFrame too just in case
    verify_frame(ui.ClientsFrame, "ClientsFrame")
    print("--- END ---")
