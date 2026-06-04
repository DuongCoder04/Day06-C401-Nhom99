import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[2] / "yumi.db"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dishes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                restaurant TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                category TEXT NOT NULL,
                diet_tags TEXT NOT NULL,
                meal_tags TEXT NOT NULL,
                is_hot INTEGER NOT NULL,
                comfort_score REAL NOT NULL,
                shareable INTEGER NOT NULL,
                popularity REAL NOT NULL,
                image_url TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                name TEXT PRIMARY KEY,
                rating REAL NOT NULL,
                is_open INTEGER NOT NULL,
                delivery_minutes INTEGER NOT NULL,
                delivery_fee INTEGER NOT NULL,
                distance_km REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                session_id TEXT NOT NULL,
                dish_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, dish_id)
            )
            """
        )
        _seed_dishes_if_empty(connection)
        _seed_restaurants_if_empty(connection)


def _seed_dishes_if_empty(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) AS count FROM dishes").fetchone()["count"]
    if count:
        return

    menu_path = DATA_DIR / "menu.json"
    dishes = json.loads(menu_path.read_text(encoding="utf-8"))
    connection.executemany(
        """
        INSERT INTO dishes (
            id, name, price, restaurant, cuisine, category, diet_tags, meal_tags,
            is_hot, comfort_score, shareable, popularity, image_url, description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                dish["id"],
                dish["name"],
                dish["price"],
                dish["restaurant"],
                dish["cuisine"],
                dish["category"],
                json.dumps(dish.get("diet_tags", []), ensure_ascii=False),
                json.dumps(dish.get("meal_tags", []), ensure_ascii=False),
                int(bool(dish.get("is_hot"))),
                dish.get("comfort_score", 0),
                int(bool(dish.get("shareable"))),
                dish.get("popularity", 0),
                dish["image_url"],
                dish["description"],
            )
            for dish in dishes
        ],
    )


def _seed_restaurants_if_empty(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) AS count FROM restaurants").fetchone()["count"]
    if count:
        return

    restaurants_path = DATA_DIR / "restaurants.json"
    restaurants = json.loads(restaurants_path.read_text(encoding="utf-8"))
    connection.executemany(
        """
        INSERT INTO restaurants (
            name, rating, is_open, delivery_minutes, delivery_fee, distance_km
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                restaurant["name"],
                restaurant["rating"],
                int(bool(restaurant["is_open"])),
                restaurant["delivery_minutes"],
                restaurant["delivery_fee"],
                restaurant["distance_km"],
            )
            for restaurant in restaurants
        ],
    )


def get_dish_rows() -> list[sqlite3.Row]:
    with connect() as connection:
        return list(connection.execute("SELECT * FROM dishes ORDER BY id"))


def get_restaurant_rows() -> list[sqlite3.Row]:
    with connect() as connection:
        return list(connection.execute("SELECT * FROM restaurants ORDER BY name"))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                session_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, preference_key)
            )
            """
        )


def add_cart_quantity(session_id: str, dish_id: str, delta: int) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO cart_items (session_id, dish_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id, dish_id)
            DO UPDATE SET
                quantity = quantity + excluded.quantity,
                updated_at = CURRENT_TIMESTAMP
            """,
            (session_id, dish_id, delta),
        )
        connection.execute(
            "DELETE FROM cart_items WHERE session_id = ? AND dish_id = ? AND quantity <= 0",
            (session_id, dish_id),
        )


def get_cart_rows(session_id: str) -> list[sqlite3.Row]:
    with connect() as connection:
        return list(
            connection.execute(
                "SELECT dish_id, quantity FROM cart_items WHERE session_id = ? ORDER BY updated_at",
                (session_id,),
            )
        )


def append_history(session_id: str, role: str, content: str) -> None:
    with connect() as connection:
        connection.execute(
            "INSERT INTO session_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_history(session_id: str, limit: int = 10) -> list[dict[str, str]]:
    with connect() as connection:
        rows = list(
            connection.execute(
                """
                SELECT role, content
                FROM session_history
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
        )
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def log_event(session_id: str, event_type: str, payload: dict[str, Any]) -> None:
    with connect() as connection:
        connection.execute(
            "INSERT INTO user_events (session_id, event_type, payload) VALUES (?, ?, ?)",
            (session_id, event_type, json.dumps(payload, ensure_ascii=False)),
        )


def get_analytics() -> dict[str, Any]:
    with connect() as connection:
        total_user_messages = connection.execute(
            "SELECT COUNT(*) AS count FROM session_history WHERE role = 'user'"
        ).fetchone()["count"]
        total_assistant_messages = connection.execute(
            "SELECT COUNT(*) AS count FROM session_history WHERE role = 'assistant'"
        ).fetchone()["count"]
        add_to_cart_count = connection.execute(
            "SELECT COUNT(*) AS count FROM user_events WHERE event_type = 'add_to_cart'"
        ).fetchone()["count"]
        preference_count = connection.execute(
            "SELECT COUNT(*) AS count FROM user_preferences"
        ).fetchone()["count"]
        cart_item_count = connection.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS count FROM cart_items"
        ).fetchone()["count"]
        event_rows = list(
            connection.execute(
                "SELECT event_type, payload FROM user_events ORDER BY id DESC LIMIT 300"
            )
        )

    intent_counts: dict[str, int] = {}
    out_of_scope_count = 0
    for row in event_rows:
        if row["event_type"] != "chat_response":
            continue
        try:
            payload = json.loads(row["payload"])
        except json.JSONDecodeError:
            continue
        intent = payload.get("intent", "UNKNOWN")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        if payload.get("action") == "out_of_scope":
            out_of_scope_count += 1

    return {
        "total_user_messages": total_user_messages,
        "total_assistant_messages": total_assistant_messages,
        "add_to_cart_count": add_to_cart_count,
        "preference_count": preference_count,
        "cart_item_count": cart_item_count,
        "out_of_scope_count": out_of_scope_count,
        "top_intents": [
            {"intent": intent, "count": count}
            for intent, count in sorted(intent_counts.items(), key=lambda item: item[1], reverse=True)[:6]
        ],
    }


def save_preference(session_id: str, key: str, value: str) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO user_preferences (session_id, preference_key, preference_value)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id, preference_key)
            DO UPDATE SET
                preference_value = excluded.preference_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (session_id, key, value),
        )


def get_preferences(session_id: str) -> dict[str, str]:
    with connect() as connection:
        rows = list(
            connection.execute(
                """
                SELECT preference_key, preference_value
                FROM user_preferences
                WHERE session_id = ?
                ORDER BY updated_at DESC
                """,
                (session_id,),
            )
        )
    return {row["preference_key"]: row["preference_value"] for row in rows}
