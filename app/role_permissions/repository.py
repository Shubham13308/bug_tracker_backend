from typing import Any, List
# pyrefly: ignore [missing-import]
from bson import ObjectId
# pyrefly: ignore [missing-import]
from pymongo.results import DeleteResult, InsertManyResult
from app.database.mongodb import db

role_permission_collection = db["role_permissions"]


def delete_role_permissions(role_id: str) -> DeleteResult:
    """Delete all permission mappings for a given role ID."""
    role_target = ObjectId(role_id) if isinstance(role_id, str) and ObjectId.is_valid(role_id) else role_id
    return role_permission_collection.delete_many(
        {
            "$or": [
                {"role_id": role_target},
                {"role_id": str(role_id)},
            ]
        }
    )


def create_role_permissions(role_permissions: list) -> InsertManyResult:
    """Insert multiple role-permission mapping records."""
    return role_permission_collection.insert_many(
        role_permissions
    )


def get_role_permissions(role_id: str) -> List[dict[str, Any]]:
    """Retrieve all permission mappings for a given role ID."""
    role_target = ObjectId(role_id) if isinstance(role_id, str) and ObjectId.is_valid(role_id) else role_id
    return list(
        role_permission_collection.find(
            {
                "$or": [
                    {"role_id": role_target},
                    {"role_id": str(role_id)},
                ]
            }
        )
    )