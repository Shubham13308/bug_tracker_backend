from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from bson import ObjectId
from fastapi import HTTPException, status

from app.projects.repository import (
    create_project,
    get_project_by_key,
    get_project_by_id,
    get_all_projects,
    get_projects_paginated,
    count_projects,
    update_project,
    archive_project,
    get_all_employees,
    create_assignment_record,
    get_all_assignments
)
from app.database.mongodb import user_collection, assign_collection
from app.websocket.manager import manager


from app.projects.schema import (
    ProjectCreate,
    ProjectResponse,
    ProjectStatus,
    ProjectUpdate,
    PaginatedProjectResponse,
    EmployeeAvailableResponse,
    AssignTeamLeadRequest
)
from app.activity.service import create_activity_log
from app.activity.schema import ActivityAction, ActivityEvent, EntityType
from app.activity.utils import get_changed_fields, get_actor_name


def create_new_project(
    project: ProjectCreate,
    current_user: dict,
) -> ProjectResponse:
    """
    Create a new project.

    Business Rules:
    - Project key must be unique.
    - Project key is stored in uppercase.
    - End date cannot be before start date.
    - Every new project starts as ACTIVE.
    - Creator becomes project owner.
    - Creator is automatically added as a member.
    """

    # Normalize input
    project_key = project.key.strip().upper()
    project_name = project.name.strip()

    # Check duplicate project key
    existing_project = get_project_by_key(project_key)

    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project key already exists.",
        )

    # Validate dates
    if (
        project.start_date
        and project.end_date
        and project.end_date < project.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be earlier than start date.",
        )

    now = datetime.now(timezone.utc)

    project_data = project.model_dump()

    project_data.update(
        {
            "name": project_name,
            "key": project_key,
            "status": ProjectStatus.ACTIVE,
            "owner_id": ObjectId(current_user["_id"]),
            "team_size": project.team_size or 1,
            "created_at": now,
            "updated_at": now,
            "is_archived": False,
        }
    )

    result = create_project(project_data)
    
    event = ActivityEvent(
        entity_type=EntityType.PROJECT,
        entity_id=str(result.inserted_id),
        action=ActivityAction.CREATED,
        performed_by=str(current_user["_id"]),
        actor_name=get_actor_name(current_user),
        entity_name=project_data["name"],
        snapshot={k: v for k, v in project_data.items() if k not in ["updated_at"]},
    )
    create_activity_log(event)

    return ProjectResponse(
        id=str(result.inserted_id),
        name=project_data["name"],
        key=project_data["key"],
        description=project_data["description"],
        status=project_data["status"],
        start_date=project_data["start_date"],
        end_date=project_data["end_date"],
        color=project_data["color"],
        icon=project_data["icon"],
        owner_id=str(project_data["owner_id"]),
        members=[str(member) for member in project_data.get("members", [])],
        team_size=project_data.get("team_size", 1),
        is_archived=project_data["is_archived"],
        created_at=project_data["created_at"],
        updated_at=project_data["updated_at"],
    )
def get_all_employee_dropdown(role_id: str | None = "6a55fd1e54a2a5ca60cf3052") -> list[EmployeeAvailableResponse]:
    employees = get_all_employees(role_id=role_id)
    
    return [
        EmployeeAvailableResponse(
            id=str(emp["_id"]),
            name=f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() or emp.get("username", "Unknown"),
            email=emp.get("email", ""),
            role=emp.get("designation") or emp.get("role") or "Developer",
            status="AVAILABLE" if emp.get("is_active", True) else "INACTIVE"
        )
        for emp in employees
    ]
def get_all_active_projects() -> list[ProjectResponse]:
    projects = get_all_projects()
    
    return [
        ProjectResponse(
            id=str(p["_id"]),
            name=p["name"],
            key=p["key"],
            description=p.get("description"),
            status=p["status"],
            start_date=p.get("start_date"),
            end_date=p.get("end_date"),
            color=p["color"],
            icon=p["icon"],
            owner_id=str(p["owner_id"]),
            members=[str(member) for member in p["members"]],
            team_size=p.get("team_size", 1),
            is_archived=p["is_archived"],
            created_at=p["created_at"],
            updated_at=p["updated_at"],
        ) for p in projects
    ]


