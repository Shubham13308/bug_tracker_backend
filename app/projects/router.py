from fastapi import APIRouter, Depends, status

from app.auth.permissions import require_permission
from app.projects.schema import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    PaginatedProjectResponse,
    ProjectStatus,
    EmployeeAvailableResponse,
    AssignTeamLeadRequest
)
from app.projects.service import (
    create_new_project,
    get_paginated_projects,
    get_project,
    update_existing_project,
    soft_delete_project,
    get_all_employee_dropdown,
    assign_tl_to_project,
    get_project_assignments
)


router = APIRouter()


@router.get(
    "/employees",
    response_model=list[EmployeeAvailableResponse],
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/employees/dropdown",
    response_model=list[EmployeeAvailableResponse],
    status_code=status.HTTP_200_OK,
)
def get_employee_dropdown_list(
    role_id: str | None = None,
    current_user=Depends(require_permission("project:view"))
):
    """
    Get active employees for project employee assignment dropdown.
    """
    return get_all_employee_dropdown(role_id=role_id)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project: ProjectCreate,
    current_user=Depends(require_permission("project:create")),
):
    """
    Create a new project.
    """

    return create_new_project(
        project=project,
        current_user=current_user,
    )

@router.get(
    "/",
    response_model=PaginatedProjectResponse,
    status_code=status.HTTP_200_OK,
)
def get_projects(
    page: int = 1,
    limit: int = 10,
    search_name: str | None = None,
    search_key: str | None = None,
    status_filter: ProjectStatus | None = None,
    current_user=Depends(require_permission("project:view"))
):
    """
    Get paginated active projects.
    """
    return get_paginated_projects(page, limit, search_name, search_key, status_filter)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
)
def get_project_by_id(
    project_id: str,
    current_user=Depends(require_permission("project:view"))
):
    """
    Get project by ID.
    """
    return get_project(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
)
def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user=Depends(require_permission("project:update"))
):
    """
    Update project details.
    """
    return update_existing_project(project_id, project_update, current_user)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
)
def delete_project(
    project_id: str,
    current_user=Depends(require_permission("project:delete"))
):
    """
    Soft delete a project.
    """
    return soft_delete_project(project_id, current_user)


@router.post(
    "/assign-tl",
    status_code=status.HTTP_200_OK,
)
async def assign_team_lead(
    payload: AssignTeamLeadRequest,
    current_user=Depends(require_permission("project:update"))
):
    """
    Assign Team Lead (emp_id) to a project (project_id).
    """
    return await assign_tl_to_project(payload, current_user)


@router.get(
    "/assignments",
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/assign",
    status_code=status.HTTP_200_OK,
)
def list_assignments(
    current_user=Depends(require_permission("project:view"))
):
    """
    Get all assignment records (who assigned whom).
    """
    return get_project_assignments()