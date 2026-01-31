try:
    with open('utils.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print("Read with UTF-8 OK.")
    
    non_ascii = [(i+1, c) for i, c in enumerate(content) if ord(c) > 127]
    if non_ascii:
        print(f"Found {len(non_ascii)} non-ASCII characters.")
        for i, c in non_ascii[:10]:
            print(f"Line {content.count('\\n', 0, i)+1}: {c} (U+{ord(c):04X})")
    else:
        print("No non-ASCII characters found.")
        
except Exception as e:
    print(f"Error: {e}")
