from app.ai.classifier import classify_intent
from app.ai.llm_client import LLMUnavailable, decide_tool, has_llm_config
from app.ai.recommender import recommend
from app.ai.text import extract_budget, normalize
from app.ai.tools import tool_args_to_entities
from app.data.menu_store import get_restaurant, load_menu
from app.db.sqlite_store import append_history, get_history, get_preferences, log_event, save_preference
from app.models.schemas import ChatRequest, ChatResponse, Classification, Entities, Suggestion
from app.services.cart_service import add_to_cart, get_cart


last_suggestions: dict[str, list[Suggestion]] = {}


OUT_OF_SCOPE_REPLY = (
    "Xin lỗi, Yumi chỉ hỗ trợ các việc liên quan đến đặt đồ ăn trong bản demo này: "
    "gợi ý món, tìm theo ngân sách/sức khỏe/bối cảnh, kiểm tra quán, thêm món và xem giỏ hàng."
)


def _is_in_scope(message: str) -> bool:
    text = normalize(message)
    greeting_keywords = ["xin chao", "chao", "hello", "hi", "hey", "yumi", "ban la ai"]
    if any(keyword in text for keyword in greeting_keywords):
        return True

    explicit_out_of_scope = [
        "viet tho",
        "bai tho",
        "viet code",
        "code game",
        "lam bai tap",
        "giai toan",
        "dich van ban",
        "tom tat",
        "ke chuyen",
        "tu van dau tu",
        "gia vang",
        "bitcoin",
        "co phieu",
        "thoi tiet hom nay",
        "lich bong da",
        "dat ve may bay",
        "khach san",
    ]
    if any(keyword in text for keyword in explicit_out_of_scope):
        return False

    food_signals = [
        "an",
        "uong",
        "doi",
        "bung",
        "no",
        "nhe",
        "mon",
        "do an",
        "do uong",
        "com",
        "pho",
        "bun",
        "banh",
        "salad",
        "ga",
        "bo",
        "lau",
        "pizza",
        "sushi",
        "ramen",
        "tra sua",
        "sinh to",
        "chao ga",
        "goi cuon",
        "combo",
        "set an",
        "nhom",
        "nguoi",
        "healthy",
        "giam can",
        "protein",
        "chay",
        "mon chay",
        "khong cay",
        "di ung",
        "hai san",
    ]
    ordering_signals = [
        "goi y",
        "chon",
        "dat",
        "them",
        "lay",
        "gio hang",
        "gio co gi",
        "don cua toi",
        "ship",
        "phi ship",
        "giao",
        "may phut",
        "quan",
        "mo",
        "dong",
        "duoi",
        "ngan sach",
        "gia",
        "phu hop",
        "nhanh",
        "can gap",
    ]
    memory_signals = ["nho la", "nho rang", "ban nho gi", "nho gi ve toi", "toi thich", "khong thich", "so thich"]

    has_food_signal = any(keyword in text for keyword in food_signals)
    has_ordering_signal = any(keyword in text for keyword in ordering_signals)
    has_memory_signal = any(keyword in text for keyword in memory_signals)

    return has_food_signal or has_ordering_signal or has_memory_signal


def _cart_reply(session_id: str) -> str:
    cart = get_cart(session_id)
    if not cart.items:
        return "Giỏ hàng của bạn đang trống. Bạn muốn Yumi gợi ý món nào không?"

    lines = [f"- {item.name} x{item.quantity} - {item.price * item.quantity:,}đ" for item in cart.items]
    return "Giỏ hàng của bạn:\n" + "\n".join(lines) + f"\nTổng: {cart.total:,}đ"


def _resolve_dish(session_id: str, message: str, dish_ref: str | None) -> Suggestion | None:
    suggestions = last_suggestions.get(session_id, [])
    ref_map = {"first": 0, "second": 1, "third": 2}

    if dish_ref in ref_map and len(suggestions) > ref_map[dish_ref]:
        return suggestions[ref_map[dish_ref]]

    message_norm = normalize(message)
    for dish in suggestions:
        if normalize(dish.name) in message_norm:
            return dish

    for dish in load_menu():
        if normalize(dish.name) in message_norm:
            return Suggestion(**dish.model_dump(), reason=dish.description)

    return None


