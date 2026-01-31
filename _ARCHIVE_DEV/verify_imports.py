
import sys
import traceback

print("Checking imports...")

try:
    print("Importing main...")
    import main
except Exception:
    traceback.print_exc()

try:
    print("Importing utils...")
    import utils
except Exception:
    traceback.print_exc()
    
try:
    print("Importing reports...")
    import reports
except Exception:
    traceback.print_exc()

try:
    print("Importing word_exports...")
    import word_exports
except Exception:
    traceback.print_exc()

try:
    print("Importing ui...")
    import ui
except Exception:
    traceback.print_exc()
    
try:
    print("Importing database...")
    import database
except Exception:
    traceback.print_exc()

try:
    print("Importing logic...")
    import logic
except Exception:
    traceback.print_exc()
    
print("Check complete.")
