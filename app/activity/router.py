from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.activity.service import (
    get_activities_service,
    get_activity_by_id_service,
)
from app.auth.permissions import require_permission
from app.activity.schema import EntityType, ActivityAction

router = APIRouter()


@router.get("/")
def get_activities(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    entity_type: Optional[EntityType] = None,
    action: Optional[ActivityAction] = None,
    performed_by: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user=Depends(require_permission("activity:view")),
):
    """
    Get all activity logs with pagination and filters.
    """

    filters = {}

    if entity_type:
        filters["entity_type"] = entity_type

    if action:
        filters["action"] = action

    if performed_by:
        filters["performed_by"] = performed_by

    if project_id:
        filters["project_id"] = project_id

    return get_activities_service(
        page=page,
        limit=limit,
        filters=filters,
    )


@router.get("/{activity_id}")
def get_activity(activity_id: str,
                 current_user=Depends(require_permission("activity:view"))):
    """
    Get activity by ID.
    """

    return get_activity_by_id_service(activity_id)