def _build_project_response(p: dict) -> ProjectResponse:
    pid_str = str(p["_id"])
    team_lead_id = str(p["team_lead_id"]) if p.get("team_lead_id") else None
    team_lead_name = None
    if team_lead_id:
        tl_user = user_collection.find_one({
            "_id": ObjectId(team_lead_id) if ObjectId.is_valid(team_lead_id) else team_lead_id
        })
        if tl_user:
            team_lead_name = f"{tl_user.get('first_name', '')} {tl_user.get('last_name', '')}".strip() or tl_user.get("username")

    # Build assigned member employee names list
    member_names: list[str] = []

    # 1. Collect names from 'assign' collection
    assigned_docs = list(assign_collection.find({"project_id": pid_str}))
    for doc in assigned_docs:
        assigned_to = doc.get("assigned_to")
        if isinstance(assigned_to, dict):
            name = assigned_to.get("name")
            if name and name not in member_names:
                member_names.append(name)
        elif isinstance(assigned_to, str):
            u = user_collection.find_one({"_id": ObjectId(assigned_to) if ObjectId.is_valid(assigned_to) else assigned_to})
            if u:
                name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("username")
                if name and name not in member_names:
                    member_names.append(name)

    # 2. Collect names from project document's 'members' field
    raw_members = p.get("members") or []
    for m in raw_members:
        if isinstance(m, str):
            if ObjectId.is_valid(m):
                u = user_collection.find_one({"_id": ObjectId(m)})
                if u:
                    name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("username")
                    if name and name not in member_names:
                        member_names.append(name)
            else:
                if m and m not in member_names:
                    member_names.append(m)

    return ProjectResponse(
        id=pid_str,
        name=p["name"],
        key=p["key"],
        description=p.get("description"),
        status=p["status"],
        start_date=p.get("start_date"),
        end_date=p.get("end_date"),
        color=p["color"],
        icon=p["icon"],
        owner_id=str(p["owner_id"]),
        team_lead_id=team_lead_id,
        team_lead_name=team_lead_name,
        members=member_names,
        team_size=p.get("team_size", len(member_names) if member_names else 1),
        is_archived=p.get("is_archived", False),
        created_at=p["created_at"],
        updated_at=p["updated_at"],
    )




def get_paginated_projects(
    page: int,
    limit: int,
    search_name: str | None,
    search_key: str | None,
    status: ProjectStatus | None
) -> PaginatedProjectResponse:
    query = {"is_archived": False}

    if search_name:
        query["name"] = {"$regex": search_name, "$options": "i"}
    if search_key:
        query["key"] = {"$regex": search_key, "$options": "i"}
    if status:
        query["status"] = status

    skip = (page - 1) * limit
    projects_data = get_projects_paginated(query, skip, limit)
    total_records = count_projects(query)

    total_pages = (total_records + limit - 1) // limit if total_records > 0 else 0

    employees_list = get_all_employee_dropdown(role_id="6a55fd1e54a2a5ca60cf3052")

    return PaginatedProjectResponse(
        data=[_build_project_response(p) for p in projects_data],
        employees=employees_list,
        page=page,
        limit=limit,
        total_records=total_records,
        total_pages=total_pages
    )


def get_project(project_id: str) -> ProjectResponse:
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID")

    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return _build_project_response(project)



def update_existing_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: dict
) -> ProjectResponse:
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID")

    existing = get_project_by_id(project_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    update_data = project_update.model_dump(exclude_unset=True)

    if not update_data:
        return _build_project_response(existing)

    # Validate dates if they are being updated
    start_date = update_data.get("start_date", existing.get("start_date"))
    end_date = update_data.get("end_date", existing.get("end_date"))

    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be earlier than start date."
        )

    if "members" in update_data:
        # Convert member strings to ObjectIds and ensure owner is always in members? The requirement doesn't explicitly state.
        update_data["members"] = [ObjectId(m) for m in update_data["members"] if ObjectId.is_valid(m)]

    update_data["updated_at"] = datetime.now(timezone.utc)

    update_project(project_id, update_data)

    updated_project = get_project_by_id(project_id)
    
    changes = get_changed_fields(
        existing,
        updated_project,
        exclude_fields=["_id", "created_at", "updated_at"],
    )

    event = ActivityEvent(
        entity_type=EntityType.PROJECT,
        entity_id=project_id,
        action=ActivityAction.UPDATED,
        performed_by=str(current_user["_id"]),
        actor_name=get_actor_name(current_user),
        entity_name=updated_project["name"],
        changes=changes,
    )
    create_activity_log(event)

    return _build_project_response(updated_project)


