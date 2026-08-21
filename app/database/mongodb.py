import os
import certifi
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from pymongo import MongoClient
# pyrefly: ignore [missing-import]
from pymongo.errors import OperationFailure

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL environment variable not found in environment.")

try:
    # Serverless-friendly TLS connection with certifi CA bundle and 5s timeout
    client = MongoClient(
        MONGO_URL,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    client.admin.command("ping")
    print("MongoDB connected successfully with certifi TLS!")
except Exception as e:
    print(f"Primary certifi TLS connection notice: {e}")
    try:
        client = MongoClient(
            MONGO_URL,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000,
        )
        client.admin.command("ping")
        print("MongoDB connected with tlsAllowInvalidCertificates fallback!")
    except Exception as e2:
        print(f"Fallback MongoDB connection notice: {e2}")
        client = MongoClient(MONGO_URL)

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
        if e.code == 85:
            try:
                refresh_tokens_collection.drop_index("expires_at_1")
                refresh_tokens_collection.create_index(
                    [("expires_at", 1)],
                    expireAfterSeconds=0,
                    name="refresh_token_ttl"
                )
            except Exception as drop_err:
                print(f"Index recreation notice: {drop_err}")
        else:
            print(f"Index creation warning: {e}")
    except Exception as general_err:
        print(f"Index creation notice: {general_err}")

    try:
        projects_collection.create_index([("key", 1)], unique=True)
        projects_collection.create_index([("name", 1)])
        projects_collection.create_index([("status", 1)])

        issues_collection.create_index([("issue_key", 1)], unique=True)
        issues_collection.create_index([("title", 1)])
        issues_collection.create_index([("project_id", 1)])
        issues_collection.create_index([("status", 1)])
        issues_collection.create_index([("priority", 1)])
        issues_collection.create_index([("assignee_id", 1)])
        issues_collection.create_index([("reporter_id", 1)])
        issues_collection.create_index([("issue_type", 1)])
    except Exception as idx_err:
        print(f"Indexes creation warning: {idx_err}")

try:
    create_indexes()
except Exception as e:
    print(f"Non-fatal index creation warning: {e}")