from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.activity.repository import (
    get_activities,
    get_activity_by_id,
    log_activity,
)
# pyrefly: ignore [missing-import]
from bson import ObjectId
from app.database.mongodb import db
from app.activity.schema import (
    ActivityAction,
    ActivityEvent,
    ActivityResponse,
    EntityType,
)


def map_activity(activity: dict) -> ActivityResponse:
    """
    Convert MongoDB document to ActivityResponse.
    """

    return ActivityResponse(
        _id=str(activity["_id"]),
        entity_type=activity["entity_type"],
        entity_id=str(activity["entity_id"]),
        action=activity["action"],
        performed_by=str(activity["performed_by"]),
        project_id=(
            str(activity["project_id"])
            if activity.get("project_id")
            else None
        ),
        description=activity["description"],
        changes=activity.get("changes"),
        snapshot=activity.get("snapshot"),
        created_at=activity["created_at"],
    )


def create_activity_log(event: ActivityEvent) -> ActivityResponse:
    """
    Create a new activity log.
    """

    description = (
        f"{event.actor_name} "
        f"{event.action.value} "
        f"{event.entity_type.value} "
        f"{event.entity_name}"
    )

    activity_data = {
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "action": event.action,
        "performed_by": event.performed_by,
        "project_id": event.project_id,
        "description": description,
        "changes": event.changes,
        "snapshot": event.snapshot,
        "created_at": datetime.now(timezone.utc),
    }

    activity = log_activity(activity_data)

    return map_activity(activity)


def get_activity_by_id_service(activity_id: str) -> ActivityResponse:
    """
    Fetch activity by id.
    """

    activity = get_activity_by_id(activity_id)

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    return map_activity(activity)


def get_activities_service(
    page: int = 1,
    limit: int = 10,
    filters: dict | None = None,
):
    """
    Fetch paginated activities.
    """

    data = get_activities(page, limit, filters)

    data["activities"] = [
        map_activity(activity)
        for activity in data["activities"]
    ]

    return data
