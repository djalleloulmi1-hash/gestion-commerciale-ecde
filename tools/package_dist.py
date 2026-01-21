import os
import shutil
import sys

def package():
    dist_dir = "DISTRIBUTION"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # 1. Copy Executable
    src_exe = "dist/main.exe"
    dst_exe = os.path.join(dist_dir, "GestionCommerciale.exe")
    if os.path.exists(src_exe):
        shutil.copy2(src_exe, dst_exe)
        print(f"Copied Executable: {dst_exe}")
    else:
        print("ERROR: dist/main.exe not found!")
        
    # 2. Copy Assets
    assets = [
        "logo_entete.png",
        "logo_gica.png",
        "config.ini",
        "README.md",
        "Manuel_Utilisateur_GICA.docx"
    ]
    
    for asset in assets:
        if os.path.exists(asset):
            shutil.copy2(asset, os.path.join(dist_dir, asset))
            print(f"Copied Asset: {asset}")
        else:
            print(f"WARNING: Asset {asset} not found.")

    # 3. Create Launcher for Exe
    launcher_content = '@echo off\ncd /d "%~dp0"\nstart "" "GestionCommerciale.exe"\nexit'
    with open(os.path.join(dist_dir, "Lancer Application.bat"), "w") as f:
        f.write(launcher_content)
    print("Created Launcher .bat")

    # 4. Create empty directories
    os.makedirs(os.path.join(dist_dir, "Backups"), exist_ok=True)
    os.makedirs(os.path.join(dist_dir, "Rapports"), exist_ok=True)

    print(f"Packaging Complete. Folder: {os.path.abspath(dist_dir)}")

if __name__ == "__main__":
    package()
