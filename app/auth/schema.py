# pyrefly: ignore [missing-import]
from pydantic import BaseModel,EmailStr

class LoginRequest(BaseModel):
    email:EmailStr
    password:str

class LoginResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str = "Bearer"

class RefreshTokenResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str = "Bearer"

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    created_at: str
