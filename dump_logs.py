import sqlite3
import pandas as pd
from database import DatabaseManager

db = DatabaseManager()
conn = db._get_connection()

print("=== AUDIT LOGS (Last 20) ===")
try:
    df_audit = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 20", conn)
    print(df_audit.to_string())
except Exception as e:
    print(f"Error reading audit_logs: {e}")

print("\n=== STOCK MOVEMENTS (Last 20) ===")
try:
    df_move = pd.read_sql_query("SELECT * FROM stock_movements ORDER BY created_at DESC LIMIT 20", conn)
    print(df_move.to_string())
except Exception as e:
    print(f"Error reading stock_movements: {e}")
