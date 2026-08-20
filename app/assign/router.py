from fastapi import APIRouter, Depends, status

from app.auth.permissions import require_permission
