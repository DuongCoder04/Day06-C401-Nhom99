import json
from functools import lru_cache

from app.db.sqlite_store import get_dish_rows, get_restaurant_rows
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


# Cache an immutable tuple to prevent callers from accidentally mutating the shared object
@lru_cache
def _load_menu_cached() -> tuple[Dish, ...]:
    return tuple(_row_to_dish(row) for row in get_dish_rows())


# Cache an immutable dict snapshot of restaurants
@lru_cache
def _load_restaurants_cached() -> dict[str, dict]:
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


def load_menu() -> list[Dish]:
    """Return a fresh list backed by the immutable cached tuple."""
    return list(_load_menu_cached())


def load_restaurants() -> dict[str, dict]:
    """Return the cached restaurants dict (read-only usage expected)."""
    return _load_restaurants_cached()


def get_dish(dish_id: str) -> Dish | None:
    return next((dish for dish in _load_menu_cached() if dish.id == dish_id), None)


def get_restaurant(name: str) -> dict | None:
    return _load_restaurants_cached().get(name)


def invalidate_menu_cache() -> None:
    """Clear the in-memory cache so the next call reloads from DB.
    Call this after updating dish/restaurant data at runtime."""
    _load_menu_cached.cache_clear()
    _load_restaurants_cached.cache_clear()
