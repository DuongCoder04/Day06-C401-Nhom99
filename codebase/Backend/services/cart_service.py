from collections import defaultdict

from models.schemas import CartItem, MenuItem


class CartService:
    def __init__(self) -> None:
        self._carts: dict[str, dict[str, CartItem]] = defaultdict(dict)

    def add_item(self, session_id: str, item: MenuItem, quantity: int = 1) -> tuple[list[CartItem], int]:
        cart = self._carts[session_id]
        existing = cart.get(item.id)

        if existing:
            cart[item.id] = existing.model_copy(update={"quantity": existing.quantity + quantity})
        else:
            cart[item.id] = CartItem(dish_id=item.id, name=item.name, price=item.price, quantity=quantity)

        return self.get_cart(session_id)

    def remove_item(self, session_id: str, dish_id: str) -> tuple[list[CartItem], int]:
        cart = self._carts.get(session_id, {})
        cart.pop(dish_id, None)
        return self.get_cart(session_id)

    def get_cart(self, session_id: str) -> tuple[list[CartItem], int]:
        cart = list(self._carts.get(session_id, {}).values())
        total = sum(item.price * item.quantity for item in cart)
        return cart, total
