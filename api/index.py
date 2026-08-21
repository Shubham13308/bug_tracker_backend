import sys
import os

# Add root directory to sys.path for Vercel Serverless Functions
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Compatibility monkey-patch for passlib with newer bcrypt versions on Vercel
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        class About:
            __version__ = getattr(bcrypt, "__version__", "4.0.1")
        bcrypt.__about__ = About()
except Exception:
    pass

from app.main import app
