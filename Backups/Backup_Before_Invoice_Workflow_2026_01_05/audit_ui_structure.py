import re

def audit_ui_structure(filename="ui.py"):
    print(f"Auditing {filename} for structure issues...")
    issues = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_class = None
    current_method = None
    method_indent = 0
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        if not stripped or stripped.startswith('#'): continue
        
        # Detect Class
        if stripped.startswith("class "):
            current_class = stripped.split('(')[0].replace('class ', '').strip()
            current_method = None
            
        # Detect Method
        elif stripped.startswith("def "):
            method_name = stripped.split('(')[0].replace('def ', '').strip()
            
            # Check for excessive indentation (Nested functions)
            # Standard method indent inside class is usually 4 spaces (class) + 4 spaces (def) = 8
            # or 0 + 4 = 4 if no class.
            
            if current_class:
                expected_indent = 4
                if indent > expected_indent:
                     issues.append(f"Line {line_num}: Nested function or bad indentation detected: '{method_name}' at indent {indent} (Expected 4 inside class)")
            else:
                 if indent > 0:
                      issues.append(f"Line {line_num}: Function '{method_name}' indented at top level.")

    if issues:
        print(f"FOUND {len(issues)} STRUCTURAL ISSUES:")
        for i in issues:
            print(i)
    else:
        print("Structure seems OK (No obvious nested functions detected).")

if __name__ == "__main__":
    audit_ui_structure()
