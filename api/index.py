import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from app import app
except ImportError:
    # Fallback import method
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import app

# Export the Flask app for Vercel
# Vercel will automatically detect and use this