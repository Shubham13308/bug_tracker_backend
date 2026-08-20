from datetime import datetime, timezone
import re
from fastapi import HTTPException, status

from app.permissions.repository import (
    create_permission,
    get_permission_by_id,
    get_permission_by_name,
    get_permission_by_permission,
    get_permissions,
    update_permission,
    soft_delete_permission,
)

from app.permissions.schema import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
)


def validate_permission(perm: str):
    """Validate permission format e.g. 'module:action' or '*'."""
    if perm == "*":
        return True
    pattern = r"^[a-z0-9_-]+:[a-z0-9_*:-]+$"
    if not re.match(pattern, perm):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission string format. Example format: 'module:action' (e.g. 'project:view')",
        )
    return True


def format_permission_response(permission: dict) -> PermissionResponse:
    """Format MongoDB permission document into PermissionResponse."""
    return PermissionResponse(
        id=str(permission["_id"]),
        name=permission["name"],
        permission=permission["permission"],
        module=permission["module"],
        description=permission.get("description"),
        navigation=permission.get("navigation"),
        is_active=permission.get("is_active", True),
        created_at=permission["created_at"],
        updated_at=permission["updated_at"],
    )


def create_new_permission(permission: PermissionCreate) -> PermissionResponse:
    permission.permission = permission.permission.lower().strip()
    permission.module = permission.module.lower().strip()
    permission.name = permission.name.strip()

    validate_permission(permission.permission)

    existing_name = get_permission_by_name(permission.name)
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission name already exists",
        )

    existing_permission = get_permission_by_permission(permission.permission)
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission string already exists",
        )

    permission_data = permission.model_dump()
    permission_data["permission"] = permission.permission
    permission_data["module"] = permission.module
    permission_data["name"] = permission.name
    permission_data["is_active"] = True
    now = datetime.now(timezone.utc)
    permission_data["created_at"] = now
    permission_data["updated_at"] = now

    result = create_permission(permission_data)
    created_permission = get_permission_by_id(str(result.inserted_id))

    return format_permission_response(created_permission)


def get_all_permissions() -> list[PermissionResponse]:
    permissions = get_permissions()
    return [format_permission_response(p) for p in permissions]


def get_permission(permission_id: str) -> PermissionResponse:
    permission = get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return format_permission_response(permission)


def update_existing_permission(
    permission_id: str,
    permission_update: PermissionUpdate,
) -> PermissionResponse:
    existing_permission = get_permission_by_id(permission_id)
    if not existing_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    update_data = permission_update.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"]:
        update_data["name"] = update_data["name"].strip()
        duplicate = get_permission_by_name(update_data["name"])
        if duplicate and str(duplicate["_id"]) != permission_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission name already exists",
            )

    if "permission" in update_data and update_data["permission"]:
        update_data["permission"] = update_data["permission"].lower().strip()
        validate_permission(update_data["permission"])
        duplicate_perm = get_permission_by_permission(update_data["permission"])
        if duplicate_perm and str(duplicate_perm["_id"]) != permission_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission string already exists",
            )

    if "module" in update_data and update_data["module"]:
        update_data["module"] = update_data["module"].lower().strip()

    update_data["updated_at"] = datetime.now(timezone.utc)
    update_permission(permission_id, update_data)

    updated_permission = get_permission_by_id(permission_id)
    return format_permission_response(updated_permission)


def delete_permission(permission_id: str):
    permission = get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    soft_delete_permission(permission_id)
    return {"message": "Permission deleted successfully"}