from fastapi import APIRouter, Depends, status

from app.auth.permissions import require_permission
from app.issues.schema import (
    IssueCreate,
    IssueResponse,
    IssueUpdate,
    PaginatedIssueResponse,
    IssueStatus,
    IssuePriority,
    IssueType,
    IssueStatusUpdate,
    IssueAssigneeUpdate
)
from app.issues.service import (
    create_new_issue,
    get_paginated_issues,
    get_issue,
    update_existing_issue,
    update_issue_status,
    update_issue_assignee
)

router = APIRouter()


@router.post(
    "/",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(
    issue: IssueCreate,
    current_user=Depends(require_permission("issue:create")),
):
    """
    Create a new issue.
    """
    return await create_new_issue(
        issue=issue,
        current_user=current_user,
    )

@router.get(
    "/",
    response_model=PaginatedIssueResponse,
    status_code=status.HTTP_200_OK,
)
def get_issues(
    page: int = 1,
    limit: int = 10,
    search_title: str | None = None,
    project_id: str | None = None,
    status_filter: IssueStatus | None = None,
    priority: IssuePriority | None = None,
    assignee_id: str | None = None,
    reporter_id: str | None = None,
    issue_type: IssueType | None = None,
    current_user=Depends(require_permission("issue:view"))
):
    """
    Get paginated issues.
    """
    return get_paginated_issues(
        page, limit, search_title, project_id, status_filter, priority, assignee_id, reporter_id, issue_type
    )


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    status_code=status.HTTP_200_OK,
)
def get_issue_by_id(
    issue_id: str,
    current_user=Depends(require_permission("issue:view"))
):
    """
    Get issue by ID.
    """
    return get_issue(issue_id)


@router.patch(
    "/{issue_id}",
    response_model=IssueResponse,
    status_code=status.HTTP_200_OK,
)
def update_issue(
    issue_id: str,
    issue_update: IssueUpdate,
    current_user=Depends(require_permission("issue:update"))
):
    """
    Update issue details.
    """
    return update_existing_issue(issue_id, issue_update, current_user)


@router.patch(
    "/{issue_id}/status",
    response_model=IssueResponse,
    status_code=status.HTTP_200_OK,
)
def update_status(
    issue_id: str,
    status_update: IssueStatusUpdate,
    current_user=Depends(require_permission("issue:change_status"))
):
    """
    Update only issue status.
    """
    return update_issue_status(issue_id, status_update.status, current_user)


@router.patch(
    "/{issue_id}/assign",
    response_model=IssueResponse,
    status_code=status.HTTP_200_OK,
)
async def update_assignee(
    issue_id: str,
    assign_update: IssueAssigneeUpdate,
    current_user=Depends(require_permission("issue:assign"))
):
    """
    Update issue assignee and optionally project_id.
    """
    return await update_issue_assignee(
        issue_id=issue_id,
        assignee_id=assign_update.assignee_id,
        current_user=current_user,
        project_id=assign_update.project_id
    )