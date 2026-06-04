import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    session_id = "e2e-session"

    with TestClient(app) as client:
        config = client.get("/api/config")
        assert_condition(config.status_code == 200, "config endpoint failed")

        menu = client.get("/api/menu")
        assert_condition(menu.status_code == 200, "menu endpoint failed")
        assert_condition(len(menu.json()) >= 20, "menu dataset should have at least 20 dishes")

        chat = client.post(
            "/api/chat",
            json={"message": "Có gì dưới 80k?", "session_id": session_id, "user_context": {}},
        )
        assert_condition(chat.status_code == 200, "chat budget request failed")
        chat_data = chat.json()
        assert_condition(chat_data["intent"] == "BY_BUDGET", "budget intent mismatch")
        assert_condition(len(chat_data["suggestions"]) == 3, "expected 3 suggestions")

        add = client.post(
            "/api/chat",
            json={"message": "Thêm món đầu tiên", "session_id": session_id, "user_context": {}},
        )
        assert_condition(add.status_code == 200, "add-to-cart chat failed")
        add_data = add.json()
        assert_condition(add_data["cart_summary"]["item_count"] >= 1, "cart should have one item")

        cart = client.get(f"/api/cart/{session_id}")
        assert_condition(cart.status_code == 200, "cart endpoint failed")
        cart_data = cart.json()
        assert_condition(cart_data["item_count"] >= 1, "cart item count mismatch")

        first_item = cart_data["items"][0]
        update = client.post(
            "/api/cart/update",
            json={"session_id": session_id, "dish_id": first_item["dish_id"], "delta": 1},
        )
        assert_condition(update.status_code == 200, "cart update failed")
        assert_condition(update.json()["item_count"] >= 2, "cart update did not increase quantity")

        remove = client.post(
            "/api/cart/remove",
            json={"session_id": session_id, "dish_id": first_item["dish_id"]},
        )
        assert_condition(remove.status_code == 200, "cart remove failed")
        assert_condition(
            all(item["dish_id"] != first_item["dish_id"] for item in remove.json()["items"]),
            "cart remove did not remove item",
        )

        direct_pref = client.post(
            "/api/preferences",
            json={"session_id": session_id, "preference_key": "budget", "preference_value": "80000"},
        )
        assert_condition(direct_pref.status_code == 200, "direct preference save failed")
        assert_condition(direct_pref.json()["preferences"]["budget"] == "80000", "direct preference mismatch")

        pref = client.post(
            "/api/chat",
            json={"message": "Nhớ là tôi không cay", "session_id": session_id, "user_context": {}},
        )
        assert_condition(pref.status_code == 200, "save preference failed")
        assert_condition(pref.json()["intent"] == "SAVE_PREFERENCE", "save preference intent mismatch")

        prefs = client.post(
            "/api/chat",
            json={"message": "Bạn nhớ gì về tôi?", "session_id": session_id, "user_context": {}},
        )
        assert_condition(prefs.status_code == 200, "get preferences failed")
        assert_condition("spice" in prefs.json()["reply"], "preference was not stored")

        combo = client.post(
            "/api/chat",
            json={"message": "Gợi ý combo dưới 120k", "session_id": session_id, "user_context": {}},
        )
        assert_condition(combo.status_code == 200, "combo request failed")
        assert_condition(combo.json()["intent"] == "RECOMMEND_COMBO", "combo intent mismatch")

        availability = client.post(
            "/api/chat",
            json={"message": "Phở Hà Nội giao bao lâu?", "session_id": session_id, "user_context": {}},
        )
        assert_condition(availability.status_code == 200, "availability request failed")
        assert_condition("giao khoảng" in availability.json()["reply"], "availability reply mismatch")

        out_of_scope = client.post(
            "/api/chat",
            json={"message": "Viết giúp tôi một bài thơ về mặt trăng", "session_id": session_id, "user_context": {}},
        )
        assert_condition(out_of_scope.status_code == 200, "out-of-scope request failed")
        assert_condition(out_of_scope.json()["action"] == "out_of_scope", "out-of-scope action mismatch")
        assert_condition(out_of_scope.json()["reply"].startswith("Xin lỗi"), "out-of-scope reply must start with Xin lỗi")

    print("E2E API test passed")


if __name__ == "__main__":
    main()
