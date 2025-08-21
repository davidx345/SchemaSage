#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

def check_database():
    """Check database tables and columns"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("No DATABASE_URL found")
        return
    
    print(f"Connecting to: {database_url[:50]}...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check tables
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"Tables: {tables}")
            
            # Check users table columns if it exists
            if 'users' in tables:
                result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public'"))
                columns = [(row[0], row[1], row[2]) for row in result]
                print(f"Users table columns: {columns}")
            else:
                print("Users table does not exist")
                
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_database()
