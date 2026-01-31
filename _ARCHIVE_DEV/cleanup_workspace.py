import os
import shutil

# Files essential for the application runtime
CRITICAL_FILES = {
    'main.py',
    'ui.py',
    'database.py',
    'logic.py',
    'utils.py',
    'reports.py',
    'word_exports.py',
    'cleanup_workspace.py' # Don't move self while running
}

ARCHIVE_DIR = '_ARCHIVE_DEV'

def clean_workspace():
    # Create archive directory if it doesn't exist
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
        print(f"Created archive directory: {ARCHIVE_DIR}")

    # Get all python files in current directory
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
    
    moved_count = 0
    
    for file in files:
        if file not in CRITICAL_FILES:
            try:
                src = file
                dst = os.path.join(ARCHIVE_DIR, file)
                
                # If file already exists in archive, overwrite or skip? 
                # Let's overwrite to ensure we move the current one
                if os.path.exists(dst):
                    os.remove(dst)
                    
                shutil.move(src, dst)
                print(f"Moved: {file} -> {ARCHIVE_DIR}/")
                moved_count += 1
            except Exception as e:
                print(f"Error moving {file}: {e}")

    print(f"\nCleanup Complete.")
    print(f"Total files moved: {moved_count}")
    print(f"Critical files preserved: {len(CRITICAL_FILES) - 1}") # -1 for self

if __name__ == "__main__":
    clean_workspace()
