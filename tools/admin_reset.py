import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager

def reset_admin():
    db = DatabaseManager()
    
    username = "admin"
    password = "admin" # Requested by user
    
    # Check if user exists
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    
    hashed_pwd = db.hash_password(password)
    
    if row:
        user_id = row[0]
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pwd, user_id))
        conn.commit()
        print(f"SUCCESS: Password for user '{username}' has been updated to '{password}'.")
    else:
        db.create_user(username, password, "Administrateur", "admin")
        print(f"SUCCESS: User '{username}' created with password '{password}'.")
        
    db.close()

if __name__ == "__main__":
    reset_admin()
