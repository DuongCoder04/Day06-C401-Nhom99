import json
from functools import lru_cache

from app.db.sqlite_store import get_dish_rows, get_restaurant_rows, init_db
from app.models.schemas import Dish


def _row_to_dish(row) -> Dish:
    return Dish(
        id=row["id"],
        name=row["name"],
        price=row["price"],
        restaurant=row["restaurant"],
        cuisine=row["cuisine"],
        category=row["category"],
        diet_tags=json.loads(row["diet_tags"]),
        meal_tags=json.loads(row["meal_tags"]),
        is_hot=bool(row["is_hot"]),
        comfort_score=row["comfort_score"],
        shareable=bool(row["shareable"]),
        popularity=row["popularity"],
        image_url=row["image_url"],
        description=row["description"],
    )


@lru_cache
def load_menu() -> list[Dish]:
    init_db()
    return [_row_to_dish(row) for row in get_dish_rows()]


def get_dish(dish_id: str) -> Dish | None:
    return next((dish for dish in load_menu() if dish.id == dish_id), None)


@lru_cache
def load_restaurants() -> dict[str, dict]:
    init_db()
    return {
        row["name"]: {
            "name": row["name"],
            "rating": row["rating"],
            "is_open": bool(row["is_open"]),
            "delivery_minutes": row["delivery_minutes"],
            "delivery_fee": row["delivery_fee"],
            "distance_km": row["distance_km"],
        }
        for row in get_restaurant_rows()
    }


def get_restaurant(name: str) -> dict | None:
    return load_restaurants().get(name)

