#!/usr/bin/env python3
"""
Debug script to test database creation without Docker
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, '.')
sys.path.insert(0, './server')

# Load environment variables
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env', override=True)
        print("✅ Loaded .env file")
    else:
        print("❌ No .env file found")
        sys.exit(1)
except ImportError:
    print("❌ python-dotenv not installed")
    sys.exit(1)

print(f"📁 Current working directory: {os.getcwd()}")
print(f"🌍 FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
print(f"🌍 DATABASE_PATH: {os.environ.get('DATABASE_PATH', 'not set')}")

# Test database path resolution
try:
    from server.db import DB_PATH
    print(f"🗄️  Resolved database path: {DB_PATH}")
    
    # Check if path is absolute or relative
    if os.path.isabs(DB_PATH):
        print("✅ Database path is absolute")
    else:
        print("⚠️  Database path is relative")
        abs_path = os.path.abspath(DB_PATH)
        print(f"🔄 Absolute path would be: {abs_path}")
    
    # Check directory
    db_dir = os.path.dirname(DB_PATH)
    print(f"📂 Database directory: {db_dir}")
    
    if db_dir:
        if os.path.exists(db_dir):
            print(f"✅ Database directory exists")
            # Check permissions
            if os.access(db_dir, os.W_OK):
                print("✅ Database directory is writable")
            else:
                print("❌ Database directory is not writable")
        else:
            print(f"⚠️  Database directory does not exist")
            print(f"🔧 Attempting to create: {db_dir}")
            try:
                os.makedirs(db_dir, exist_ok=True)
                print("✅ Database directory created successfully")
            except Exception as e:
                print(f"❌ Failed to create directory: {e}")
    
    # Test database creation
    print(f"🧪 Testing database creation...")
    try:
        import sqlite3
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ Database connection successful")
            if tables:
                print(f"📋 Found {len(tables)} tables: {[t[0] for t in tables]}")
            else:
                print("📋 Database is empty (no tables)")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        
except Exception as e:
    print(f"❌ Failed to import database module: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Debug complete")
