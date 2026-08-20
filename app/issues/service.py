from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from bson import ObjectId
from fastapi import HTTPException, status

from app.projects.repository import get_project_by_id
from app.auth.repository import get_user_by_id

from app.issues.repository import (
    create_issue,
    get_last_issue,
    get_issues_paginated,
    count_issues,
    get_issue_by_id,
    update_issue
)

from app.issues.schema import (
    IssueCreate,
    IssueResponse,
    IssueStatus,
    IssuePriority,
    IssueType,
    PaginatedIssueResponse,
    IssueUpdate
)
from app.activity.service import create_activity_log
from app.activity.schema import ActivityAction, EntityType, ActivityEvent
from app.activity.utils import get_changed_fields, get_actor_name
from app.websocket.manager import manager


async def create_new_issue(
    issue: IssueCreate,
    current_user: dict,
) -> IssueResponse:
    """
    Create a new issue.
    """

    # -------------------------------
    # Validate Project
    # -------------------------------
    project = get_project_by_id(issue.project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # -------------------------------
    # Validate Assignee
    # -------------------------------
    assignee = None

    if issue.assignee_id:

        assignee = get_user_by_id(issue.assignee_id)

        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found."
            )

    # -------------------------------
    # Generate Issue Number
    # -------------------------------
    last_issue = get_last_issue(issue.project_id)

    if last_issue:
        issue_no = last_issue["issue_no"] + 1
    else:
        issue_no = 1

    issue_key = f"{project['key']}-{issue_no}"

    now = datetime.now(timezone.utc)

    issue_data = issue.model_dump()

    issue_data.update(
        {
            "project_id": ObjectId(issue.project_id),

            "reporter_id": ObjectId(current_user["_id"]),

            "assignee_id": (
                ObjectId(issue.assignee_id)
                if issue.assignee_id
                else None
            ),

            "issue_no": issue_no,

            "issue_key": issue_key,

            "status": IssueStatus.OPEN,

            "resolved_at": None,

            "created_at": now,

            "updated_at": now,
        }
    )

    result = create_issue(issue_data)

    event = ActivityEvent(
        entity_type=EntityType.ISSUE,
        entity_id=str(result.inserted_id),
        action=ActivityAction.CREATED,
        performed_by=str(current_user["_id"]),
        actor_name=get_actor_name(current_user),
        entity_name=issue_key,
        project_id=issue.project_id,
        snapshot={
            "title": issue_data["title"],
            "status": issue_data["status"],
            "priority": issue_data["priority"],
            "assignee_id": (
                str(issue_data["assignee_id"])
                if issue_data["assignee_id"]
                else None
            ),
        },
    )
    create_activity_log(event)

    if issue.assignee_id:
        try:
            assigned_by_id = str(current_user["_id"])
            assigned_by_name = get_actor_name(current_user)
            assigned_to_name = (
                f"{assignee.get('first_name', '')} {assignee.get('last_name', '')}".strip()
                or assignee.get("username", "Employee")
                if assignee else "Employee"
            )
            await manager.send_to_user(
                str(issue.assignee_id),
                {
                    "type": "PROJECT_ASSIGNED",
                    "issue_id": str(result.inserted_id),
                    "issue_key": issue_key,
                    "project_id": issue.project_id,
                    "project_name": project.get("name"),
                    "assigned_by": assigned_by_id,
                    "assigned_by_name": assigned_by_name,
                    "assigned_to_name": assigned_to_name,
                    "message": f"This project is assigned to you by your Team Lead ({assigned_by_name})"
                }
            )
        except Exception as ws_err:
            print("Notice: Error sending WebSocket notification on issue create:", ws_err)

    return IssueResponse(
        id=str(result.inserted_id),

        issue_key=issue_key,

        issue_no=issue_no,

        title=issue_data["title"],

        description=issue_data["description"],

        project_id=str(issue_data["project_id"]),

        reporter_id=str(issue_data["reporter_id"]),

        assignee_id=(
            str(issue_data["assignee_id"])
            if issue_data["assignee_id"]
            else None
        ),

        status=issue_data["status"],

        priority=issue_data["priority"],

        issue_type=issue_data["issue_type"],

        due_date=issue_data["due_date"],

        estimated_hours=issue_data["estimated_hours"],

        labels=issue_data["labels"],

        resolved_at=None,

        created_at=issue_data["created_at"],

        updated_at=issue_data["updated_at"],
    )


