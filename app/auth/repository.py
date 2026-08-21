from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
from bson import ObjectId

from app.database.mongodb import db
from app.core.security import decode_token

refresh_tokens_collection = db["refresh_tokens"]
user_collection = db["users"]
role_collection = db["roles"]
def get_user_by_email(email:str):
    """Get user by email"""
    return user_collection.find_one({
        "email": email
    })
def get_role_by_id(role_id: str):
    obj_id = ObjectId(role_id) if isinstance(role_id, str) and ObjectId.is_valid(role_id) else role_id
    return role_collection.find_one({"_id": obj_id})
    
def get_user_by_id(user_id: str):
    """Get user by id"""
    obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    return user_collection.find_one({"_id": obj_id})

def create_refresh_session(user_id, token_id: str):
    """Create refresh token session"""
    obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    return refresh_tokens_collection.insert_one({
        "user_id": obj_id,
        "token_id": token_id,
        "is_revoked": False,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
    })

def get_active_refresh_session(user_id, token_id: str):
    obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    return refresh_tokens_collection.find_one({
        "user_id": obj_id,
        "token_id": token_id,
        "is_revoked": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })

def revoke_refresh_session(
    session_id
):

    refresh_tokens_collection.update_one(
        {
            "_id": session_id
        },
        {
            "$set": {
                "is_revoked": True,
                "revoked_at": datetime.now(
                    timezone.utc
                )
            }
        }
    )

def revoke_all_refresh_sessions(user_id: str):
    refresh_tokens_collection.update_many(
        {
            "user_id": ObjectId(user_id),
            "is_revoked": False
        },
        {
            "$set": {
                "is_revoked": True,
                "revoked_at": datetime.now(timezone.utc)
            }
        }
    )
