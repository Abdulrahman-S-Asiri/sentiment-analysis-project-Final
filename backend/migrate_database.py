#!/usr/bin/env python3
"""
Database Migration Script
Adds new columns (role, is_active, created_at) to existing database
"""

import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import DATABASE_PATH, engine
from backend import models
from sqlalchemy import text

def migrate_database():
    """Add new columns to existing database"""
    print("Starting database migration...")
    
    # Connect to SQLite database directly
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add role column if it doesn't exist
        if 'role' not in columns:
            print("Adding 'role' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
            print("[OK] Added 'role' column")
        else:
            print("[OK] 'role' column already exists")
        
        # Add is_active column if it doesn't exist
        if 'is_active' not in columns:
            print("Adding 'is_active' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active VARCHAR(10) DEFAULT 'active'")
            print("[OK] Added 'is_active' column")
        else:
            print("[OK] 'is_active' column already exists")
        
        # Add created_at column if it doesn't exist
        if 'created_at' not in columns:
            print("Adding 'created_at' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
            print("[OK] Added 'created_at' column")
        else:
            print("[OK] 'created_at' column already exists")
        
        # Update existing users to have default values
        cursor.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
        cursor.execute("UPDATE users SET is_active = 'active' WHERE is_active IS NULL")

        # Check sentiment_results table columns
        cursor.execute("PRAGMA table_info(sentiment_results)")
        sr_columns = [col[1] for col in cursor.fetchall()]

        if 'emotions_json' not in sr_columns:
            print("Adding 'emotions_json' column...")
            cursor.execute("ALTER TABLE sentiment_results ADD COLUMN emotions_json TEXT")
            print("[OK] Added 'emotions_json' column")
        else:
            print("[OK] 'emotions_json' column already exists")

        if 'explanations_json' not in sr_columns:
            print("Adding 'explanations_json' column...")
            cursor.execute("ALTER TABLE sentiment_results ADD COLUMN explanations_json TEXT")
            print("[OK] Added 'explanations_json' column")
        else:
            print("[OK] 'explanations_json' column already exists")

        conn.commit()
        print("\n[OK] Database migration completed successfully!")
        
        # Create admin user if it doesn't exist
        cursor.execute("SELECT id FROM users WHERE email = 'admin@admin.com'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            print("\nCreating admin user...")
            import bcrypt
            from datetime import datetime, date
            
            # Hash password using bcrypt directly
            password = "admin123".encode('utf-8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO users (username, email, password, date, gender, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("admin", "admin@admin.com", hashed_password, "2000-01-01", "other", "admin", "active", current_time))
            
            conn.commit()
            print("[OK] Admin user created!")
            print("   Email: admin@admin.com")
            print("   Password: admin123")
            print("   [WARNING] Please change the password after first login!")
        else:
            # Update existing admin to have admin role
            cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@admin.com'")
            conn.commit()
            print("\n[OK] Admin user already exists (role updated)")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