def soft_delete_project(project_id: str, current_user: dict) -> dict:
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID")

    existing = get_project_by_id(project_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    archive_project(project_id, {
        "is_archived": True,
        "updated_at": datetime.now(timezone.utc)
    })

    event = ActivityEvent(
        entity_type=EntityType.PROJECT,
        entity_id=project_id,
        action=ActivityAction.ARCHIVED,
        performed_by=str(current_user["_id"]),
        actor_name=get_actor_name(current_user),
        entity_name=existing["name"],
        snapshot={k: v for k, v in existing.items() if k not in ["updated_at"]},
    )
    create_activity_log(event)

    return {"message": "Project deleted successfully"}


async def assign_tl_to_project(payload: AssignTeamLeadRequest, current_user: dict):
    if not ObjectId.is_valid(payload.project_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID")
    
    project = get_project_by_id(payload.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    emp_obj_id = ObjectId(payload.emp_id) if ObjectId.is_valid(payload.emp_id) else payload.emp_id

    # Look up assigned employee details from user_collection
    assigned_user = user_collection.find_one({
        "_id": emp_obj_id if isinstance(emp_obj_id, ObjectId) else payload.emp_id
    })

    # Update project with team_lead_id
    update_result = update_project(payload.project_id, {
        "team_lead_id": str(emp_obj_id),
        "updated_at": datetime.now(timezone.utc)
    })

    if not update_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Record who assigned whom in the 'assign' collection
    assigned_by_id = (
        str(current_user["_id"])
        if isinstance(current_user, dict) and "_id" in current_user
        else str(current_user.get("id"))
    )
    assigned_by_name = get_actor_name(current_user) if isinstance(current_user, dict) else "Unknown"
    assigned_by_email = current_user.get("email") if isinstance(current_user, dict) else None

    assigned_to_name = (
        assigned_user.get("full_name") or assigned_user.get("name")
        if assigned_user else str(payload.emp_id)
    )
    assigned_to_email = assigned_user.get("email") if assigned_user else None

    assignment_doc = {
        "project_id": str(payload.project_id),
        "project_name": project.get("name"),
        "assigned_to": {
            "id": str(payload.emp_id),
            "name": assigned_to_name,
            "email": assigned_to_email
        },
        "assigned_by": {
            "id": assigned_by_id,
            "name": assigned_by_name,
            "email": assigned_by_email
        },
        "role": "Team Lead",
        "assigned_at": datetime.now(timezone.utc)
    }

    create_assignment_record(assignment_doc)

    await manager.send_to_user(
        str(payload.emp_id),
        {
            "type": "PROJECT_ASSIGNED",
            "project_id": str(payload.project_id),
            "project_name": project.get("name"),
            "assigned_by": assigned_by_id,
            "assigned_by_name": assigned_by_name,
            "assigned_to_name": assigned_to_name,
            "message": f"This project is assigned to you by your Team Lead ({assigned_by_name})"
        },
    )

    return {
        "message": "Team Lead assigned successfully",
        "project_id": payload.project_id,
        "emp_id": payload.emp_id,
        "assigned_by": assigned_by_id,
        "assigned_by_name": assigned_by_name,
        "assigned_to_name": assigned_to_name
    }


def get_project_assignments() -> list:
    assignments = get_all_assignments()
    result = []
    for item in assignments:
        item["_id"] = str(item["_id"])
        if isinstance(item.get("assigned_at"), datetime):
            item["assigned_at"] = item["assigned_at"].isoformat()
        result.append(item)
    return result