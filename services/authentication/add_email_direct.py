#!/usr/bin/env python3
import os
import psycopg2
from urllib.parse import urlparse

def add_email_column():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Parse the database URL
        result = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port,
            database=result.path[1:],  # Remove leading slash
            user=result.username,
            password=result.password
        )
        
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully")
        
        # Check if email column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'email'
        """)
        
        email_exists = cursor.fetchone()
        
        if email_exists:
            print("✅ Email column already exists")
        else:
            print("📝 Adding email column...")
            # Add email column
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE")
            conn.commit()
            print("✅ Added email column successfully")
        
        # Verify all columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Current users table columns:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database update completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    add_email_column()
