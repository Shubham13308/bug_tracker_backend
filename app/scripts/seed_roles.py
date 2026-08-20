from datetime import datetime, timezone
from app.database.mongodb import db

role_collection = db["roles"]
permission_collection = db["permissions"]

ROLES = {
    "admin": {
        "description": "Full access to all modules.",
        "permissions": ["*"] # Denotes all permissions
    },
    "project manager": {
        "description": "Can manage projects, issues and view users/roles.",
        "permissions": [
            "project:create", "project:view", "project:update", "project:delete",
            "issue:create", "issue:view", "issue:update", "issue:delete",
            "issue:assign", "issue:change_status",
            "user:view", "role:view"
        ]
    },
    "developer": {
        "description": "Can work on issues and view projects.",
        "permissions": [
            "project:view",
            "issue:create", "issue:view", "issue:update", "issue:delete",
            "issue:assign", "issue:change_status"
        ]
    },
    "tester": {
        "description": "Can work on issues and view projects.",
        "permissions": [
            "project:view",
            "issue:create", "issue:view", "issue:update", "issue:delete",
            "issue:change_status"
        ]
    },
    "viewer": {
        "description": "Read-only access to projects and issues.",
        "permissions": [
            "project:view", "issue:view"
        ]
    }
}

def run():
    print("Seeding roles...")
    now = datetime.now(timezone.utc)

    for role_name, config in ROLES.items():
        existing = role_collection.find_one({"name": role_name})
        
        perm_ids = config["permissions"]
        
        if not existing:
            role_collection.insert_one({
                "name": role_name,
                "description": config["description"],
                "permissions": perm_ids,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            })
            print(f"  [✔] Created role: {role_name}")
        else:
            # Sync permissions if role already exists
            role_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"permissions": perm_ids, "updated_at": now}}
            )
            print(f"  [~] Updated role: {role_name} (permissions synced)")
            
    print("Successfully seeded roles.\n")

if __name__ == "__main__":
    run()
