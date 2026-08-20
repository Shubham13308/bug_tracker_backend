from datetime import datetime
from enum import Enum
from typing import Any, Optional

# pyrefly: ignore [missing-import]
from bson import ObjectId
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    PROJECT = "project"
    ISSUE = "issue"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    COMMENT = "comment"
    ATTACHMENT = "attachment"


class ActivityAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ARCHIVED = "archived"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    ATTACHMENT_UPLOADED = "attachment_uploaded"
    ATTACHMENT_DELETED = "attachment_deleted"


class ActivityEvent(BaseModel):
    entity_type: EntityType
    entity_id: str
    action: ActivityAction
    performed_by: str
    actor_name: str
    entity_name: str
    project_id: str | None = None
    changes: dict | None = None
    snapshot: dict | None = None


class ActivityResponse(BaseModel):
    id: str = Field(alias="_id")

    entity_type: EntityType
    entity_id: str

    action: ActivityAction

    performed_by: str

    project_id: Optional[str] = None

    description: str

    changes: Optional[dict[str, Any]] = None
    snapshot: Optional[dict[str, Any]] = None

    created_at: datetime

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )
