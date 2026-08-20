from fastapi import APIRouter

from app.permissions.schema import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
)
from app.permissions.service import (
    create_new_permission,
    get_all_permissions,
    get_permission,
    update_existing_permission,
    delete_permission,
)

router = APIRouter()


@router.post("", response_model=PermissionResponse, status_code=201)
def create_permission(
    permission: PermissionCreate,
):
    return create_new_permission(permission)


@router.get("", response_model=list[PermissionResponse], status_code=200)
def get_permissions():
    return get_all_permissions()


@router.get("/{permission_id}", response_model=PermissionResponse, status_code=200)
def get_permission_by_id_endpoint(permission_id: str):
    return get_permission(permission_id)


@router.patch("/{permission_id}", response_model=PermissionResponse, status_code=200)
def update_permission(
    permission_id: str,
    permission_update: PermissionUpdate,
):
    return update_existing_permission(
        permission_id,
        permission_update,
    )


@router.delete("/{permission_id}", status_code=200)
def delete_permission_endpoint(permission_id: str):
    return delete_permission(permission_id)