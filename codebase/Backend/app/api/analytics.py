from fastapi import APIRouter

from app.db.sqlite_store import get_analytics


router = APIRouter(tags=["analytics"])


@router.get("/analytics")
def analytics() -> dict:
    return get_analytics()