def _suggestion_reply(intent: str, suggestions: list[Suggestion], budget: int | None, group_size: int | None) -> str:
    if not suggestions:
        return "Yumi chưa tìm thấy món phù hợp trong menu mẫu. Bạn muốn đổi tiêu chí không?"
    if intent == "BY_BUDGET" and budget:
        return f"Có {len(suggestions)} món trong ngân sách {budget:,}đ. Yumi chọn các món dễ quyết định nhất cho bạn."
    if intent == "BY_DIET":
        return f"Yumi tìm được {len(suggestions)} món hợp mục tiêu ăn uống của bạn."
    if intent == "BY_GROUP" and group_size:
        return f"Cho nhóm {group_size} người, Yumi ưu tiên món dễ chia sẻ."
    if intent == "BY_CONTEXT":
        return "Dựa trên bối cảnh bạn nói, Yumi gợi ý các món này."
    return "Yumi gợi ý 3 món dễ chọn nhất lúc này."


def _discovery_reply(message: str, intent: str, suggestions: list[Suggestion], budget: int | None, group_size: int | None) -> str:
    text = normalize(message)
    if intent == "FIND_FOOD" and any(token in text for token in ["doi", "doi bung", "an no", "no bung"]):
        return "Bạn đang đói rồi thì Yumi ưu tiên món no bụng, quán đang mở và giao nhanh nhất cho bạn."
    if intent == "FIND_FOOD" and any(token in text for token in ["chua biet an", "khong biet an", "chon gi"]):
        return "Bạn chưa biết chọn gì thì Yumi rút gọn còn 3 món dễ quyết định nhất, ưu tiên quán đang mở và món phổ biến."
    if intent == "FIND_FOOD" and any(token in text for token in ["gi cung duoc", "sao cung duoc"]):
        return "Nếu bạn ăn gì cũng được, Yumi sẽ chọn các món an toàn: dễ ăn, giao nhanh và giá hợp lý."
    if intent == "FIND_FOOD":
        return "Yumi chọn nhanh 3 món đáng cân nhắc nhất từ menu thật, có tính cả quán đang mở và tốc độ giao."
    if intent == "BY_BUDGET" and budget:
        return f"Với ngân sách khoảng {budget:,}đ, Yumi lọc các món vừa túi tiền nhưng vẫn đủ no và dễ đặt."
    if intent == "BY_DIET" and any(token in text for token in ["giam can", "healthy", "eat clean", "nhe bung", "an nhe"]):
        return "Bạn muốn ăn nhẹ/lành mạnh, nên Yumi ưu tiên món ít nặng bụng và có tag healthy trong menu."
    if intent == "BY_DIET":
        return "Yumi lọc các món phù hợp mục tiêu ăn uống của bạn và tránh gợi ý quá rộng."
    if intent == "BY_CONTEXT" and any(token in text for token in ["mua", "lanh"]):
        return "Trời mưa/lạnh thì Yumi ưu tiên món nóng, comfort food và quán còn mở."
    if intent == "BY_CONTEXT" and any(token in text for token in ["giao nhanh", "ship nhanh", "co lien", "can gap"]):
        return "Bạn cần nhanh, nên Yumi ưu tiên quán đang mở và thời gian giao ngắn."
    if intent == "BY_CONTEXT" and any(token in text for token in ["khuya", "dem roi"]):
        return "Ăn khuya thì Yumi ưu tiên món ấm bụng, dễ ăn và không quá nặng."
    if intent == "BY_GROUP" and group_size:
        return f"Cho nhóm {group_size} người, Yumi ưu tiên món dễ chia sẻ hoặc combo để đặt nhanh hơn."
    return _suggestion_reply(intent, suggestions, budget, group_size)


def _classification_from_tool(name: str, args: dict) -> Classification:
    entities = tool_args_to_entities(args)
    if name == "search_menu":
        if entities.budget_max:
            intent = "BY_BUDGET"
        elif entities.diet_type:
            intent = "BY_DIET"
        elif entities.group_size:
            intent = "BY_GROUP"
        elif entities.weather:
            intent = "BY_CONTEXT"
        else:
            intent = "FIND_FOOD"
        return Classification(intent=intent, confidence=0.95, entities=entities)
    if name == "add_to_cart":
        return Classification(intent="ADD_TO_CART", confidence=0.95, entities=entities)
    if name == "view_cart":
        return Classification(intent="VIEW_CART", confidence=0.95, entities=entities)
    if name == "clarify":
        return Classification(intent="FIND_FOOD", confidence=0.65, entities=entities)
    if name == "save_user_preference":
        return Classification(intent="SAVE_PREFERENCE", confidence=0.95, entities=entities)
    if name == "get_user_preferences":
        return Classification(intent="GET_PREFERENCES", confidence=0.95, entities=entities)
    if name == "check_availability":
        return Classification(intent="CHECK_AVAILABILITY", confidence=0.95, entities=entities)
    if name == "recommend_combo":
        return Classification(intent="RECOMMEND_COMBO", confidence=0.95, entities=entities)
    return Classification(intent="UNKNOWN", confidence=0.3, entities=Entities())