def _build_issue_response(issue_data: dict) -> IssueResponse:
    return IssueResponse(
        id=str(issue_data["_id"]),
        issue_key=issue_data["issue_key"],
        issue_no=issue_data["issue_no"],
        title=issue_data["title"],
        description=issue_data.get("description"),
        project_id=str(issue_data["project_id"]),
        reporter_id=str(issue_data["reporter_id"]),
        assignee_id=str(issue_data["assignee_id"]) if issue_data.get("assignee_id") else None,
        status=issue_data["status"],
        priority=issue_data["priority"],
        issue_type=issue_data["issue_type"],
        due_date=issue_data.get("due_date"),
        estimated_hours=issue_data.get("estimated_hours"),
        labels=issue_data.get("labels", []),
        resolved_at=issue_data.get("resolved_at"),
        created_at=issue_data["created_at"],
        updated_at=issue_data["updated_at"],
    )


def get_paginated_issues(
    page: int,
    limit: int,
    search_title: str | None,
    project_id: str | None,
    status: IssueStatus | None,
    priority: IssuePriority | None,
    assignee_id: str | None,
    reporter_id: str | None,
    issue_type: IssueType | None
) -> PaginatedIssueResponse:
    query = {}

    if search_title:
        query["title"] = {"$regex": search_title, "$options": "i"}
    if project_id and ObjectId.is_valid(project_id):
        query["project_id"] = ObjectId(project_id)
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if assignee_id and ObjectId.is_valid(assignee_id):
        query["assignee_id"] = ObjectId(assignee_id)
    if reporter_id and ObjectId.is_valid(reporter_id):
        query["reporter_id"] = ObjectId(reporter_id)
    if issue_type:
        query["issue_type"] = issue_type

    skip = (page - 1) * limit
    issues_data = get_issues_paginated(query, skip, limit)
    total_records = count_issues(query)
    total_pages = (total_records + limit - 1) // limit

    return PaginatedIssueResponse(
        data=[_build_issue_response(i) for i in issues_data],
        page=page,
        limit=limit,
        total_records=total_records,
        total_pages=total_pages
    )


def get_issue(issue_id: str) -> IssueResponse:
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")

    issue = get_issue_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    return _build_issue_response(issue)


