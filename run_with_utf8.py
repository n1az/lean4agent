"""
Helper script to run tests with proper UTF-8 encoding on Windows.
"""

import sys
import os

# Force UTF-8 encoding before any imports
if sys.platform == 'win32':
    # Set console to UTF-8 mode
    os.system('chcp 65001 >nul 2>&1')
    
    # Set environment variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Reconfigure streams
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')

# Now run the actual test
if __name__ == "__main__":
    import test_incremental
