from typing import Optional
# pyrefly: ignore [missing-import]
from bson import ObjectId
from app.database.mongodb import db

role_collection = db['roles']

def get_role_by_id(role_id: str) -> Optional[dict]:
    """Retrieve a role by its ID."""
    try:
        return role_collection.find_one({"_id": ObjectId(role_id)})
    except Exception:
        return None

def create_role_in_db(role_data: dict) -> dict:
    """Insert a new role into the database."""
    result = role_collection.insert_one(role_data)
    role_data["_id"] = result.inserted_id
    return role_data

def get_all_roles_from_db() -> list:
    """Retrieve all roles from the database."""
    return list(role_collection.find())
