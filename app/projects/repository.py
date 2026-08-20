# pyrefly: ignore [missing-import]
from bson import ObjectId
# pyrefly: ignore [missing-import]
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
# pyrefly: ignore [missing-import]
from bson import ObjectId
from app.database.mongodb import projects_collection, user_collection, assign_collection



def create_project(project_data: dict) -> InsertOneResult:
    """
    Create a new project.
    """
    return projects_collection.insert_one(project_data)


def get_project_by_id(project_id: str):
    """
    Get a project by its MongoDB ObjectId.
    """
    return projects_collection.find_one({
        "_id": ObjectId(project_id),
        "is_archived": False
    })


def get_project_by_key(key: str):
    """
    Get project using its unique key.
    """
    return projects_collection.find_one({
        "key": key,
        "is_archived": False
    })

def get_all_employees(role_id: str | None = None):
    """
    Return all active employees. If role_id is specified, filter by role_id.
    """
    query: dict = {"is_active": True}
    if role_id:
        query_conditions = [{"role_id": role_id}]
        try:
            query_conditions.append({"role_id": ObjectId(role_id)})
        except Exception:
            pass
        query["$or"] = query_conditions

    # Print query for debugging
    print("DEBUG - PyMongo Query:", query)

    results = list(user_collection.find(query))
    print("DEBUG - Total Employees Matched:", len(results))
    return results

def get_all_projects():
    """
    Return all active assigned projects.
    """

    assigned_project_ids = assign_collection.distinct("project_id")

    object_ids = [
        ObjectId(pid)
        for pid in assigned_project_ids
        if ObjectId.is_valid(pid)
    ]

    return list(
        projects_collection.find(
            {
                "_id": {"$in": object_ids},
                "is_archived": False,
            }
        ).sort("created_at", -1)
    )

def get_projects_paginated(query: dict, skip: int, limit: int):
    """
    Return paginated projects based on a query.
    """
    return list(
        projects_collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )


def count_projects(query: dict) -> int:
    """
    Count total projects based on a query.
    """
    return projects_collection.count_documents(query)


def update_project(
    project_id: str,
    update_data: dict
) -> UpdateResult:
    """
    Update project.
    """
    return projects_collection.update_one(
        {
            "_id": ObjectId(project_id),
            "is_archived": False
        },
        {
            "$set": update_data
        }
    )


def archive_project(project_id: str, update_data: dict) -> UpdateResult:
    """
    Soft delete (archive) project.
    """
    return projects_collection.update_one(
        {
            "_id": ObjectId(project_id)
        },
        {
            "$set": update_data
        }
    )


def delete_project(project_id: str) -> DeleteResult:
    """
    Permanently delete project.
    Normally not used.
    """
    return projects_collection.delete_one({
        "_id": ObjectId(project_id)
    })


def create_assignment_record(assignment_data: dict) -> InsertOneResult:
    """
    Save assignment record to the 'assign' collection.
    """
    return assign_collection.insert_one(assignment_data)


def get_all_assignments():
    """
    Get all assignment records from the 'assign' collection.
    """
    return list(assign_collection.find().sort("assigned_at", -1))

def search_projects(query: dict):
    """
    Search projects using MongoDB filters.
    Used by AI natural-language search.
    """
    query["is_archived"] = False

    return list(
        projects_collection.find(query)
        .sort("created_at", -1)
    )
def get_project_by_name(name: str):
    """
    Get active project by name.
    """
    return projects_collection.find_one({
        "name": {
            "$regex": name,
            "$options": "i"
        },
        "is_archived": False
    })