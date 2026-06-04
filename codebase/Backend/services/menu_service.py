import json
from pathlib import Path

from models.schemas import MenuItem

MENU_PATH = Path(__file__).resolve().parent.parent / "data" / "menu.json"


class MenuService:
    def __init__(self) -> None:
        self._items = self._load_items()

    def _load_items(self) -> list[MenuItem]:
        raw_items = json.loads(MENU_PATH.read_text(encoding="utf-8"))
        return [MenuItem.model_validate(item) for item in raw_items]

    def get_all(self) -> list[MenuItem]:
        return self._items

    def get_by_id(self, dish_id: str) -> MenuItem | None:
        return next((item for item in self._items if item.id == dish_id), None)

    def search(self, query: str | None = None, budget: int | None = None, diet: str | None = None) -> list[MenuItem]:
        items = self._items

        if query:
            needle = query.lower().strip()
            items = [
                item
                for item in items
                if needle in item.name.lower()
                or needle in item.restaurant.lower()
                or any(needle in tag.lower() for tag in item.tags)
            ]

        if budget is not None:
            items = [item for item in items if item.price <= budget]

        if diet:
            diet_key = diet.lower().strip()
            items = [
                item
                for item in items
                if diet_key in item.tags or diet_key in item.category.lower() or diet_key in item.name.lower()
            ]

        return items
