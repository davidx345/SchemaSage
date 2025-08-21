#!/usr/bin/env python3
"""
Database migration script to add missing columns for Google OAuth
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    exit(1)

def run_migration():
    """Add missing columns for Google OAuth"""
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('google_id', 'email', 'full_name');
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add google_id column if it doesn't exist
        if 'google_id' not in existing_columns:
            print("Adding google_id column...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN google_id VARCHAR(255) UNIQUE;
            """)
            print("✅ Added google_id column")
        else:
            print("✅ google_id column already exists")
        
        # Add email column if it doesn't exist
        if 'email' not in existing_columns:
            print("Adding email column...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN email VARCHAR(255) UNIQUE;
            """)
            print("✅ Added email column")
        else:
            print("✅ email column already exists")
        
        # Add full_name column if it doesn't exist
        if 'full_name' not in existing_columns:
            print("Adding full_name column...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN full_name VARCHAR(255);
            """)
            print("✅ Added full_name column")
        else:
            print("✅ full_name column already exists")
        
        # Also make hashed_password nullable for OAuth users
        print("Making hashed_password nullable...")
        cursor.execute("""
            ALTER TABLE users 
            ALTER COLUMN hashed_password DROP NOT NULL;
        """)
        print("✅ Made hashed_password nullable")
        
        print("\n🎉 Database migration completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        exit(1)

if __name__ == "__main__":
    run_migration()
