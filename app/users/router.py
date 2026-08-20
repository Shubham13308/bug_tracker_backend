from fastapi import APIRouter, Depends
from app.users.schema import UserCreate, UserResponse, UserListResponse, RoleDropdownResponse
from app.users.service import create_user, get_all_users, get_roles_dropdown_list
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get('/', response_model=UserListResponse)
def list_users(current_user: dict = Depends(get_current_user)):
    return get_all_users()


@router.get('/roles/dropdown', response_model=list[RoleDropdownResponse])
@router.get('/roles', response_model=list[RoleDropdownResponse])
def fetch_roles_dropdown(current_user: dict = Depends(get_current_user)):
    return get_roles_dropdown_list()


@router.post('/register',response_model=UserResponse,status_code=201)

def register_user(user:UserCreate):
    return create_user(user)
@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: dict = Depends(get_current_user)
):

    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
        "email": current_user["email"],
        "designation": current_user.get("designation"),
        "reporting_manager_id": current_user.get("reporting_manager_id"),
        "role_id": str(current_user.get("role_id")),
        "role": current_user.get("role"),
        "is_active": current_user["is_active"],
        "created_at": current_user.get("created_at"),
        "updated_at": current_user.get("updated_at")
    }