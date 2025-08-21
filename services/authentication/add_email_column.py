#!/usr/bin/env python3
import os
import psycopg2
from urllib.parse import urlparse

def add_email_column():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        # Connect to the database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        
        print("✅ Connected to database successfully")
        
        cursor = conn.cursor()
        
        # Check if email column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'email'
        """)
        
        if cursor.fetchone():
            print("✅ email column already exists")
        else:
            # Add email column
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE")
            print("✅ Added email column")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Email column migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    add_email_column()
