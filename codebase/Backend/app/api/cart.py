from fastapi import APIRouter

from app.models.schemas import AddToCartRequest, CartResponse, RemoveCartRequest, UpdateCartRequest
from app.services.cart_service import add_to_cart, get_cart, remove_from_cart, update_quantity


router = APIRouter(tags=["cart"])


@router.post("/cart/add", response_model=CartResponse)
def add_item(request: AddToCartRequest) -> CartResponse:
    return add_to_cart(request.session_id, request.dish_id, request.quantity)


@router.post("/cart/update", response_model=CartResponse)
def update_item(request: UpdateCartRequest) -> CartResponse:
    return update_quantity(request.session_id, request.dish_id, request.delta)


@router.post("/cart/remove", response_model=CartResponse)
def remove_item(request: RemoveCartRequest) -> CartResponse:
    return remove_from_cart(request.session_id, request.dish_id)


@router.get("/cart/{session_id}", response_model=CartResponse)
def read_cart(session_id: str) -> CartResponse:
    return get_cart(session_id)
