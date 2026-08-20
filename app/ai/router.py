from fastapi import APIRouter

from app.ai.schema import (
    AISearchRequest,
    AISearchIntent,
    AISearchResponse,
)
from app.ai.service import (
    understand_search_query,
    execute_ai_search,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/understand",
    response_model=AISearchIntent,
    summary="Debug/Internal endpoint: Understand natural language query intent"
)
def understand_ai_query(
    request: AISearchRequest,
):
    return understand_search_query(request.query)


@router.post(
    "/search",
    response_model=AISearchResponse,
    summary="Unified AI search endpoint across Projects, Issues, Employees, and Assignments"
)
def ai_search(
    request: AISearchRequest,
):
    return execute_ai_search(request.query)