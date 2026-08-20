import os

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from pymongo import MongoClient
# pyrefly: ignore [missing-import]
from pymongo.errors import OperationFailure

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL environment variable not found.")

try:
    client = MongoClient(MONGO_URL)
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except Exception as e:
    raise RuntimeError(f"Failed to connect to MongoDB: {e}")

db = client["bug_tracker"]

issues_collection = db["issues"]
user_collection = db["users"]
refresh_tokens_collection = db["refresh_tokens"]
projects_collection = db["projects"]
assign_collection = db["assign"]

def create_indexes():
    try:
        refresh_tokens_collection.create_index(
            [("expires_at", 1)],
            expireAfterSeconds=0,
            name="refresh_token_ttl"
        )
    except OperationFailure as e:
        # Code 85 is IndexOptionsConflict
        if e.code == 85:
            print("Dropping old index and recreating with new options...")
            refresh_tokens_collection.drop_index("expires_at_1")
            refresh_tokens_collection.create_index(
                [("expires_at", 1)],
                expireAfterSeconds=0,
                name="refresh_token_ttl"
            )
        else:
            raise

    # Projects indexes
    projects_collection.create_index([("key", 1)], unique=True)
    projects_collection.create_index([("name", 1)])
    projects_collection.create_index([("status", 1)])

    # Issues indexes
    issues_collection.create_index([("issue_key", 1)], unique=True)
    issues_collection.create_index([("title", 1)])
    issues_collection.create_index([("project_id", 1)])
    issues_collection.create_index([("status", 1)])
    issues_collection.create_index([("priority", 1)])
    issues_collection.create_index([("assignee_id", 1)])
    issues_collection.create_index([("reporter_id", 1)])
    issues_collection.create_index([("issue_type", 1)])


create_indexes()