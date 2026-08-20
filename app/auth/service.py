from fastapi import HTTPException

from app.auth.schema import LoginRequest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password
)
from app.auth.repository import (
    create_refresh_session,
    get_active_refresh_session,
    get_user_by_email,
    get_user_by_id,
    get_role_by_id,
    revoke_refresh_session,
    revoke_all_refresh_sessions,

)

def login_user(
    login_request: LoginRequest
) -> dict:

    email = str(login_request.email).lower()

    user = get_user_by_email(email)

    if (
        not user or
        not verify_password(
            login_request.password,
            user["password"]
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=403,
            detail="User is inactive"
        )

    user_id = str(user["_id"])

    access_token = create_access_token(
        user_id
    )

    refresh_token, token_id = (
        create_refresh_token(user_id)
    )

    create_refresh_session(
        user["_id"],
        token_id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }


def refresh_access_token(
    refresh_token: str
) -> dict:

    payload = decode_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")
    token_id = payload.get("jti")
    if not user_id or not token_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )
    session = get_active_refresh_session(
        user_id,
        token_id
    )

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid or revoked"
        )

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=403,
            detail="User is inactive"
        )

    revoke_refresh_session(
        session["_id"]
    )

    access_token = create_access_token(
        user_id
    )

    new_refresh_token, new_token_id = (
        create_refresh_token(user_id)
    )

    create_refresh_session(
        user["_id"],
        new_token_id
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer"
    }

def logout_user(
    refresh_token: str
) -> dict:

    payload = decode_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    token_id = payload.get("jti")
    user_id = payload.get("sub")

    if not user_id or not token_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    session = get_active_refresh_session(
        user_id,
        token_id
    )

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Already logged out"
        )

    revoke_refresh_session(
        session["_id"]
    )

    return {
        "message": "Successfully logged out."
    }

def logout_all_devices(user_id: str) -> dict:
    revoke_all_refresh_sessions(user_id)
    return {
        "message": "Logged out from all devices."
    }