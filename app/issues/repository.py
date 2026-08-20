# pyrefly: ignore [missing-import]
from bson import ObjectId
# pyrefly: ignore [missing-import]
from pymongo import DESCENDING
# pyrefly: ignore [missing-import]
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from app.database.mongodb import issues_collection


def create_issue(issue_data: dict) -> InsertOneResult:
    """
    Create a new issue.
    """
    return issues_collection.insert_one(issue_data)


def get_issue_by_id(issue_id: str):
    """
    Get issue by MongoDB ObjectId.
    """
    return issues_collection.find_one(
        {
            "_id": ObjectId(issue_id)
        }
    )


def get_issue_by_key(issue_key: str):
    """
    Get issue by issue key.
    Example: EMS-1
    """
    return issues_collection.find_one(
        {
            "issue_key": issue_key
        }
    )


def get_project_issues(project_id: str):
    """
    Get all issues of a project.
    """
    return list(
        issues_collection.find(
            {
                "project_id": ObjectId(project_id)
            }
        ).sort("created_at", DESCENDING)
    )


def get_last_issue(project_id: str):
    """
    Return latest issue of a project.
    Used for generating next issue number.
    """
    return issues_collection.find_one(
        {
            "project_id": ObjectId(project_id)
        },
        sort=[("issue_no", DESCENDING)]
    )


def get_issues_paginated(query: dict, skip: int, limit: int):
    """
    Get paginated issues based on a query.
    """
    return list(
        issues_collection.find(query)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )


def count_issues(query: dict) -> int:
    """
    Count total issues based on a query.
    """
    return issues_collection.count_documents(query)


def update_issue(
    issue_id: str,
    update_data: dict,
) -> UpdateResult:
    """
    Update issue.
    """
    return issues_collection.update_one(
        {
            "_id": ObjectId(issue_id)
        },
        {
            "$set": update_data
        }
    )


def delete_issue(issue_id: str) -> DeleteResult:
    """
    Permanently delete issue.
    """
    return issues_collection.delete_one(
        {
            "_id": ObjectId(issue_id)
        }
    )

def search_issues(query: dict):
    """
    Search issues using MongoDB filters.
    Used by AI natural-language search.
    """
    return list(
        issues_collection.find(query)
        .sort("created_at", DESCENDING)
    )