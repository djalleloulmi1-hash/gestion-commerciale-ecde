import sys
import os

print("--- Verifying Modules ---")

try:
    print("Importing utils...")
    import utils
    print("PASS: utils imported successfully.")
except Exception as e:
    print(f"FAIL: utils import failed: {e}")
    sys.exit(1)

try:
    print("Importing database...")
    import database
    print("PASS: database imported successfully.")
except Exception as e:
    print(f"FAIL: database import failed: {e}")
    sys.exit(1)

try:
    print("Importing logic...")
    import logic
    print("PASS: logic imported successfully.")
except Exception as e:
    print(f"FAIL: logic import failed: {e}")
    sys.exit(1)

try:
    print("Importing ui...")
    # ui might require tkinter, which is available in python env but let's see if it initializes anything weird on import
    # It usually defines classes, so it should be fine.
    import ui
    print("PASS: ui imported successfully.")
except Exception as e:
    print(f"FAIL: ui import failed: {e}")
    sys.exit(1)

print("--- All critical modules verified ---")
