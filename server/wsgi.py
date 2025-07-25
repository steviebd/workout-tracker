#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
"""
import os
import sys

# Add the server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

application = create_app()

if __name__ == "__main__":
    application.run()