def _classify(request: ChatRequest) -> tuple[Classification, str | None, dict]:
    local_classification = classify_intent(request.message)
    if local_classification.intent in {
        "SAVE_PREFERENCE",
        "GET_PREFERENCES",
        "CHECK_AVAILABILITY",
        "RECOMMEND_COMBO",
    }:
        return local_classification, None, {}
    if local_classification.intent in {
        "FIND_FOOD",
        "BY_BUDGET",
        "BY_DIET",
        "BY_CONTEXT",
        "BY_GROUP",
        "VIEW_CART",
        "ADD_TO_CART",
        "CHITCHAT",
    } and local_classification.confidence >= 0.9:
        return local_classification, None, {}

    if not has_llm_config():
        return local_classification, None, {}

    try:
        decision = decide_tool(request.message, get_history(request.session_id))
        classification = _classification_from_tool(decision.name, decision.arguments)
        clarification_question = decision.arguments.get("question") if decision.name == "clarify" else None
        return classification, clarification_question, decision.arguments
    except LLMUnavailable:
        return local_classification, None, {}


def _remember(session_id: str, role: str, content: str) -> None:
    append_history(session_id, role, content)


def _finalize(session_id: str, response: ChatResponse) -> ChatResponse:
    _remember(session_id, "assistant", response.reply)
    log_event(
        session_id,
        "chat_response",
        {"intent": response.intent, "action": response.action, "suggestion_count": len(response.suggestions)},
    )
    return response


def _extract_preference(message: str, tool_args: dict) -> tuple[str, str]:
    key = tool_args.get("preference_key")
    value = tool_args.get("preference_value")
    if key and value:
        return str(key), str(value)

    text = normalize(message)
    budget = extract_budget(message)
    if budget:
        return "budget", str(budget)
    if "khong cay" in text:
        return "spice", "không cay"
    if "giam can" in text or "healthy" in text:
        return "diet", "low_cal"
    if "nhat" in text:
        return "cuisine", "japanese"
    if "han" in text:
        return "cuisine", "korean"
    if "chay" in text:
        return "diet", "vegetarian"
    return "favorite", message.strip()


def _availability_reply(query: str) -> str:
    query_norm = normalize(query)
    matched_dish = next((dish for dish in load_menu() if normalize(dish.name) in query_norm), None)
    restaurant_name = matched_dish.restaurant if matched_dish else None

    if not restaurant_name:
        for dish in load_menu():
            if normalize(dish.restaurant) in query_norm:
                restaurant_name = dish.restaurant
                break

    if not restaurant_name:
        return "Mình chưa tìm thấy quán hoặc món đó trong dataset Yumi."

    restaurant = get_restaurant(restaurant_name)
    if not restaurant:
        return f"Mình có món thuộc {restaurant_name}, nhưng chưa có dữ liệu giao hàng của quán này."

    status = "đang mở" if restaurant["is_open"] else "đang đóng"
    return (
        f"{restaurant_name} hiện {status}. "
        f"Rating {restaurant['rating']}/5, giao khoảng {restaurant['delivery_minutes']} phút, "
        f"phí ship {restaurant['delivery_fee']:,}đ."
    )


def _combo_suggestions(budget_max: int | None, group_size: int | None) -> list[Suggestion]:
    dishes = load_menu()
    mains = [dish for dish in dishes if dish.category not in {"drink", "snack"}]
    sides = [dish for dish in dishes if dish.category in {"drink", "snack"} or dish.shareable]
    combos: list[Suggestion] = []

    for main in sorted(mains, key=lambda item: item.popularity, reverse=True):
        side = next((item for item in sides if item.id != main.id), None)
        if not side:
            continue
        total = main.price + side.price
        if budget_max and total > budget_max:
            continue
        reason = f"Combo {main.name} + {side.name}, tổng khoảng {total:,}đ"
        if group_size and group_size >= 3:
            reason += f", phù hợp nhóm {group_size} người"
        restaurant = get_restaurant(main.restaurant) or {}
        combos.append(
            Suggestion(
                **main.model_dump(),
                reason=reason,
                rating=restaurant.get("rating"),
                is_open=restaurant.get("is_open"),
                delivery_minutes=restaurant.get("delivery_minutes"),
                delivery_fee=restaurant.get("delivery_fee"),
                distance_km=restaurant.get("distance_km"),
            )
        )
        if len(combos) == 3:
            break

    return combos


