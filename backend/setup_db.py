#!/usr/bin/env python3
"""
Quick setup script for database initialization
Run this after setting up venv and installing dependencies
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.init_db import init_db

if __name__ == "__main__":
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print()
    
    try:
        init_db()
        print()
        print("=" * 60)
        print("✅ Setup complete!")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Setup failed!")
        print("=" * 60)
        print(f"Error: {e}")
        sys.exit(1)
