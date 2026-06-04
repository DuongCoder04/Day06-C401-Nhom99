from fastapi import APIRouter

from app.db.sqlite_store import get_preferences, save_preference
from app.models.schemas import SavePreferenceRequest


router = APIRouter(tags=["preferences"])


@router.post("/preferences")
def save_user_preference(request: SavePreferenceRequest) -> dict:
    save_preference(request.session_id, request.preference_key, request.preference_value)
    return {"success": True, "preferences": get_preferences(request.session_id)}


@router.get("/preferences/{session_id}")
def read_user_preferences(session_id: str) -> dict:
    return {"preferences": get_preferences(session_id)}

