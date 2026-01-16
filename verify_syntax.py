
import sys
import os

print("Checking syntax...")

try:
    import database
    print("database.py: OK")
except Exception as e:
    print(f"database.py: ERROR - {e}")

try:
    import logic
    print("logic.py: OK")
except Exception as e:
    print(f"logic.py: ERROR - {e}")
    
try:
    import utils
    print("utils.py: OK")
except Exception as e:
    print(f"utils.py: ERROR - {e}")

try:
    # ui imports tkinter so it needs a display, but we can check if it compiles
    # by just loading it. If no display, it might fail on root creation but syntax should be checked by import.
    # However we just want to catch SyntaxError
    import ui
    print("ui.py: OK (Imported)")
except ImportError as e:
    print(f"ui.py: ImportError (Might be deps) - {e}")
except SyntaxError as e:
    print(f"ui.py: SyntaxError - {e}")
except Exception as e:
    # Tkinter might fail to initialize, that's expected in headless but means syntax is OK
    print(f"ui.py: Runtime Error (Expected if no display) - {e}")

print("Verification Complete")
