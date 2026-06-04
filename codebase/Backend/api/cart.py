from fastapi import APIRouter, HTTPException

from models.schemas import CartActionResponse, CartAddRequest, CartRemoveRequest, CartResponse
from services.state import cart_service, menu_service

router = APIRouter()


@router.post("/add", response_model=CartActionResponse)
def add_to_cart(payload: CartAddRequest) -> CartActionResponse:
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be greater than 0")

    item = menu_service.get_by_id(payload.dish_id)
    if item is None:
        raise HTTPException(status_code=404, detail="dish not found")

    items, total = cart_service.add_item(payload.session_id, item, payload.quantity)
    return CartActionResponse(success=True, cart_total=total, item_count=sum(item.quantity for item in items))


@router.get("/{session_id}", response_model=CartResponse)
def get_cart(session_id: str) -> CartResponse:
    items, total = cart_service.get_cart(session_id)
    return CartResponse(items=items, total=total)


@router.delete("/remove", response_model=CartActionResponse)
def remove_from_cart(payload: CartRemoveRequest) -> CartActionResponse:
    items, total = cart_service.remove_item(payload.session_id, payload.dish_id)
    return CartActionResponse(success=True, cart_total=total, item_count=sum(item.quantity for item in items))
