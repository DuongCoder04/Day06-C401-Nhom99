from app.data.menu_store import get_dish
from app.db.sqlite_store import add_cart_quantity, get_cart_rows
from app.models.schemas import CartItem, CartResponse


def _to_response(session_id: str) -> CartResponse:
    items: list[CartItem] = []

    for row in get_cart_rows(session_id):
        dish = get_dish(row["dish_id"])
        if not dish:
            continue
        items.append(
            CartItem(
                dish_id=dish.id,
                name=dish.name,
                price=dish.price,
                restaurant=dish.restaurant,
                image_url=dish.image_url,
                quantity=row["quantity"],
            )
        )

    total = sum(item.price * item.quantity for item in items)
    item_count = sum(item.quantity for item in items)
    return CartResponse(items=items, total=total, item_count=item_count)


def get_cart(session_id: str) -> CartResponse:
    return _to_response(session_id)


def add_to_cart(session_id: str, dish_id: str, quantity: int = 1) -> CartResponse:
    if quantity < 1:
        quantity = 1
    if not get_dish(dish_id):
        return get_cart(session_id)

    add_cart_quantity(session_id, dish_id, quantity)
    return _to_response(session_id)


def update_quantity(session_id: str, dish_id: str, delta: int) -> CartResponse:
    if not get_dish(dish_id):
        return _to_response(session_id)

    add_cart_quantity(session_id, dish_id, delta)
    return _to_response(session_id)


def remove_from_cart(session_id: str, dish_id: str) -> CartResponse:
    current = next((row for row in get_cart_rows(session_id) if row["dish_id"] == dish_id), None)
    if current:
        add_cart_quantity(session_id, dish_id, -int(current["quantity"]))
    return _to_response(session_id)
