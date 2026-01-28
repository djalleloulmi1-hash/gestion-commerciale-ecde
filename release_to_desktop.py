
import os
import shutil
import sys
import subprocess
import configparser

def release_to_desktop():
    print("=== Starting Release Process ===")
    
    # 1. Define Paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    desktop_dir = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    release_folder_name = "GESTION COMMERCIALE 2026"
    release_path = os.path.join(desktop_dir, release_folder_name)
    
    dist_dir = os.path.join(project_dir, 'dist')
    build_dir = os.path.join(project_dir, 'build')
    
    # 2. Clean Previous Builds
    print("Cleaning previous builds...")
    if os.path.exists(dist_dir):
        try:
            shutil.rmtree(dist_dir)
        except Exception as e:
            print(f"Warning: Could not remove {dist_dir}: {e}")
            
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
        except Exception as e:
            print(f"Warning: Could not remove {build_dir}: {e}")

    # 3. Build Executable
    print("Building executable with PyInstaller...")
    # Use the existing spec file
    spec_file = os.path.join(project_dir, "GestionCommerciale_GICA.spec")
    
    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found at {spec_file}")
        return False

    try:
        subprocess.check_call([sys.executable, "-m", "PyInstaller", spec_file])
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        return False
        
    # 4. Prepare Destination
    print(f"Preparing destination: {release_path}")
    if not os.path.exists(release_path):
        os.makedirs(release_path)
        
    # 5. Copy Files
    print("Copying files...")
    
    # Executable
    src_exe = os.path.join(dist_dir, "GestionCommerciale_GICA.exe") # Name from spec
    dst_exe = os.path.join(release_path, "GESTION COMMERCIALE.exe") # Desired name
    
    if os.path.exists(src_exe):
        shutil.copy2(src_exe, dst_exe)
        print(f"Executable copied to: {dst_exe}")
    else:
        print(f"Error: Built executable not found at {src_exe}")
        return False
        
    # Database (Copy the active one)
    # Determine active DB from config or default
    db_path = os.path.join(project_dir, "gestion_commerciale.db")
    # Verify if config points elsewhere
    config_path = os.path.join(project_dir, "config.ini")
    if os.path.exists(config_path):
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
        if 'DATABASE' in cfg and 'path' in cfg['DATABASE']:
            conf_db = cfg['DATABASE']['path']
            # If absolute path, use it
            if os.path.isabs(conf_db):
                 if os.path.exists(conf_db):
                     db_path = conf_db
            else:
                 # logical path inside project
                 full_p = os.path.join(project_dir, conf_db)
                 if os.path.exists(full_p):
                     db_path = full_p

    dst_db = os.path.join(release_path, "gestion_commerciale.db")
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, dst_db)
        print(f"Database copied from {db_path} to {dst_db}")
    else:
        print(f"Warning: Database source not found at {db_path}. created empty placeholder?")
        
    # Config File (Create Portable Config)
    dst_config = os.path.join(release_path, "config.ini")
    with open(dst_config, 'w') as f:
        f.write("[DATABASE]\n")
        f.write("path = gestion_commerciale.db\n") # Relative path for portability
    print("Created portable config.ini")

    # 6. Create Subdirectories
    print("Creating structure...")
    folders = ["Backups", "Rapports", "Exports"]
    for f in folders:
        os.makedirs(os.path.join(release_path, f), exist_ok=True)
        
    # Exports subfolders
    for f in ["Exports_Word", "Exports_Excel", "Exports_PDF"]:
        os.makedirs(os.path.join(release_path, "Exports", f), exist_ok=True)

    print("=== Release Process Completed Successfully ===")
    return True

if __name__ == "__main__":
    release_to_desktop()
