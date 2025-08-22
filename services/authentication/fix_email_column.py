#!/usr/bin/env python3

import os
import psycopg2
from psycopg2 import sql

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.jscwpzhloxdnyvhcriiq:ayodele3579@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

def add_email_column():
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Add email column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255);")
            print("✅ Added email column")
        except psycopg2.errors.DuplicateColumn:
            print("ℹ️ Email column already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\nUsers table columns after update:")
        for column in columns:
            print(f"  {column}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Email column added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_email_column()
