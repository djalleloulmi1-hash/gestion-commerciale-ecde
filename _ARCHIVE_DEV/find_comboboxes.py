
import re

filename = r"c:\GICA_PROJET\ui.py"

try:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    print(f"Scanning {len(lines)} lines in {filename}...")
    
    count = 0
    for i, line in enumerate(lines):
        if "Combobox" in line:
            print(f"Line {i+1}: {line.strip()}")
            count += 1
            
    print(f"Found {count} occurrences.")
    
except Exception as e:
    print(f"Error: {e}")
