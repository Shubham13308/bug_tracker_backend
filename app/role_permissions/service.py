from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from bson import ObjectId
from fastapi import HTTPException, status

from app.permissions.repository import get_permissions_by_ids
from app.permissions.service import format_permission_response
from app.role_permissions.repository import (
    create_role_permissions,
    delete_role_permissions,
    get_role_permissions,
)
from app.role_permissions.schema import (
    AssignPermissionsRequest,
    RolePermissionsDetailResponse,
)
from app.roles.repository import get_role_by_id


def assign_permissions_to_role(
    role_id: str,
    request: AssignPermissionsRequest,
) -> dict:
    """
    Assign permissions to a role.
    Existing permissions will be replaced.
    """
    # Validate role
    role = get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Validate permissions using single query
    permissions = get_permissions_by_ids(request.permission_ids)
    if len(permissions) != len(request.permission_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permission IDs are invalid.",
        )

    # Remove existing mappings
    delete_role_permissions(role_id)

    # Prepare new mappings with ObjectId for indexed performance and consistency
    now = datetime.now(timezone.utc)
    role_obj_id = ObjectId(role_id) if ObjectId.is_valid(role_id) else role_id

    role_permissions = [
        {
            "role_id": role_obj_id,
            "permission_id": ObjectId(pid) if ObjectId.is_valid(pid) else pid,
            "created_at": now,
        }
        for pid in request.permission_ids
    ]

    # Insert mappings
    if role_permissions:
        create_role_permissions(role_permissions)

    return {
        "message": "Permissions assigned successfully."
    }


def get_permissions_of_role(role_id: str) -> RolePermissionsDetailResponse:
    """
    Get all permissions and permission details assigned to a role.
    """
    role = get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    role_permissions = get_role_permissions(role_id)
    permission_ids = [str(rp["permission_id"]) for rp in role_permissions]

    # Efficiently fetch permission details using get_permissions_by_ids in a single query
    permission_docs = get_permissions_by_ids(permission_ids) if permission_ids else []

    formatted_permissions = [
        format_permission_response(permission)
        for permission in permission_docs
    ]

    return RolePermissionsDetailResponse(
        role_id=str(role["_id"]),
        role=role.get("name", ""),
        permissions=formatted_permissions,
    )