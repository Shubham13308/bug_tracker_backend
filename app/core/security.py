import os
from datetime import datetime,timedelta,timezone
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from jose import JWTError,jwt
# pyrefly: ignore [missing-import]
from passlib.context import CryptContext
from uuid import uuid4
load_dotenv()
# Password Hashing and Verification
password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "default_jwt_secret_key_change_in_production"
ALGORITHM = os.getenv("JWT_ALGORITHM") or os.getenv("ALGORITHM") or "HS256"
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 15

try:
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
except ValueError:
    REFRESH_TOKEN_EXPIRE_DAYS = 7

def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return password_context.verify(
        plain_password,
        hashed_password
    )

def create_access_token(user_id:str)-> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload={"sub":str(user_id),"token_type":"access","exp":expire}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    token_id = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id,"token_type": "refresh","jti": token_id,"exp": expire}
    token = jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
    return token, token_id

def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_access_token(token:str)->dict:
    payload=decode_token(token)
    if not payload or payload.get("token_type") != "access":
        raise ValueError("Invalid token")
    return payload
