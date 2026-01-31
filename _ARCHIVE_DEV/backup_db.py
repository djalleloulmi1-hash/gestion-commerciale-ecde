from database import DatabaseManager
import os

print("Creating Database Backup...")
db = DatabaseManager()
success, path = db.export_miroir("c:\\GICA_PROJET\\backups")
if success:
    print(f"Backup created successfully at: {path}")
else:
    print(f"Backup failed: {path}")
