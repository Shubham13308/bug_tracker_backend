from datetime import datetime, timezone
from app.database.mongodb import db
from app.core.security import hash_password

user_collection = db["users"]
role_collection = db["roles"]

def run():
    print("Seeding admin user...")
    admin_email = "admin@example.com"
    
    existing_user = user_collection.find_one({"email": admin_email})
    if existing_user:
        print(f"  [-] Skipped admin user - {admin_email} already exists.\n")
        return
        
    admin_role = role_collection.find_one({"name": "admin"})
    if not admin_role:
        print("  [x] Error: Admin role not found. Please seed roles first.\n")
        return
        
    now = datetime.now(timezone.utc)
    
    user_collection.insert_one({
        "name": "System Administrator",
        "email": admin_email,
        "password": hash_password("Admin@123"),
        "role_id": admin_role["_id"],
        "is_active": True,
        "created_at": now,
        "updated_at": now
    })
    
    print(f"  [✔] Created admin user: {admin_email} / Admin@123\n")

if __name__ == "__main__":
    run()
