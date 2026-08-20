# pyrefly: ignore [missing-import]
from bson import ObjectId
from fastapi import Depends, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from app.core.security import decode_token
from app.database.mongodb import db
from app.roles.repository import get_role_by_id

user_collection = db["users"]

bearer_scheme = HTTPBearer()


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
) -> str:
    return credentials.credentials

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
) -> dict:

    token = credentials.credentials

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token"
        )

    # Make sure a refresh token cannot access protected APIs
    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )

    # Check before converting the string to ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID"
        )

    user = user_collection.find_one(
        {
            "_id": ObjectId(user_id)
        }
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    role_id = user.get("role_id")
    if role_id:
        role = get_role_by_id(str(role_id))
        user["role"] = role.get("name") if role else None
    else:
        user["role"] = None
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    return user