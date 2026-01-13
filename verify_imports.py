
import sys
import os

# Add project root to path
sys.path.append("C:\\GICA_PROJET")

print("Attempting to import ui...")
try:
    import ui
    print("SUCCESS: ui imported successfully.")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
except Exception as e:
    print(f"FAILURE: Exception during import: {e}")

print("Attempting to import utils...")
try:
    import utils
    print("SUCCESS: utils imported successfully.")
except Exception as e:
    print(f"FAILURE: utils import error: {e}")

print("Attempting to import main...")
try:
    import main
    print("SUCCESS: main imported successfully.")
except Exception as e:
    print(f"FAILURE: main import error: {e}")
