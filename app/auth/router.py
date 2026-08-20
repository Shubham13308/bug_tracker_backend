from fastapi import APIRouter, Depends
from app.auth.schema import (LoginRequest,LoginResponse,RefreshTokenResponse,UserResponse)
from app.auth.service import login_user, refresh_access_token, logout_user, logout_all_devices
from app.auth.dependencies import get_bearer_token, get_current_user

router=APIRouter()

@router.post('/login',response_model=LoginResponse,status_code=200)
def login(login_data:LoginRequest):
    return login_user(login_data)

@router.post('/refresh',response_model=RefreshTokenResponse,status_code=200)
def refresh(refresh_token: str = Depends(get_bearer_token)):
    return refresh_access_token(refresh_token)

@router.post('/logout', status_code=200)
def logout(refresh_token: str = Depends(get_bearer_token)):
    return logout_user(refresh_token)

@router.post('/logout-all', status_code=200)
def logout_all(current_user: dict = Depends(get_current_user)):
    return logout_all_devices(str(current_user["_id"]))

@router.get('/me', response_model=UserResponse, status_code=200)
def get_me(current_user: dict = Depends(get_current_user)):
    user_name = current_user.get("name")
    if not user_name:
        user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or current_user.get("username", "")

    return UserResponse(
        id=str(current_user["_id"]),
        name=user_name,
        email=current_user["email"],
        role=current_user.get("role", "employee"),
        created_at=current_user.get("created_at", "").isoformat() if hasattr(current_user.get("created_at"), "isoformat") else str(current_user.get("created_at"))
    )
