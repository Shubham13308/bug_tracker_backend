from fastapi import APIRouter

from app.role_permissions.schema import (
    AssignPermissionsRequest,
    RolePermissionsDetailResponse,
)
from app.role_permissions.service import (
    assign_permissions_to_role,
    get_permissions_of_role,
)

router = APIRouter()


@router.post("/{role_id}/permissions", status_code=200)
@router.put("/{role_id}/permissions", status_code=200)
def assign_permissions(
    role_id: str,
    request: AssignPermissionsRequest,
):
    return assign_permissions_to_role(role_id, request)


@router.get("/{role_id}/permissions", response_model=RolePermissionsDetailResponse, status_code=200)
def get_role_permissions_endpoint(
    role_id: str,
):
    return get_permissions_of_role(role_id)
