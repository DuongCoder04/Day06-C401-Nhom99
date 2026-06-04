from models.schemas import MenuItem
from services.menu_service import MenuService


class Recommender:
    def __init__(self, menu_service: MenuService) -> None:
        self.menu_service = menu_service

    def recommend(self, intent: str, message: str, budget: int | None = None, diet: str | None = None) -> list[MenuItem]:
        items = self.menu_service.get_all()
        text = message.lower().strip()

        if intent == "BY_BUDGET":
            extracted_budget = self._extract_budget(text)
            if extracted_budget is not None:
                budget = extracted_budget

        if intent == "BY_DIET" and diet is None:
            if "low carb" in text:
                diet = "low_carb"
            elif "high protein" in text:
                diet = "high_protein"
            elif "ăn kiêng" in text or "healthy" in text:
                diet = "healthy"
            elif "low cal" in text or "giảm cân" in text:
                diet = "low_cal"

        if budget is not None:
            items = [item for item in items if item.price <= budget]

        if diet:
            diet_key = diet.lower().strip()
            items = [
                item
                for item in items
                if diet_key in item.tags or diet_key in item.category.lower() or diet_key in item.name.lower()
            ]

        if intent == "FIND_FOOD":
            items = sorted(items, key=lambda item: ("popular" not in item.tags, item.price))

        return items[:3]

    def _extract_budget(self, text: str) -> int | None:
        digits = "".join(ch if ch.isdigit() else " " for ch in text).split()
        if not digits:
            return None
        return int(digits[0])
