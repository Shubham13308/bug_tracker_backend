from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.users.router import router as user_router
from app.roles.router import router as role_router
from app.auth.router import router as auth_router
from app.projects.router import router as project_router
from app.issues.router import router as issue_router
from app.activity.router import router as activity_router
from app.permissions.router import router as permission_router
from app.role_permissions.router import router as role_permission_router
from app.websocket.router import router as websocket_router
from app.ai.router import router as ai_router
app = FastAPI(title="Project and Bug Tracker",version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://bugtrackerfrontend.vercel.app",
        "https://bug-tracker-frontend.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router,prefix="/api/v1/users",tags=["Users"])
app.include_router(role_router,prefix="/api/v1/roles",tags=["Roles"])
app.include_router(role_permission_router,prefix="/api/v1/roles",tags=["Role Permissions"])
app.include_router(auth_router,prefix="/api/v1/auth",tags=["Authentication"])
app.include_router(project_router,prefix="/api/v1/projects",tags=["Projects"])
app.include_router(issue_router,prefix="/api/v1/issues",tags=["Issues"])
app.include_router(activity_router,prefix="/api/v1/activities",tags=["Activities"])
app.include_router(permission_router,prefix="/api/v1/permissions",tags=["Permissions"])
app.include_router(websocket_router,prefix="/api/v1",tags=["WebSocket"])
app.include_router(ai_router,prefix="/api/v1",tags=["AI"])
@app.get("/")
def home():

    return {
        "message": "Project and Bug Tracker API"
    }   