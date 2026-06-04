from datetime import datetime

from app.data.menu_store import get_restaurant, load_menu
from app.models.schemas import Dish, Entities, Suggestion


def _meal_time() -> str:
    hour = datetime.now().hour
    if 6 <= hour < 10:
        return "breakfast"
    if 10 <= hour < 14:
        return "lunch"
    if 14 <= hour < 17:
        return "snack"
    if 17 <= hour < 22:
        return "dinner"
    return "late_night"


def _effective_meal_time(entities: Entities) -> str:
    return entities.meal_time or _meal_time()


def _score(dish: Dish, entities: Entities) -> float:
    score = dish.popularity * 40
    meal = _effective_meal_time(entities)

    if meal in dish.meal_tags:
        score += 22
    if entities.budget_max and dish.price <= entities.budget_max:
        score += 35
    if entities.budget_max and dish.price > entities.budget_max:
        score -= 80
    if entities.diet_type and entities.diet_type in dish.diet_tags:
        score += 45
    if entities.diet_type and entities.diet_type not in dish.diet_tags:
        score -= 35
    if entities.preference_hint == "hearty" and dish.category in {"rice", "noodle", "hotpot", "combo"}:
        score += 22
    if entities.preference_hint == "light" and dish.category in {"salad", "snack", "sandwich"}:
        score += 22
    if entities.weather in {"rain", "cold"} and dish.is_hot:
        score += 20
    if entities.weather == "rain":
        score += dish.comfort_score * 18
    if entities.group_size and entities.group_size >= 3 and dish.shareable:
        score += 45
    if entities.group_size and entities.group_size >= 3 and not dish.shareable:
        score -= 20

    restaurant = get_restaurant(dish.restaurant)
    if restaurant:
        if restaurant["is_open"]:
            score += 12
        else:
            score -= 70
        if restaurant["delivery_minutes"] <= 20:
            score += 10
        if restaurant["rating"] >= 4.5:
            score += 8

    return score


def _reason(dish: Dish, entities: Entities) -> str:
    meal = _effective_meal_time(entities)

    if entities.budget_max:
        return f"Hợp ngân sách {entities.budget_max:,}đ và vẫn dễ chọn cho bữa này."
    if entities.diet_type == "low_cal":
        return "Nhẹ bụng và hợp khi bạn muốn ăn healthy."
    if entities.diet_type == "high_protein":
        return "Nhiều đạm hơn, hợp khi bạn muốn ăn chắc bụng."
    if entities.preference_hint == "hearty":
        return "No bụng hơn, hợp khi bạn muốn một bữa chắc dạ."
    if entities.preference_hint == "light":
        return "Thanh nhẹ và dễ ăn hơn cho bữa này."
    if entities.group_size:
        return f"Phù hợp hơn khi đặt cho nhóm {entities.group_size} người."
    if entities.weather in {"rain", "cold"}:
        return "Món nóng, hợp lúc trời mưa hoặc se lạnh."
    if meal == "breakfast":
        return "Hợp buổi sáng và dễ bắt đầu ngày mới."
    if meal == "lunch":
        return "Hợp bữa trưa vì đủ no mà không quá nặng."
    if meal == "dinner":
        return "Hợp bữa tối và dễ quyết định nhanh."
    if meal == "late_night":
        return "Dễ ăn hơn cho bữa khuya."
    restaurant = get_restaurant(dish.restaurant)
    if restaurant and restaurant["delivery_minutes"] <= 20:
        return f"Từ quán đang mở, giao khoảng {restaurant['delivery_minutes']} phút."
    return "Phổ biến, dễ ăn và hợp để chốt món nhanh."


def _to_suggestion(dish: Dish, reason: str) -> Suggestion:
    restaurant = get_restaurant(dish.restaurant) or {}
    return Suggestion(
        **dish.model_dump(),
        reason=reason,
        rating=restaurant.get("rating"),
        is_open=restaurant.get("is_open"),
        delivery_minutes=restaurant.get("delivery_minutes"),
        delivery_fee=restaurant.get("delivery_fee"),
        distance_km=restaurant.get("distance_km"),
    )


def recommend(entities: Entities, limit: int = 3) -> list[Suggestion]:
    dishes = load_menu()

    if entities.budget_max:
        filtered = [dish for dish in dishes if dish.price <= entities.budget_max]
        dishes = filtered if filtered else dishes

    if entities.diet_type:
        filtered = [dish for dish in dishes if entities.diet_type in dish.diet_tags]
        dishes = filtered if filtered else dishes

    if entities.group_size and entities.group_size >= 3:
        filtered = [dish for dish in dishes if dish.shareable]
        dishes = filtered if filtered else dishes

    ranked = sorted(dishes, key=lambda dish: _score(dish, entities), reverse=True)[:limit]
    return [_to_suggestion(dish, _reason(dish, entities)) for dish in ranked]
