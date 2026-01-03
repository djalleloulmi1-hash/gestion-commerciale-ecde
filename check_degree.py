try:
    with open('utils.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.splitlines()
    found = False
    for line_idx, line in enumerate(lines):
        for char_idx, char in enumerate(line):
            if ord(char) == 0xB0: # Degree sign
                print(f"Found Degree Sign at Line {line_idx+1}, Col {char_idx+1}: {line.strip()}")
                found = True
    
    if not found:
        print("No degree signs found.")
        
except Exception as e:
    print(f"Error: {e}")
