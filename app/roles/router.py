from fastapi import APIRouter, Depends
from app.roles.schema import RoleCreate,RoleResponse
from app.roles.service import create_role,get_all_roles
from app.auth.permissions import require_permission

router=APIRouter()

@router.post('/create',response_model=RoleResponse,status_code=201)
def create_new_role(
    role:RoleCreate,
    current_user=Depends(require_permission("role:create"))
):
    return create_role(role)

@router.get('/get-all-roles',response_model=list[RoleResponse],status_code=200)
def fetch_all_roles(
    current_user=Depends(require_permission("role:view"))
):
    return get_all_roles()