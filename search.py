#!/usr/bin/env python3
"""
SnapChronicles Search - Quick Access Script

Simple wrapper to launch the database search CLI from the project root.

Usage:
    python search.py
    
This script launches the interactive search interface for querying your
captured screenshots and audio transcriptions using natural language.
"""

import sys
import os

# Add src to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import and run the search CLI
try:
    from database.search_cli import main
    
    if __name__ == "__main__":
        exit_code = main()
        sys.exit(exit_code)
        
except ImportError as e:
    print(f"❌ Error importing search CLI: {e}")
    print("Make sure you're running this from the SnapChronicles root directory.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running search CLI: {e}")
    sys.exit(1) 