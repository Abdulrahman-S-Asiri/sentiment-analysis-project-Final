#!/usr/bin/env python3
"""
Script to create an admin user
Run this script to create an admin user in the database
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import SessionLocal
from backend import models
from passlib.context import CryptContext
from datetime import datetime, date

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(models.User).filter(models.User.email == "admin@admin.com").first()
        
        if admin:
            print("⚠️ Admin user already exists!")
            print(f"   Email: {admin.email}")
            print(f"   Username: {admin.username}")
            print(f"   Role: {admin.role}")
            return
        
        # Create admin user
        hashed_password = pwd_context.hash("admin123")
        
        admin_user = models.User(
            username="admin",
            email="admin@admin.com",
            password=hashed_password,
            date=date(2000, 1, 1),
            gender="other",
            role="admin",
            is_active="active"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@admin.com")
        print(f"   ⚠️ Please change the admin password after first login!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()

