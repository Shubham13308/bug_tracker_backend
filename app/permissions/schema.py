from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, ConfigDict


class Navigation(BaseModel):
    enabled: bool = True
    route: Optional[str] = None
    menu_name: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    permission: str = Field(..., min_length=2, max_length=100)
    module: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    navigation: Optional[Navigation] = None


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    permission: Optional[str] = Field(None, min_length=2, max_length=100)
    module: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    navigation: Optional[Navigation] = None
    is_active: Optional[bool] = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )
    id: str
    name: str
    permission: str
    module: str
    description: Optional[str] = None
    navigation: Optional[Navigation] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
