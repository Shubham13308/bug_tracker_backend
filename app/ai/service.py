import os
import re

# pyrefly: ignore [missing-import]
from bson import ObjectId
from datetime import datetime
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv, find_dotenv
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types

from app.ai.prompt import AI_SEARCH_SYSTEM_PROMPT
from app.ai.schema import AISearchIntent
from app.database.mongodb import (
    projects_collection,
    issues_collection,
    user_collection,
    assign_collection,
)

load_dotenv(find_dotenv())

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None


def understand_search_query(query: str) -> AISearchIntent:
    """
    Call Gemini API to convert natural language prompt into a structured intent JSON.
    Used for debug/internal testing.
    """
    if not client:
        return AISearchIntent(entity="project", search_text=query)

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            AI_SEARCH_SYSTEM_PROMPT,
            f"User request:\n{query}",
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AISearchIntent,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    return AISearchIntent.model_validate_json(response.text)


def execute_ai_search(query: str) -> dict:
    """
    Single unified AI search service endpoint for Projects, Issues, Employees, and Assignments.
    1. Parses natural-language intent via Gemini.
    2. Queries relevant MongoDB collection(s): Projects, Issues, Users, Assignments.
    3. Formats results cleanly for React frontend.
    """
    intent = understand_search_query(query)

    # -------------------------------------------------------------
    # 1. SEARCH PROJECTS
    # -------------------------------------------------------------
    if intent.entity == "project":
        mongo_query: dict = {"is_archived": False}

        if intent.project_key:
            mongo_query["key"] = {"$regex": f"^{re.escape(intent.project_key)}$", "$options": "i"}

        if intent.project_name:
            mongo_query["name"] = {"$regex": re.escape(intent.project_name), "$options": "i"}

        if intent.status:
            mongo_query["status"] = {"$regex": re.escape(intent.status), "$options": "i"}

        if intent.search_text and not intent.project_name:
            mongo_query["$or"] = [
                {"name": {"$regex": re.escape(intent.search_text), "$options": "i"}},
                {"description": {"$regex": re.escape(intent.search_text), "$options": "i"}},
                {"key": {"$regex": re.escape(intent.search_text), "$options": "i"}},
            ]

        projects = list(projects_collection.find(mongo_query).sort("created_at", -1))

        results = []
        for p in projects:
            members_list = p.get("members", [])
            results.append({
                "id": str(p["_id"]),
                "name": p.get("name"),
                "key": p.get("key"),
                "description": p.get("description"),
                "status": p.get("status", "ACTIVE"),
                "team_size": p.get("team_size") or (len(members_list) if isinstance(members_list, list) else 0),
            })

        return {
            "message": f"Found {len(results)} project(s).",
            "results": results,
        }

    # -------------------------------------------------------------
    # 2. SEARCH ISSUES
    # -------------------------------------------------------------
    if intent.entity == "issue":
        mongo_query: dict = {}

        # Project lookup by key or name
        if intent.project_key:
            proj = projects_collection.find_one({"key": {"$regex": f"^{re.escape(intent.project_key)}$", "$options": "i"}})
            if proj:
                mongo_query["project_id"] = proj["_id"]
            else:
                return {"message": f"Project '{intent.project_key}' was not found.", "results": []}

        elif intent.project_name:
            proj = projects_collection.find_one({"name": {"$regex": re.escape(intent.project_name), "$options": "i"}})
            if proj:
                mongo_query["project_id"] = proj["_id"]
            else:
                return {"message": f"Project '{intent.project_name}' was not found.", "results": []}

        # Issue attributes
        if intent.status:
            mongo_query["status"] = {"$regex": f"^{re.escape(intent.status)}$", "$options": "i"}

        if intent.priority:
            mongo_query["priority"] = {"$regex": f"^{re.escape(intent.priority)}$", "$options": "i"}

        if intent.issue_type:
            mongo_query["issue_type"] = {"$regex": f"^{re.escape(intent.issue_type)}$", "$options": "i"}

        # Assignee lookup by person name
        person = intent.person_name or intent.assigned_to_name
        if person:
            user_doc = user_collection.find_one({
                "$or": [
                    {"first_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"last_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"username": {"$regex": re.escape(person), "$options": "i"}},
                ]
            })
            if user_doc:
                mongo_query["assignee_id"] = user_doc["_id"]

        if intent.search_text:
            mongo_query["$or"] = [
                {"title": {"$regex": re.escape(intent.search_text), "$options": "i"}},
                {"description": {"$regex": re.escape(intent.search_text), "$options": "i"}},
                {"issue_key": {"$regex": re.escape(intent.search_text), "$options": "i"}},
            ]

        issues = list(issues_collection.find(mongo_query).sort("created_at", -1))

        results = []
        for issue in issues:
            results.append({
                "id": str(issue["_id"]),
                "issue_key": issue.get("issue_key"),
                "title": issue.get("title"),
                "description": issue.get("description"),
                "project_id": str(issue.get("project_id")) if issue.get("project_id") else None,
                "priority": issue.get("priority"),
                "status": issue.get("status"),
                "issue_type": issue.get("issue_type"),
            })

        return {
            "message": f"Found {len(results)} issue(s).",
            "results": results,
        }

    # -------------------------------------------------------------
    # 3. SEARCH EMPLOYEES / USERS (with optional detailed profile lookup)
    # -------------------------------------------------------------
    if intent.entity == "employee":
        mongo_query: dict = {}

        person = intent.person_name or intent.search_text
        if person:
            tokens = person.strip().split()
            if len(tokens) >= 2:
                first, last = tokens[0], tokens[-1]
                mongo_query["$or"] = [
                    {"$and": [
                        {"first_name": {"$regex": re.escape(first), "$options": "i"}},
                        {"last_name": {"$regex": re.escape(last), "$options": "i"}}
                    ]},
                    {"first_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"last_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"username": {"$regex": re.escape(person), "$options": "i"}},
                    {"email": {"$regex": re.escape(person), "$options": "i"}},
                ]
            else:
                mongo_query["$or"] = [
                    {"first_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"last_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"username": {"$regex": re.escape(person), "$options": "i"}},
                    {"email": {"$regex": re.escape(person), "$options": "i"}},
                    {"role": {"$regex": re.escape(person), "$options": "i"}},
                    {"designation": {"$regex": re.escape(person), "$options": "i"}},
                ]

        if intent.role:
            mongo_query["role"] = {"$regex": re.escape(intent.role), "$options": "i"}

        users = list(user_collection.find(mongo_query))

        results = []
        for u in users:
            first_name = u.get("first_name", "")
            last_name = u.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or u.get("username", "Employee")
            u_id = u["_id"]
            u_id_str = str(u_id)

            emp_data = {
                "id": u_id_str,
                "name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "username": u.get("username"),
                "email": u.get("email"),
                "role": u.get("role") or u.get("designation") or "Employee",
                "designation": u.get("designation"),
                "status": "ACTIVE" if u.get("is_active", True) else "INACTIVE",
            }

            if intent.show_details:
                # Retrieve projects for this employee
                user_projects = list(projects_collection.find({
                    "is_archived": False,
                    "$or": [
                        {"members": u_id_str},
                        {"members": u_id},
                        {"owner_id": u_id_str},
                        {"owner_id": u_id}
                    ]
                }))
                emp_data["projects"] = [
                    {
                        "id": str(p["_id"]),
                        "name": p.get("name"),
                        "key": p.get("key"),
                        "status": p.get("status")
                    } for p in user_projects
                ]

                # Retrieve issues assigned to this employee
                user_issues = list(issues_collection.find({
                    "$or": [
                        {"assignee_id": u_id},
                        {"assignee_id": u_id_str}
                    ]
                }))
                emp_data["issues"] = [
                    {
                        "id": str(i["_id"]),
                        "issue_key": i.get("issue_key"),
                        "title": i.get("title"),
                        "status": i.get("status"),
                        "priority": i.get("priority")
                    } for i in user_issues
                ]

                emp_data["description"] = f"Role: {emp_data['role']} | Projects: {len(user_projects)} | Issues: {len(user_issues)}"

            results.append(emp_data)

        return {
            "message": f"Found {len(results)} employee(s).",
            "results": results,
        }

    # -------------------------------------------------------------
    # 4. SEARCH ASSIGNMENTS / TEAM MEMBERSHIPS
    # -------------------------------------------------------------
    if intent.entity == "assignment":
        results = []

        # Case A: Person's name is specified -> find projects assigned to this person
        person = intent.person_name or intent.assigned_to_name or intent.search_text
        if person and not (intent.project_key or intent.project_name):
            user_doc = user_collection.find_one({
                "$or": [
                    {"first_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"last_name": {"$regex": re.escape(person), "$options": "i"}},
                    {"username": {"$regex": re.escape(person), "$options": "i"}},
                ]
            })

            user_id_str = str(user_doc["_id"]) if user_doc else None

            # Look up projects where user is owner or member
            if user_id_str:
                proj_query = {
                    "is_archived": False,
                    "$or": [
                        {"members": user_id_str},
                        {"members": user_doc["_id"]},
                        {"owner_id": user_id_str},
                        {"owner_id": user_doc["_id"]}
                    ]
                }
                projs = list(projects_collection.find(proj_query))
                for p in projs:
                    results.append({
                        "id": str(p["_id"]),
                        "name": p.get("name"),
                        "key": p.get("key"),
                        "description": f"Assigned project for {user_doc.get('first_name', person)}",
                        "status": p.get("status", "ACTIVE"),
                        "team_size": p.get("team_size") or len(p.get("members", [])),
                    })

            # Also check assign_collection
            if user_id_str:
                assign_query = {
                    "$or": [
                        {"assignee_id": user_id_str},
                        {"assigned_to.name": {"$regex": re.escape(person), "$options": "i"}}
                    ]
                }

                assignments = list(assign_collection.find(assign_query).sort("assigned_at", -1))
                for a in assignments:
                    results.append({
                        "id": str(a["_id"]),
                        "name": a.get("project_name") or a.get("issue_key") or "Project Assignment",
                        "key": a.get("issue_key") or a.get("project_id"),
                        "description": f"Assigned to {a.get('assigned_to', {}).get('name', person)} ({a.get('role', 'Developer')})",
                        "status": "ACTIVE",
                    })

            if results:
                return {
                    "message": f"Found {len(results)} assigned record(s) for '{person}'.",
                    "results": results,
                }

        # Case B: Project key/name specified -> find people assigned to this project
        proj_identifier = intent.project_key or intent.project_name or intent.search_text
        if proj_identifier:
            proj = projects_collection.find_one({
                "$or": [
                    {"key": {"$regex": f"^{re.escape(proj_identifier)}$", "$options": "i"}},
                    {"name": {"$regex": re.escape(proj_identifier), "$options": "i"}}
                ]
            })

            if proj:
                proj_id_str = str(proj["_id"])
                assign_records = list(assign_collection.find({"project_id": proj_id_str}))
                member_ids = proj.get("members", [])

                assigned_users = []
                for rec in assign_records:
                    u_info = rec.get("assigned_to", {})
                    if u_info.get("name"):
                        assigned_users.append({
                            "id": rec.get("assignee_id") or str(rec["_id"]),
                            "name": u_info.get("name"),
                            "email": u_info.get("email"),
                            "role": rec.get("role", "Team Member"),
                            "status": "ACTIVE",
                            "description": f"Assigned to project {proj.get('name')}"
                        })

                if not assigned_users and member_ids:
                    for m_id in member_ids:
                        try:
                            u_doc = user_collection.find_one({"_id": ObjectId(m_id) if ObjectId.is_valid(m_id) else m_id})
                            if u_doc:
                                assigned_users.append({
                                    "id": str(u_doc["_id"]),
                                    "name": f"{u_doc.get('first_name', '')} {u_doc.get('last_name', '')}".strip() or u_doc.get("username"),
                                    "email": u_doc.get("email"),
                                    "role": u_doc.get("role") or u_doc.get("designation") or "Developer",
                                    "status": "ACTIVE",
                                    "description": f"Member of {proj.get('name')}"
                                })
                        except Exception:
                            pass

                if assigned_users:
                    return {
                        "message": f"Found {len(assigned_users)} member(s) assigned to '{proj.get('name')}'.",
                        "results": assigned_users,
                    }

    # -------------------------------------------------------------
    # 5. MULTI-COLLECTION FALLBACK SEARCH (If no specific entity match)
    # -------------------------------------------------------------
    search_term = intent.search_text or intent.person_name or intent.project_name or query.strip()
    if search_term:
        regex_pattern = {"$regex": re.escape(search_term), "$options": "i"}

        matched_projects = list(projects_collection.find({
            "is_archived": False,
            "$or": [{"name": regex_pattern}, {"key": regex_pattern}, {"description": regex_pattern}]
        }).limit(5))

        matched_issues = list(issues_collection.find({
            "$or": [{"title": regex_pattern}, {"issue_key": regex_pattern}, {"description": regex_pattern}]
        }).limit(5))

        matched_users = list(user_collection.find({
            "$or": [{"first_name": regex_pattern}, {"last_name": regex_pattern}, {"username": regex_pattern}, {"email": regex_pattern}]
        }).limit(5))

        results = []
        for p in matched_projects:
            results.append({
                "id": str(p["_id"]),
                "name": p.get("name"),
                "key": p.get("key"),
                "description": p.get("description"),
                "status": p.get("status", "ACTIVE"),
                "team_size": p.get("team_size") or len(p.get("members", [])),
            })

        for i in matched_issues:
            results.append({
                "id": str(i["_id"]),
                "issue_key": i.get("issue_key"),
                "title": i.get("title"),
                "description": i.get("description"),
                "priority": i.get("priority"),
                "status": i.get("status"),
                "issue_type": i.get("issue_type"),
            })

        for u in matched_users:
            full_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("username")
            results.append({
                "id": str(u["_id"]),
                "name": full_name,
                "email": u.get("email"),
                "role": u.get("role") or u.get("designation") or "Employee",
                "status": "ACTIVE",
            })

        if results:
            return {
                "message": f"Found {len(results)} matching record(s).",
                "results": results,
            }

    return {
        "message": "No matching results found for your request.",
        "results": [],
    }