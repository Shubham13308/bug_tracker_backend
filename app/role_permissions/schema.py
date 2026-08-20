from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field
from app.permissions.schema import PermissionResponse


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of Permission IDs"
    )


class RolePermissionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    role_id: str
    permission_id: str
    created_at: datetime


class RolePermissionsDetailResponse(BaseModel):
    role_id: str
    role: str
    permissions: list[PermissionResponse]