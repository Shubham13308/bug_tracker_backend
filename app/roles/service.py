from datetime import datetime, timezone
from fastapi import HTTPException, status
# pyrefly: ignore [missing-import]
from bson import ObjectId

from app.database.mongodb import db
from app.roles.schema import RoleCreate, RoleResponse
from app.roles.repository import get_role_by_id, create_role_in_db, get_all_roles_from_db

role_collection = db['roles']

def create_role(role: RoleCreate) -> RoleResponse:
    name = str(role.name).strip().lower()
    existing_role = role_collection.find_one({"name": name})
    if existing_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")

    permission_ids = []
    for permission_id in role.permissions:
        try:
            obj_id = ObjectId(permission_id)
            permission_ids.append(obj_id)
        except Exception:
            permission_ids.append(permission_id)

    role_data = role.model_dump()
    role_data['name'] = name
    role_data['permissions'] = permission_ids
    
    now = datetime.now(timezone.utc)
    role_data['created_at'] = now
    role_data['updated_at'] = now
    
    created_role = create_role_in_db(role_data)
    
    return RoleResponse(
        id=str(created_role["_id"]),
        name=created_role["name"],
        description=created_role.get("description"),
        permissions=[str(pid) for pid in created_role.get("permissions", [])],
        created_at=created_role["created_at"],
        updated_at=created_role["updated_at"]
    )

def get_all_roles():
    try:
        roles = get_all_roles_from_db()
        role_list = []
        for r in roles:
            role_list.append(RoleResponse(
                id=str(r["_id"]),
                name=r["name"],
                description=r.get("description"),
                permissions=[str(pid) for pid in r.get("permissions", [])],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        return role_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))