"""
Database Migration Service
"""

# Add the service root to Python path for absolute imports
import sys
import os

# Add current directory to Python path to enable absolute imports
service_root = os.path.dirname(os.path.abspath(__file__))
if service_root not in sys.path:
    sys.path.insert(0, service_root)
