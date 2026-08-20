import os
import sys

# Append the project root to sys.path to allow absolute imports when running as a script
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.scripts.seed_roles import run as seed_roles
from app.scripts.seed_admin import run as seed_admin

def initialize_database():
    print("\n" + "="*50)
    print("  🚀 Starting Database Initialization 🚀")
    print("="*50 + "\n")
    
    seed_roles()
    seed_admin()
    
    print("="*50)
    print("  ✅ Database Initialization Complete!")
    print("="*50 + "\n")

if __name__ == "__main__":
    initialize_database()
