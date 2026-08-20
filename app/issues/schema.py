from datetime import datetime
from enum import Enum
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class IssueStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    CLOSED = "CLOSED"


class IssuePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueType(str, Enum):
    BUG = "BUG"
    FEATURE = "FEATURE"
    TASK = "TASK"
    IMPROVEMENT = "IMPROVEMENT"


class IssueCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Issue Title"
    )

    description: Optional[str] = Field(
        default=None,
        max_length=3000,
        description="Issue Description"
    )

    project_id: str = Field(
        ...,
        description="Project ID"
    )

    assignee_id: Optional[str] = Field(
        default=None,
        description="Assigned User ID"
    )

    priority: IssuePriority = Field(
        default=IssuePriority.MEDIUM,
        description="Issue Priority"
    )

    issue_type: IssueType = Field(
        default=IssueType.TASK,
        description="Issue Type"
    )

    due_date: Optional[datetime] = Field(
        default=None,
        description="Issue Due Date"
    )

    estimated_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=500,
        description="Estimated work hours"
    )

    labels: list[str] = Field(
        default_factory=list,
        description="Issue Labels"
    )


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        max_length=3000
    )

    status: Optional[IssueStatus] = None

    priority: Optional[IssuePriority] = None

    issue_type: Optional[IssueType] = None

    assignee_id: Optional[str] = None

    due_date: Optional[datetime] = None

    estimated_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=500
    )

    labels: Optional[list[str]] = None


class IssueResponse(BaseModel):
    id: str

    issue_key: str

    issue_no: int

    title: str

    description: Optional[str]

    project_id: str

    reporter_id: str

    assignee_id: Optional[str]

    status: IssueStatus

    priority: IssuePriority

    issue_type: IssueType

    due_date: Optional[datetime]

    estimated_hours: Optional[int]

    labels: list[str]

    resolved_at: Optional[datetime]

    created_at: datetime

    updated_at: datetime


class PaginatedIssueResponse(BaseModel):
    data: list[IssueResponse]
    page: int
    limit: int
    total_records: int
    total_pages: int


class IssueStatusUpdate(BaseModel):
    status: IssueStatus


class IssueAssigneeUpdate(BaseModel):
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None