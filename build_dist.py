import os
import shutil
import sys
import time

def build_distribution():
    print("Starting distribution build...")
    
    # Paths
    project_dir = r"c:\GICA_PROJET"
    dist_dir = os.path.join(project_dir, "dist", "GestionCommerciale_GICA")
    # If one-file mode (exe inside dist directly) or one-dir mode
    # Based on SPEC file: console=False, but didn't see if it was --onedir or --onefile. 
    # Usually default is --onedir. The SPEC file had `coll = COLLECT(...)` which implies --onedir.
    
    output_dir = os.path.join(project_dir, "GESTION ECDE 2026")
    
    # Source files
    exe_source = os.path.join(dist_dir, "GestionCommerciale_GICA.exe")
    db_source = os.path.join(project_dir, "gestion_commerciale.db")
    config_source = os.path.join(project_dir, "config.ini")
    
    # Destination files
    exe_dest = os.path.join(output_dir, "GestionCommerciale.exe")
    db_dest = os.path.join(output_dir, "gestion_commerciale.db")
    config_dest = os.path.join(output_dir, "config.ini")
    
    # 1. Create Output Directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # 2. Copy Executable/Folder
    # Since it's likely a directory (COLL in spec), we need to copy the whole content of dist_dir to output_dir
    # But wait, usually we want a clean single folder.
    # Let's check if dist_dir exists first
    if os.path.exists(dist_dir):
        print(f"Found distribution directory: {dist_dir}")
        # It's a directory build (onedir). We should copy ALL contents of dist_dir to output_dir
        # But we want to name the exe "GestionCommerciale.exe"
        
        # Method: Copy all items from dist/GestionCommerciale_GICA/* to output_dir/
        for item in os.listdir(dist_dir):
            s = os.path.join(dist_dir, item)
            d = os.path.join(output_dir, item)
            if item == "GestionCommerciale_GICA.exe":
                d = os.path.join(output_dir, "GestionCommerciale.exe")
            
            if os.path.isdir(s):
                if os.path.exists(d): 
                    # shutil.copytree requires destination to not exist usually, or use dirs_exist_ok in 3.8+
                    # simpler to skip or merge
                    pass 
                # For safety, let's just copy files. Actually dependencies are needed.
                # Let's use robocopy or simple copytree
                try:
                    shutil.copytree(s, d, dirs_exist_ok=True)
                except Exception as e:
                    print(f"Error copying dir {item}: {e}")
            else:
                shutil.copy2(s, d)
                
        print("Copied application files.")
    else:
        print(f"Error: Could not find build output at {dist_dir}")
        # Fallback check for onefile
        onefile_exe = os.path.join(project_dir, "dist", "GestionCommerciale_GICA.exe")
        if os.path.exists(onefile_exe):
             print(f"Found single file executable: {onefile_exe}")
             shutil.copy2(onefile_exe, exe_dest)
        else:
            return False

    # 3. Copy Database
    if os.path.exists(db_source):
        shutil.copy2(db_source, db_dest)
        print(f"Copied database to {db_dest}")
    else:
        print("Warning: Database source not found!")

    # 4. Copy Config
    if os.path.exists(config_source):
        shutil.copy2(config_source, config_dest)
        print(f"Copied config to {config_dest}")
        
    # 5. Create 'Rapports' folder
    reports_dir = os.path.join(output_dir, "Rapports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        
    # 6. Create 'Exports' folders
    for sub in ["Exports_Word", "Exports_Excel", "Exports_PDF"]:
        p = os.path.join(output_dir, "Exports", sub)
        os.makedirs(p, exist_ok=True)

    print("Distribution build completed.")
    return True

if __name__ == "__main__":
    build_distribution()