def orchestrate(request: ChatRequest) -> ChatResponse:
    _remember(request.session_id, "user", request.message)

    if not _is_in_scope(request.message):
        response = ChatResponse(
            reply=OUT_OF_SCOPE_REPLY,
            intent="UNKNOWN",
            action="out_of_scope",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    classification, llm_question, tool_args = _classify(request)
    intent = classification.intent
    entities = classification.entities

    if intent == "UNKNOWN":
        response = ChatResponse(
            reply=OUT_OF_SCOPE_REPLY,
            intent=intent,
            action="out_of_scope",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "CHITCHAT":
        response = ChatResponse(
            reply="Mình là Yumi, trợ lý AI giúp bạn chọn món và chuẩn bị giỏ hàng. Bạn muốn gợi ý theo ngân sách, sức khỏe hay bối cảnh hôm nay?",
            intent=intent,
            action="none",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "VIEW_CART":
        response = ChatResponse(
            reply=_cart_reply(request.session_id),
            intent=intent,
            action="view_cart",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "SAVE_PREFERENCE":
        key, value = _extract_preference(request.message, tool_args)
        save_preference(request.session_id, key, value)
        log_event(request.session_id, "save_preference", {"key": key, "value": value})
        response = ChatResponse(
            reply=f"Yumi đã nhớ: {key} = {value}. Lần sau mình sẽ dùng thông tin này để gợi ý món phù hợp hơn.",
            intent=intent,
            action="save_preference",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "GET_PREFERENCES":
        preferences = get_preferences(request.session_id)
        if not preferences:
            reply = "Yumi chưa lưu sở thích nào của bạn trong phiên này."
        else:
            lines = [f"- {key}: {value}" for key, value in preferences.items()]
            reply = "Yumi đang nhớ các sở thích này:\n" + "\n".join(lines)
        response = ChatResponse(
            reply=reply,
            intent=intent,
            action="get_preferences",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "CHECK_AVAILABILITY":
        query = tool_args.get("restaurant_or_dish") or request.message
        response = ChatResponse(
            reply=_availability_reply(query),
            intent=intent,
            action="check_availability",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "RECOMMEND_COMBO":
        budget = entities.budget_max or tool_args.get("budget_max")
        group_size = entities.group_size or tool_args.get("group_size")
        suggestions = _combo_suggestions(budget, group_size)
        last_suggestions[request.session_id] = suggestions
        response = ChatResponse(
            reply="Yumi gợi ý vài combo dễ đặt từ menu thật.",
            intent=intent,
            action="recommend_combo",
            suggestions=suggestions,
            cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    if intent == "ADD_TO_CART":
        dish = _resolve_dish(request.session_id, request.message, entities.dish_ref)
        if not dish:
            response = ChatResponse(
                reply="Bạn muốn thêm món nào? Hãy nói “thêm món đầu tiên”, “thêm món thứ hai” hoặc bấm nút Thêm trên card.",
                intent=intent,
                action="clarify",
                suggestions=last_suggestions.get(request.session_id, []),
                cart_summary=get_cart(request.session_id),
                clarification_question="Bạn muốn thêm món nào?",
            )
            return _finalize(request.session_id, response)

        cart = add_to_cart(request.session_id, dish.id, entities.quantity)
        log_event(
            request.session_id,
            "add_to_cart",
            {"dish_id": dish.id, "name": dish.name, "quantity": entities.quantity},
        )
        response = ChatResponse(
            reply=f"Đã thêm {dish.name} vào giỏ. Hiện giỏ hàng có {cart.item_count} món, tổng {cart.total:,}đ.",
            intent=intent,
            action="add_to_cart",
            suggestions=[],
            cart_summary=cart,
        )
        return _finalize(request.session_id, response)

    if classification.confidence < 0.85:
        question = llm_question or "Bạn muốn ăn nhẹ hay ăn no bụng?"
        response = ChatResponse(
            reply=question,
            intent=intent,
            action="clarify",
            suggestions=[],
            cart_summary=get_cart(request.session_id),
            clarification_question=question,
        )
        return _finalize(request.session_id, response)

    suggestions = recommend(entities)
    last_suggestions[request.session_id] = suggestions
    response = ChatResponse(
        reply=_discovery_reply(request.message, intent, suggestions, entities.budget_max, entities.group_size),
        intent=intent,
        action="search",
        suggestions=suggestions,
        cart_summary=get_cart(request.session_id),
    )
    return _finalize(request.session_id, response)
