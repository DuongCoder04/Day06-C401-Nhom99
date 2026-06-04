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


def _score(dish: Dish, entities: Entities) -> float:
    score = dish.popularity * 40
    meal = _meal_time()

    if meal in dish.meal_tags:
        score += 16
    if entities.budget_max and dish.price <= entities.budget_max:
        score += 35
    if entities.budget_max and dish.price > entities.budget_max:
        score -= 80
    if entities.diet_type and entities.diet_type in dish.diet_tags:
        score += 45
    if entities.diet_type and entities.diet_type not in dish.diet_tags:
        score -= 35
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
    if entities.budget_max:
        return f"{dish.name} nằm trong ngân sách và có giá {dish.price:,}đ."
    if entities.diet_type == "low_cal":
        return f"{dish.name} nhẹ bụng, hợp khi bạn muốn ăn lành mạnh."
    if entities.diet_type == "high_protein":
        return f"{dish.name} giàu đạm, hợp cho bữa ăn chắc bụng."
    if entities.group_size:
        return f"{dish.name} phù hợp khi đặt cho nhóm {entities.group_size} người."
    if entities.weather in {"rain", "cold"}:
        return f"{dish.name} là món nóng, hợp lúc trời mưa hoặc se lạnh."
    restaurant = get_restaurant(dish.restaurant)
    if restaurant and restaurant["delivery_minutes"] <= 20:
        return f"{dish.name} từ quán đang mở, giao khoảng {restaurant['delivery_minutes']} phút."
    return f"{dish.name} phổ biến, dễ ăn và giúp bạn quyết định nhanh."


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
