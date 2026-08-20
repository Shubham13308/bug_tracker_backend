from fastapi import Depends, HTTPException, status
from app.auth.dependencies import get_current_user

DEMO_ROLE_ID = "6a55fd6054a2a5ca60cf3054"

def require_permission(permission_name: str):
    """
    Permission dependency.
    Enforces read-only access for Demo Mode users while allowing view access across all modules.
    """
    def permission_checker(current_user: dict = Depends(get_current_user)):
        username = str(current_user.get("username", "")).lower()
        designation = str(current_user.get("designation", "")).lower()
        role_id = str(current_user.get("role_id", ""))

        is_demo = (
            username == "demomode" or
            designation == "demomode" or
            role_id == DEMO_ROLE_ID
        )

        if is_demo:
            # Allow view actions, restrict mutation actions
            is_read_action = permission_name.endswith(":view") or permission_name in [
                "view", "issue:view", "project:view", "user:view", "role:view", "activity:view", "permission:view"
            ]

            if not is_read_action:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Demo Mode: You are signed in Demo Mode (Read Only). Adding users, creating projects, assigning, or modifying data is disabled."
                )

        return current_user

    return permission_checker

