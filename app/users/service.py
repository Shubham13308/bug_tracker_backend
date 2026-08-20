from datetime import datetime, timezone
from fastapi import HTTPException
from app.database.mongodb import db
from app.users.schema import UserCreate
from app.core.security import hash_password

from app.roles.repository import get_all_roles_from_db

user_collection = db['users']


def create_user(user: UserCreate):
    email = str(user.email).lower()
    username = user.username.lower()
    existing_user = user_collection.find_one({
        "$or": [
            {"email": email},
            {"username": username}
        ]
    })
    if existing_user:
        if existing_user.get("email") == email:
            raise HTTPException(status_code=400, detail="Email already exists")
        else:
            raise HTTPException(status_code=400, detail="Username already exists")
    user_data = user.model_dump()
    user_data['email'] = email
    user_data['username'] = username
    user_data['password'] = hash_password(user.password)
    user_data['is_active'] = True
    user_data['role_id'] = user_data.get('role_id') or "6a55fd6054a2a5ca60cf3054"
    user_data['designation'] = user_data.get('designation') or ""
    user_data['reporting_manager_id'] = user_data.get('reporting_manager_id') or None


    now = datetime.now(timezone.utc)
    user_data['created_at'] = now
    user_data['updated_at'] = now

    result = user_collection.insert_one(user_data)
    return {
        "id": str(result.inserted_id),
        "email": user_data['email'],
        "username": user_data['username'],
        "first_name": user_data['first_name'],
        "last_name": user_data['last_name'],
        "role_id": user_data['role_id'],
        "is_active": user_data['is_active'],
        "designation": user_data['designation'],
        "reporting_manager_id": user_data['reporting_manager_id'],
        "created_at": user_data['created_at'],
        "updated_at": user_data['updated_at']
    }



def get_roles_dropdown_list():
    roles_db = get_all_roles_from_db()
    return [
        {
            "id": str(r["_id"]),
            "name": str(r.get("name", "")),
            "description": r.get("description")
        }
        for r in roles_db
    ]


def get_all_users():
    users = list(user_collection.find({"is_active": True}))
    roles_db = get_all_roles_from_db()

    role_map = {str(r["_id"]): str(r.get("name", "")) for r in roles_db}

    # Fetch issues and projects to dynamically compute user status & workload
    issues_collection = db["issues"]
    projects_collection = db["projects"]
    all_issues = list(issues_collection.find({}))
    all_projects = list(projects_collection.find({"is_archived": False}))

    user_list = []
    for u in users:
        u_id_str = str(u["_id"])
        full_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip().lower()

        # Find issues assigned to this user
        user_issues = [
            iss for iss in all_issues
            if (iss.get("assignee_id") and (str(iss["assignee_id"]) == u_id_str or iss["assignee_id"] == u["_id"]))
        ]

        # Find projects where user is lead, owner or member
        user_projects = [
            p for p in all_projects
            if (p.get("team_lead_id") and str(p["team_lead_id"]) == u_id_str) or
               (p.get("owner_id") and str(p["owner_id"]) == u_id_str) or
               any(full_name and full_name in str(m).lower() or u_id_str in str(m) for m in p.get("members", []))
        ]

        assigned_count = len(user_issues)
        has_projects = len(user_projects) > 0
        is_assigned = assigned_count > 0 or has_projects or u.get("status") == "ASSIGNED"

        status_val = "ASSIGNED" if is_assigned else u.get("status", "AVAILABLE")
        proj_name = user_projects[0].get("name") if user_projects else (u.get("current_project") if is_assigned else "Unassigned")
        issue_titles = [f"{iss.get('issue_key', 'ISSUE')}: {iss.get('title', '')}" for iss in user_issues]

        user_list.append({
            "id": u_id_str,
            "_id": u_id_str,
            "username": u["username"],
            "first_name": u.get("first_name", ""),
            "last_name": u.get("last_name", ""),
            "email": u["email"],
            "designation": u.get("designation"),
            "reporting_manager_id": u.get("reporting_manager_id"),
            "role_id": str(u.get("role_id")) if u.get("role_id") else "",
            "role": u.get("role") or (role_map.get(str(u.get("role_id"))) if u.get("role_id") else None),
            "is_active": u.get("is_active", True),
            "status": status_val,
            "assigned_tasks_count": assigned_count if assigned_count > 0 else (1 if is_assigned else 0),
            "current_project": proj_name,
            "assigned_issues": issue_titles,
            "skills": u.get("skills", ["React", "FastAPI", "Python"]),
            "phone": u.get("phone", "+1 (555) 000-0000"),
            "avatar_color": u.get("avatar_color", "bg-blue-600"),
            "created_at": u.get("created_at"),
            "updated_at": u.get("updated_at")
        })

    roles_dropdown = [
        {
            "id": str(r["_id"]),
            "name": str(r.get("name", "")),
            "description": r.get("description")
        }
        for r in roles_db
    ]

    return {
        "data": user_list,
        "roles": roles_dropdown
    }


