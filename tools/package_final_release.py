import os
import shutil
import sys

def package_final():
    # Target Directory Name Requested by User
    dist_dir_name = "GESTION ECDE 2026"
    
    # Ensure we are in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(project_root, dist_dir_name)
    
    print(f"Packaging to: {target_dir}")
    
    # 1. Clean/Create Directory
    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
            print("Removed existing directory.")
        except Exception as e:
            print(f"Warning: Could not remove existing directory (might be open): {e}")
            
    os.makedirs(target_dir, exist_ok=True)
    
    # 2. Copy Executable from dist/
    src_exe = os.path.join(project_root, "dist", "main.exe")
    dst_exe = os.path.join(target_dir, "GestionCommerciale.exe")
    
    if os.path.exists(src_exe):
        shutil.copy2(src_exe, dst_exe)
        print(f"Copied Executable: {dst_exe}")
    else:
        print("ERROR: dist/main.exe not found! Compile first.")
        return

    # 3. Copy Assets & Database
    assets = [
        "logo_entete.png",
        "logo_gica.png",
        "config.ini",
        "README.md",
        "Manuel_Utilisateur_GICA.docx",
        "gestion_commerciale.db" # Crucial Request: Include Database
    ]
    
    for asset in assets:
        src = os.path.join(project_root, asset)
        dst = os.path.join(target_dir, asset)
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"Copied Asset: {asset}")
            except PermissionError:
                print(f"WARNING: Could not copy {asset}. Is it open?")
        else:
            print(f"WARNING: Asset {asset} not found.")

    # 4. Create Launcher .bat
    launcher_content = '@echo off\ncd /d "%~dp0"\nstart "" "GestionCommerciale.exe"\nexit'
    with open(os.path.join(target_dir, "Lancer Application.bat"), "w") as f:
        f.write(launcher_content)
    print("Created Launcher .bat")

    # 5. Create Support Directories
    os.makedirs(os.path.join(target_dir, "Backups"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "Rapports"), exist_ok=True)
    
    print(f"SUCCESS: Package created at {target_dir}")

if __name__ == "__main__":
    package_final()
