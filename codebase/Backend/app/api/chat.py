from fastapi import APIRouter

from app.ai.orchestrator import orchestrate
from app.models.schemas import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return orchestrate(request)

