
from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Username")
    first_name: str = Field(..., min_length=3, max_length=50, description="First Name")
    last_name: str = Field(..., min_length=3, max_length=50, description="Last Name")
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    role_id: Optional[str] = Field(default=None, description="Role ID")
    designation: Optional[str] = Field(default=None, description="Designation")


class UserResponse(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    role_id: str
    role: Optional[str] = None
    email: EmailStr
    is_active: bool
    designation: Optional[str] = None
    reporting_manager_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RoleDropdownResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class UserListResponse(BaseModel):
    data: list[UserResponse]
    roles: list[RoleDropdownResponse]