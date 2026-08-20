from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

class RoleCreate(BaseModel):
    """
    Schema for creating a role.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    permissions: list[str] = Field(
        default_factory=list,
        description="List of Permission IDs"
    )

class RoleUpdate(BaseModel):

    description: Optional[str] = None

    permissions: Optional[list[str]] = None

class RoleResponse(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )

    id: str

    name: str

    description: Optional[str]

    permissions: list[str]

    created_at: datetime

    updated_at: datetime