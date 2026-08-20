# pyrefly: ignore [missing-import]
from bson import ObjectId

from app.database.mongodb import db

activity_collection = db["activities"]


def log_activity(activity_data: dict):
    """
    Insert a new activity log into MongoDB.
    """
    result = activity_collection.insert_one(activity_data)

    return activity_collection.find_one({"_id": result.inserted_id})


def get_activities(
    page: int = 1,
    limit: int = 10,
    filters: dict | None = None,
):
    """
    Fetch paginated activity logs.
    """

    if filters is None:
        filters = {}

    skip = (page - 1) * limit

    activities = list(
        activity_collection.find(filters)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total_records = activity_collection.count_documents(filters)

    total_pages = (
        total_records + limit - 1
    ) // limit

    return {
        "activities": activities,
        "page": page,
        "limit": limit,
        "total_records": total_records,
        "total_pages": total_pages,
    }


def get_activity_by_id(activity_id: str):
    """
    Fetch a single activity log.
    """

    return activity_collection.find_one(
        {"_id": ObjectId(activity_id)}
    )
