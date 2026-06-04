from fastapi import APIRouter

from app.data.menu_store import load_menu
from app.models.schemas import Dish


router = APIRouter(tags=["menu"])


@router.get("/menu", response_model=list[Dish])
def menu() -> list[Dish]:
    return load_menu()

