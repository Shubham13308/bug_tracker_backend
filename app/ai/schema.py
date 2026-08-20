from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class AISearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Natural language search query",
    )


class AISearchIntent(BaseModel):
    entity: str = Field(
        description="project, issue, employee, or assignment"
    )

    search_text: Optional[str] = None
    project_key: Optional[str] = None
    project_name: Optional[str] = None
    person_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    reporter_name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    issue_type: Optional[str] = None
    role: Optional[str] = None
    show_details:bool=False


class AISearchResponse(BaseModel):
    message: str
    results: list[dict] = Field(
        default_factory=list
    )