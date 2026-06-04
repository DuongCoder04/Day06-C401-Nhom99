from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest, ChatResponse, Suggestion
from services.state import cart_service, intent_service, menu_service, recommender

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    intent = intent_service.detect(payload.message)
    budget = payload.user_context.budget if payload.user_context else None
    diet = payload.user_context.diet if payload.user_context else None

    if intent == "VIEW_CART":
        items, total = cart_service.get_cart(payload.session_id)
        reply = f"Giỏ hàng của bạn hiện có {len(items)} món, tổng {total}đ."
        suggestions = []
        return ChatResponse(reply=reply, intent=intent, suggestions=suggestions)

    if intent == "ADD_TO_CART":
        items = menu_service.search(query=payload.message, budget=budget, diet=diet)
        if not items:
            return ChatResponse(reply="Mình chưa tìm thấy món phù hợp để thêm. Bạn nói rõ tên món hơn nhé.", intent=intent, suggestions=[])

        added_item = items[0]
        cart_service.add_item(payload.session_id, added_item, 1)
        reply = f"Đã thêm {added_item.name} vào giỏ hàng."
        suggestions = [Suggestion.model_validate(item.model_dump()) for item in items[:3]]
        return ChatResponse(reply=reply, intent=intent, suggestions=suggestions)

    items = recommender.recommend(intent=intent, message=payload.message, budget=budget, diet=diet)
    if not items:
        return ChatResponse(
            reply="Mình chưa tìm thấy món phù hợp. Bạn nói rõ hơn về ngân sách hoặc khẩu vị nhé.",
            intent=intent,
            suggestions=[],
        )

    reply = "Tối nay Yumi gợi ý 3 món này cho bạn 😊"
    suggestions = [Suggestion.model_validate(item.model_dump()) for item in items]
    return ChatResponse(reply=reply, intent=intent, suggestions=suggestions)
