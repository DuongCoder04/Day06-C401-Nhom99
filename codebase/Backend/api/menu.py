from fastapi import APIRouter, Query

from models.schemas import MenuResponse
from services.state import menu_service

router = APIRouter()


@router.get("", response_model=MenuResponse)
def get_menu() -> MenuResponse:
    return MenuResponse(items=menu_service.get_all())


@router.get("/search", response_model=MenuResponse)
def search_menu(
    q: str | None = Query(default=None),
    budget: int | None = Query(default=None),
    diet: str | None = Query(default=None),
) -> MenuResponse:
    return MenuResponse(items=menu_service.search(query=q, budget=budget, diet=diet))
