# pyrefly: ignore [missing-import]
from bson import ObjectId
from app.database.mongodb import db

permission_collection = db["permissions"]


def create_permission(permission_data: dict):
    return permission_collection.insert_one(permission_data)


def get_permission_by_id(permission_id: str):
    if not ObjectId.is_valid(permission_id):
        return None
    return permission_collection.find_one(
        {
            "_id": ObjectId(permission_id),
            "is_active": True,
        }
    )


def get_permission_by_name(name: str):
    return permission_collection.find_one(
        {
            "name": name,
            "is_active": True,
        }
    )


def get_permission_by_permission(permission: str):
    return permission_collection.find_one(
        {
            "permission": permission,
            "is_active": True,
        }
    )


def get_permissions():
    return list(
        permission_collection.find(
            {
                "is_active": True
            }
        ).sort(
            "module",
            1,
        )
    )


def get_permissions_by_ids(permission_ids: list):
    """Retrieve multiple permissions by their IDs."""
    if not permission_ids:
        return []
    object_ids = []
    for pid in permission_ids:
        if isinstance(pid, ObjectId):
            object_ids.append(pid)
        elif isinstance(pid, str) and ObjectId.is_valid(pid):
            object_ids.append(ObjectId(pid))
    return list(permission_collection.find({"_id": {"$in": object_ids}, "is_active": True}))


def update_permission(
    permission_id: str,
    update_data: dict,
):
    if not ObjectId.is_valid(permission_id):
        return None
    return permission_collection.update_one(
        {
            "_id": ObjectId(permission_id)
        },
        {
            "$set": update_data
        },
    )


def soft_delete_permission(permission_id: str):
    if not ObjectId.is_valid(permission_id):
        return None
    return permission_collection.update_one(
        {
            "_id": ObjectId(permission_id)
        },
        {
            "$set": {
                "is_active": False
            }
        },
    )