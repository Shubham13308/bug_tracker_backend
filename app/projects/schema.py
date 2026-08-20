from datetime import datetime
from enum import Enum
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class AssignTeamLeadRequest(BaseModel):
    project_id: str
    emp_id: str


class EmployeeAvailableResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    

class ProjectCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Project Name"
    )

    key: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Unique Project Key (e.g. BUG, CRM)"
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Project Description"
    )

    start_date: Optional[datetime] = Field(
        default=None,
        description="Project Start Date"
    )

    end_date: Optional[datetime] = Field(
        default=None,
        description="Project End Date"
    )

    color: str = Field(
        default="#2563EB",
        description="Project Theme Color"
    )

    icon: str = Field(
        default="Folder",
        description="Project Icon"
    )

    team_size: Optional[int] = Field(
        default=1,
        ge=1,
        description="Project Team Size"
    )


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    status: Optional[ProjectStatus] = None

    start_date: Optional[datetime] = None

    end_date: Optional[datetime] = None

    color: Optional[str] = None

    icon: Optional[str] = None

    members: Optional[list[str]] = None

    team_size: Optional[int] = Field(
        default=None,
        ge=1
    )


class ProjectResponse(BaseModel):
    id: str

    name: str

    key: str

    description: Optional[str]

    status: ProjectStatus

    start_date: Optional[datetime]

    end_date: Optional[datetime]

    color: str

    icon: str

    owner_id: str

    team_lead_id: Optional[str] = None

    team_lead_name: Optional[str] = None

    members: list[str] = Field(default_factory=list)


    team_size: int = 1

    is_archived: bool

    created_at: datetime

    updated_at: datetime


class PaginatedProjectResponse(BaseModel):
    data: list[ProjectResponse]
    employees: list[EmployeeAvailableResponse] = Field(default_factory=list)
    page: int
    limit: int
    total_records: int
    total_pages: int