def update_existing_issue(issue_id: str, issue_update: IssueUpdate, current_user: dict) -> IssueResponse:
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")

    existing = get_issue_by_id(issue_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    update_data = issue_update.model_dump(exclude_unset=True)

    if not update_data:
        return _build_issue_response(existing)

    if "assignee_id" in update_data and update_data["assignee_id"]:
        assignee = get_user_by_id(update_data["assignee_id"])
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found.")
        update_data["assignee_id"] = ObjectId(update_data["assignee_id"])

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == IssueStatus.DONE and existing["status"] != IssueStatus.DONE:
            update_data["resolved_at"] = datetime.now(timezone.utc)
        elif new_status != IssueStatus.DONE and existing["status"] == IssueStatus.DONE:
            update_data["resolved_at"] = None

    update_data["updated_at"] = datetime.now(timezone.utc)
    update_issue(issue_id, update_data)

    updated_issue = get_issue_by_id(issue_id)
    
    changes = get_changed_fields(
        existing,
        updated_issue,
        exclude_fields=[
            "_id",
            "created_at",
            "updated_at",
            "resolved_at",
        ],
    )
    
    if changes:
        event = ActivityEvent(
            entity_type=EntityType.ISSUE,
            entity_id=issue_id,
            action=ActivityAction.UPDATED,
            performed_by=str(current_user["_id"]),
            actor_name=get_actor_name(current_user),
            entity_name=updated_issue["issue_key"],
            project_id=str(updated_issue["project_id"]),
            changes=changes,
        )
        create_activity_log(event)

    return _build_issue_response(updated_issue)


def update_issue_status(issue_id: str, new_status: IssueStatus, current_user: dict) -> IssueResponse:
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")

    existing = get_issue_by_id(issue_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    update_data = {"status": new_status, "updated_at": datetime.now(timezone.utc)}

    if new_status == IssueStatus.DONE and existing["status"] != IssueStatus.DONE:
        update_data["resolved_at"] = datetime.now(timezone.utc)
    elif new_status != IssueStatus.DONE and existing["status"] == IssueStatus.DONE:
        update_data["resolved_at"] = None

    update_issue(issue_id, update_data)

    updated_issue = get_issue_by_id(issue_id)
    
    event = ActivityEvent(
        entity_type=EntityType.ISSUE,
        entity_id=issue_id,
        action=ActivityAction.STATUS_CHANGED,
        performed_by=str(current_user["_id"]),
        actor_name=get_actor_name(current_user),
        entity_name=updated_issue["issue_key"],
        project_id=str(updated_issue["project_id"]),
        changes={
            "status": {
                "old": existing["status"],
                "new": updated_issue["status"],
            }
        },
    )
    create_activity_log(event)

    return _build_issue_response(updated_issue)


async def update_issue_assignee(issue_id: str, assignee_id: str | None, current_user: dict, project_id: str | None = None) -> IssueResponse:
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")

    existing = get_issue_by_id(issue_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    update_data = {"updated_at": datetime.now(timezone.utc)}

    if project_id and ObjectId.is_valid(project_id):
        update_data["project_id"] = ObjectId(project_id)

    if assignee_id:
        assignee = get_user_by_id(assignee_id)
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found.")
        update_data["assignee_id"] = ObjectId(assignee_id)
    else:
        update_data["assignee_id"] = None


    update_issue(issue_id, update_data)

    # Save to 'assign' collection (assign cluster)
    if assignee_id:
        try:
            from app.database.mongodb import assign_collection, projects_collection

            pid_str = project_id or str(existing.get("project_id"))
            proj_doc = projects_collection.find_one({"_id": ObjectId(pid_str)}) if ObjectId.is_valid(pid_str) else None
            proj_name = proj_doc.get("name") if proj_doc else None

            assigned_by_id = (
                str(current_user["_id"])
                if isinstance(current_user, dict) and "_id" in current_user
                else str(current_user.get("id"))
            )
            assigned_by_name = get_actor_name(current_user) if isinstance(current_user, dict) else "Unknown"
            assigned_by_email = current_user.get("email") if isinstance(current_user, dict) else None

            assigned_to_user = get_user_by_id(assignee_id)
            assigned_to_name = (
                f"{assigned_to_user.get('first_name', '')} {assigned_to_user.get('last_name', '')}".strip()
                or assigned_to_user.get("username")
                if assigned_to_user else str(assignee_id)
            )
            assigned_to_email = assigned_to_user.get("email") if assigned_to_user else None

            assignment_doc = {
                "project_id": pid_str,
                "project_name": proj_name,
                "issue_id": issue_id,
                "issue_key": existing.get("issue_key"),
                "assignee_id": assignee_id,
                "assigned_to": {
                    "id": assignee_id,
                    "name": assigned_to_name,
                    "email": assigned_to_email
                },
                "assigned_by": {
                    "id": assigned_by_id,
                    "name": assigned_by_name,
                    "email": assigned_by_email
                },
                "role": "Issue Fixer",
                "assigned_at": datetime.now(timezone.utc)
            }

            assign_collection.insert_one(assignment_doc)

            # Send WebSocket notification to the assigned employee (assignee_id)
            await manager.send_to_user(
                str(assignee_id),
                {
                    "type": "PROJECT_ASSIGNED",
                    "issue_id": issue_id,
                    "issue_key": existing.get("issue_key"),
                    "project_id": pid_str,
                    "project_name": proj_name,
                    "assigned_by": assigned_by_id,
                    "assigned_by_name": assigned_by_name,
                    "assigned_to_name": assigned_to_name,
                    "message": f"This project is assigned to you by your Team Lead ({assigned_by_name})"
                }
            )
        except Exception as e:
            print("Notice: Error logging assignment record or sending websocket:", e)

    updated_issue = get_issue_by_id(issue_id)

    
    old_assignee = (
        str(existing["assignee_id"])
        if existing.get("assignee_id")
        else None
    )

    new_assignee = (
        str(updated_issue["assignee_id"])
        if updated_issue.get("assignee_id")
        else None
    )

    event = ActivityEvent(
        entity_type=EntityType.ISSUE,
        entity_id=issue_id,
        action=ActivityAction.ASSIGNED,
        performed_by=str(current_user["_id"]),
        actor_name=get_actor_name(current_user),
        entity_name=updated_issue["issue_key"],
        project_id=str(updated_issue["project_id"]),
        changes={
            "assignee": {
                "old": old_assignee,
                "new": new_assignee,
            }
        },
    )
    create_activity_log(event)

    return _build_issue_response(updated_issue)