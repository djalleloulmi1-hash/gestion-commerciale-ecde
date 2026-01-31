import os
import shutil
import sys

def migrate_project(src, dst):
    # Exclusions
    ignore_patterns = shutil.ignore_patterns(
        '.git', 
        'Backups', 
        'build', 
        'dist', 
        '__pycache__', 
        '*.spec', 
        'venv', 
        '.idea', 
        '.vscode',
        '*.tmp'
    )

    print(f"Migration de {src} vers {dst}...")

    if os.path.exists(dst):
        print(f"Le dossier destination {dst} existe dejà. Nettoyage rapide (fichiers sources uniquement)...")
        # On ne supprime pas tout brutalement au cas où, on écrase.
    
    try:
        # Copy tree with ignore
        # shutil.copytree requires dst to NOT exist usually, or use dirs_exist_ok=True (Python 3.8+)
        # We'll use dirs_exist_ok=True
        shutil.copytree(src, dst, ignore=ignore_patterns, dirs_exist_ok=True)
        print("Migration terminée avec succès !")
        print(f"Fichiers copiés dans : {dst}")
    except Exception as e:
        print(f"Erreur lors de la copie : {e}")

if __name__ == "__main__":
    src_dir = os.getcwd()
    dst_dir = r"C:\GICA_PROJET"
    migrate_project(src_dir, dst_dir)
