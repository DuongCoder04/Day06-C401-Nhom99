"""
Yumi Agent Orchestrator — ReAct-style loop.

Flow per request:
  1. classify() — fast rule-based intent detection
  2. collect_context() — run tools in parallel where possible:
       • always: get current weather (if API key available)
       • by intent: search_menu / search_web / check_availability / etc.
  3. generate_reply() — LLM reads tool results and writes a natural reply
  4. fallback to template reply if LLM unavailable
"""

from __future__ import annotations

import concurrent.futures
from typing import Any

from app.ai.classifier import classify_intent
from app.ai.external_tools import get_weather, search_web
from app.ai.llm_client import LLMUnavailable, decide_tool, generate_reply, has_llm_config
from app.ai.recommender import recommend
from app.ai.text import extract_budget, normalize
from app.ai.tools import tool_args_to_entities
from app.data.menu_store import get_restaurant, load_menu
from app.db.sqlite_store import (
    append_history,
    get_history,
    get_last_suggestion_ids,
    get_preferences,
    log_event,
    save_last_suggestions,
    save_preference,
)
from app.models.schemas import ChatRequest, ChatResponse, Classification, Entities, Suggestion
from app.services.cart_service import add_to_cart, get_cart


# ── Constants ─────────────────────────────────────────────────────────────────

OUT_OF_SCOPE_REPLY = (
    "Xin lỗi, Yumi chỉ hỗ trợ các việc liên quan đến đặt đồ ăn: "
    "gợi ý món, tìm theo ngân sách/sức khỏe/thời tiết, kiểm tra quán, thêm món và xem giỏ hàng."
)

_DEFAULT_CITY = "Ho Chi Minh City"


# ── Session helpers ───────────────────────────────────────────────────────────

def _get_last_suggestions(session_id: str) -> list[Suggestion]:
    dish_ids = get_last_suggestion_ids(session_id)
    if not dish_ids:
        return []
    dishes_by_id = {d.id: d for d in load_menu()}
    return [
        Suggestion(**dish.model_dump(), reason=dish.description)
        for dish_id in dish_ids
        if (dish := dishes_by_id.get(dish_id))
    ]


def _save_last_suggestions(session_id: str, suggestions: list[Suggestion]) -> None:
    save_last_suggestions(session_id, [s.id for s in suggestions])


def _remember(session_id: str, role: str, content: str) -> None:
    append_history(session_id, role, content)


def _finalize(session_id: str, response: ChatResponse) -> ChatResponse:
    _remember(session_id, "assistant", response.reply)
    log_event(session_id, "chat_response", {
        "intent": response.intent,
        "action": response.action,
        "suggestion_count": len(response.suggestions),
    })
    return response


# ── Scope check ───────────────────────────────────────────────────────────────

def _is_in_scope(message: str) -> bool:
    text = normalize(message)
    greetings = ["xin chao", "chao", "hello", "hi", "hey", "yumi", "ban la ai"]
    if any(k in text for k in greetings):
        return True

    out_of_scope = [
        "viet tho", "bai tho", "viet code", "code game", "lam bai tap",
        "giai toan", "dich van ban", "tom tat", "ke chuyen", "tu van dau tu",
        "gia vang", "bitcoin", "co phieu", "thoi tiet hom nay", "lich bong da",
        "dat ve may bay", "khach san",
    ]
    if any(k in text for k in out_of_scope):
        return False

    food_signals = [
        "an", "uong", "doi", "bung", "no", "nhe", "mon", "do an", "do uong",
        "com", "pho", "bun", "banh", "salad", "ga", "bo", "lau", "pizza",
        "sushi", "ramen", "tra sua", "sinh to", "chao ga", "goi cuon", "combo",
        "set an", "nhom", "nguoi", "healthy", "giam can", "protein", "chay",
        "mon chay", "khong cay", "di ung", "hai san",
        # drinks & snacks
        "nuoc", "ca phe", "cafe", "tra", "sinh to", "nuoc ep", "nuoc cam",
        "nuoc chanh", "sua", "kem", "bap", "banh trang", "vit", "poke",
    ]
    ordering_signals = [
        "goi y", "chon", "dat", "them", "lay", "gio hang", "gio co gi",
        "don cua toi", "ship", "phi ship", "giao", "may phut", "quan", "mo",
        "dong", "duoi", "ngan sach", "gia", "phu hop", "nhanh", "can gap",
    ]
    memory_signals = ["nho la", "nho rang", "ban nho gi", "nho gi ve toi", "toi thich", "so thich"]

    return (
        any(k in text for k in food_signals)
        or any(k in text for k in ordering_signals)
        or any(k in text for k in memory_signals)
    )


# ── Intent classification ─────────────────────────────────────────────────────

def _classify(request: ChatRequest) -> tuple[Classification, str | None, dict]:
    local = classify_intent(request.message)

    # Always return immediately for high-confidence local intents
    fast_return_intents = {
        "SAVE_PREFERENCE", "GET_PREFERENCES", "CHECK_AVAILABILITY", "RECOMMEND_COMBO",
        "FIND_FOOD", "BY_BUDGET", "BY_DIET", "BY_CONTEXT", "BY_GROUP",
        "VIEW_CART", "ADD_TO_CART", "CHITCHAT",
    }
    if local.intent in fast_return_intents and local.confidence >= 0.9:
        return local, None, {}

    if not has_llm_config():
        return local, None, {}

    try:
        decision = decide_tool(request.message, get_history(request.session_id))
        classification = _classification_from_tool(decision.name, decision.arguments)
        clarification_q = decision.arguments.get("question") if decision.name == "clarify" else None
        return classification, clarification_q, decision.arguments
    except LLMUnavailable:
        return local, None, {}


def _classification_from_tool(name: str, args: dict) -> Classification:
    entities = tool_args_to_entities(args)
    entities.meal_time = args.get("meal_time") or entities.meal_time
    entities.preference_hint = args.get("preference_hint") or entities.preference_hint

    intent_map = {
        "add_to_cart": "ADD_TO_CART",
        "view_cart": "VIEW_CART",
        "save_user_preference": "SAVE_PREFERENCE",
        "get_user_preferences": "GET_PREFERENCES",
        "check_availability": "CHECK_AVAILABILITY",
        "recommend_combo": "RECOMMEND_COMBO",
        "get_weather": "BY_CONTEXT",
        "search_web": "FIND_FOOD",
        "clarify": "FIND_FOOD",
    }
    if name in intent_map:
        confidence = 0.65 if name == "clarify" else 0.95
        return Classification(intent=intent_map[name], confidence=confidence, entities=entities)

    if name == "search_menu":
        if entities.budget_max:
            intent = "BY_BUDGET"
        elif entities.diet_type or entities.preference_hint:
            intent = "BY_DIET"
        elif entities.group_size:
            intent = "BY_GROUP"
        elif entities.weather or entities.meal_time:
            intent = "BY_CONTEXT"
        else:
            intent = "FIND_FOOD"
        return Classification(intent=intent, confidence=0.95, entities=entities)

    return Classification(intent="UNKNOWN", confidence=0.3, entities=Entities())


# ── Context collection (tools execution) ─────────────────────────────────────

def _collect_context(
    request: ChatRequest,
    intent: str,
    entities: Entities,
    tool_args: dict,
) -> dict[str, Any]:
    """
    Run all relevant tools and collect results into a single context dict.
    Uses ThreadPoolExecutor to run weather + menu search in parallel.
    """
    ctx: dict[str, Any] = {
        "intent": intent,
        "user_message": request.message,
        "suggestions": [],
        "weather": {"available": False},
        "web_search": {"available": False},
        "cart": get_cart(request.session_id).model_dump(),
    }

    # Determine if we need weather data
    needs_weather = intent in {"BY_CONTEXT", "FIND_FOOD"} or any(
        token in normalize(request.message)
        for token in ["troi", "mua", "nong", "lanh", "thoi tiet"]
    )

    # Determine if we need web search
    text_norm = normalize(request.message)
    needs_web = any(
        token in text_norm
        for token in [
            "review", "ngon nhat", "dau ngon", "danh gia", "noi tieng",
            "noi nao ngon", "quan nao", "o dau ngon", "quan ngon",
            "goi y quan", "cho biet quan", "quan pho", "quan bun",
        ]
    ) or (intent == "FIND_FOOD" and any(t in text_norm for t in ["ngon", "review", "quan"]))

    # Detect "asking about restaurant" vs "asking about dishes"
    # When asking about a restaurant, we should NOT show irrelevant mock menu items
    from app.data.menu_store import load_restaurants
    restaurants = load_restaurants()
    mentioned_restaurant = any(normalize(name) in text_norm for name in restaurants.keys())

    is_restaurant_query = any(
        token in text_norm
        for token in [
            "quan nao ngon", "quan o dau", "review quan", "noi nao ngon",
            "dia chi", "quan ngon", "goi y quan", "quan pho", "quan bun",
            "quan com", "quan ga", "ten quan", "quan an nao",
            "o dau", "may gio", "mo cua", "dong cua", "review", "danh gia", "thong tin"
        ]
    ) or (needs_web and "quan" in text_norm) or (mentioned_restaurant and any(kw in text_norm for kw in ["o dau", "dia chi", "may gio", "mo cua", "review", "thong tin"]))

    def _fetch_weather() -> dict:
        city = tool_args.get("city", _DEFAULT_CITY)
        return get_weather(city)

    def _fetch_web() -> dict:
        query = tool_args.get("query") or f"{request.message} đồ ăn"
        return search_web(query)

    def _fetch_suggestions() -> list[Suggestion]:
        # Inject real weather into entities if available
        weather_result = ctx.get("weather", {})
        if weather_result.get("available") and not entities.weather:
            entities.weather = weather_result.get("condition")
        if intent in {"FIND_FOOD", "BY_BUDGET", "BY_DIET", "BY_CONTEXT", "BY_GROUP", "RECOMMEND_COMBO"}:
            # Don't fetch mock suggestions if this is a restaurant query (web search will handle it)
            if is_restaurant_query:
                return []

            # Detect if user asks for alternative/different suggestions
            exclude_ids: list[str] = []
            msg_norm = normalize(request.message)
            alt_keywords = ["khac", "doi mon", "thay doi", "khong thich", "mon khac",
                            "khac di", "goi y khac", "tim mon khac", "doi y", "chu khac"]
            if any(k in msg_norm for k in alt_keywords):
                prev = _get_last_suggestions(request.session_id)
                exclude_ids = [s.id for s in prev]

            return recommend(entities, exclude_ids=exclude_ids)
        return []

    # Run weather and web search concurrently if needed
    futures: dict[str, concurrent.futures.Future] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        if needs_weather:
            futures["weather"] = pool.submit(_fetch_weather)
        if needs_web:
            futures["web"] = pool.submit(_fetch_web)

        # Collect weather first (needed for suggestions scoring)
        if "weather" in futures:
            try:
                ctx["weather"] = futures["weather"].result(timeout=6)
                # Inject real weather condition into entities for recommender
                if ctx["weather"].get("available") and not entities.weather:
                    entities.weather = ctx["weather"].get("condition")
            except Exception:
                ctx["weather"] = {"available": False}

        # Now fetch suggestions (uses weather if available)
        suggestions_future = pool.submit(_fetch_suggestions)
        try:
            ctx["suggestions"] = [s.model_dump() for s in suggestions_future.result(timeout=5)]
        except Exception:
            ctx["suggestions"] = []

        # Web search result
        if "web" in futures:
            try:
                ctx["web_search"] = futures["web"].result(timeout=8)
            except Exception:
                ctx["web_search"] = {"available": False}

        # If web search returned a good answer about restaurants, clear mock suggestions
        web_result = ctx.get("web_search", {})
        if web_result.get("available") and web_result.get("answer") and is_restaurant_query:
            ctx["suggestions"] = []

        # Dedup suggestions by dish id
        seen_ids: set[str] = set()
        deduped = []
        for s in ctx.get("suggestions", []):
            dish_id = s.get("id", "")
            if dish_id not in seen_ids:
                seen_ids.add(dish_id)
                deduped.append(s)
        ctx["suggestions"] = deduped

        # Flag for downstream use
        ctx["is_restaurant_query"] = is_restaurant_query

    return ctx


# ── Reply generation ──────────────────────────────────────────────────────────

def _try_llm_reply(
    user_message: str,
    ctx: dict[str, Any],
    history: list[dict[str, str]],
) -> str | None:
    """Attempt LLM-generated reply. Returns None if unavailable."""
    if not has_llm_config():
        return None
    try:
        return generate_reply(user_message, ctx, history)
    except LLMUnavailable:
        return None


def _fallback_reply(intent: str, ctx: dict[str, Any]) -> str:
    """Template fallback when LLM is unavailable."""
    suggestions = ctx.get("suggestions", [])
    top = suggestions[0] if suggestions else None
    weather = ctx.get("weather", {})

    if weather.get("available"):
        weather_note = f" ({weather['summary']})"
    else:
        weather_note = ""

    if not top:
        return "Yumi chưa tìm được món phù hợp. Bạn thử nói rõ hơn ngân sách hoặc khẩu vị nhé."

    if intent == "BY_BUDGET":
        budget = ctx.get("intent_data", {}).get("budget_max")
        budget_str = f"{budget:,}đ" if budget else "ngân sách của bạn"
        return f"Trong {budget_str}, {top['name']} ({top['price']:,}đ) là lựa chọn ổn nhất{weather_note}."

    if intent == "BY_CONTEXT" and weather.get("available"):
        return f"{weather['summary']} Yumi gợi {top['name']} từ {top['restaurant']} — hợp thời tiết hôm nay."

    return f"Yumi gợi {top['name']} từ {top['restaurant']}{weather_note} — cùng 2 lựa chọn khác bên dưới."


# ── Cart helpers ──────────────────────────────────────────────────────────────

def _cart_reply(session_id: str) -> str:
    cart = get_cart(session_id)
    if not cart.items:
        return "Giỏ hàng của bạn đang trống. Bạn muốn Yumi gợi ý món nào không?"
    lines = [f"- {i.name} x{i.quantity} — {i.price * i.quantity:,}đ" for i in cart.items]
    return "Giỏ hàng của bạn:\n" + "\n".join(lines) + f"\nTổng: {cart.total:,}đ"


def _resolve_dish(session_id: str, message: str, dish_ref: str | None) -> Suggestion | None:
    suggestions = _get_last_suggestions(session_id)
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


def _availability_reply(query: str) -> str:
    query_norm = normalize(query)
    matched = next((d for d in load_menu() if normalize(d.name) in query_norm), None)
    restaurant_name = matched.restaurant if matched else None

    if not restaurant_name:
        for dish in load_menu():
            if normalize(dish.restaurant) in query_norm:
                restaurant_name = dish.restaurant
                break

    if not restaurant_name:
        return "Mình chưa tìm thấy quán hoặc món đó trong dataset Yumi."

    restaurant = get_restaurant(restaurant_name)
    if not restaurant:
        return f"Mình có món thuộc {restaurant_name}, nhưng chưa có dữ liệu giao hàng."

    status = "đang mở" if restaurant["is_open"] else "đang đóng"
    return (
        f"{restaurant_name} hiện {status}. "
        f"Rating {restaurant['rating']}/5, giao khoảng {restaurant['delivery_minutes']} phút, "
        f"phí ship {restaurant['delivery_fee']:,}đ."
    )


def _combo_suggestions(budget_max: int | None, group_size: int | None) -> list[Suggestion]:
    dishes = load_menu()
    mains = [d for d in dishes if d.category not in {"drink", "snack"}]
    sides = [d for d in dishes if d.category in {"drink", "snack"} or d.shareable]
    combos: list[Suggestion] = []
    for main in sorted(mains, key=lambda d: d.popularity, reverse=True):
        side = next((s for s in sides if s.id != main.id), None)
        if not side:
            continue
        total = main.price + side.price
        if budget_max and total > budget_max:
            continue
        reason = f"Combo {main.name} + {side.name}, tổng khoảng {total:,}đ"
        if group_size and group_size >= 3:
            reason += f", phù hợp nhóm {group_size} người"
        restaurant = get_restaurant(main.restaurant) or {}
        combos.append(Suggestion(
            **main.model_dump(), reason=reason,
            rating=restaurant.get("rating"), is_open=restaurant.get("is_open"),
            delivery_minutes=restaurant.get("delivery_minutes"),
            delivery_fee=restaurant.get("delivery_fee"),
            distance_km=restaurant.get("distance_km"),
        ))
        if len(combos) == 3:
            break
    return combos


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
    # Avoid / allergy signals → map to "avoid" key
    if "di ung" in text or "khong an" in text or "khong thich" in text:
        food_map = {
            "hai san": "hải sản", "bo ": "bò", "lon ": "lợn",
            "ga ": "gà", "gluten": "gluten", "sua ": "sữa", "trung ": "trứng",
        }
        for raw, label in food_map.items():
            if raw in text:
                return "avoid", label
        return "avoid", message.strip()
    if "giam can" in text or "healthy" in text or "an nhe" in text:
        return "diet", "low_cal"
    if "protein" in text or "tap gym" in text:
        return "diet", "high_protein"
    if "chay" in text:
        return "diet", "vegetarian"
    return "favorite", message.strip()


# ── Main orchestrate ──────────────────────────────────────────────────────────

def orchestrate(request: ChatRequest) -> ChatResponse:
    _remember(request.session_id, "user", request.message)

    # ── Out of scope ──────────────────────────────────────────────────────────
    if not _is_in_scope(request.message):
        response = ChatResponse(
            reply=OUT_OF_SCOPE_REPLY, intent="UNKNOWN", action="out_of_scope",
            suggestions=[], cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    # ── Classify ──────────────────────────────────────────────────────────────
    classification, llm_question, tool_args = _classify(request)
    intent = classification.intent
    entities = classification.entities
    history = get_history(request.session_id)

    if intent == "UNKNOWN":
        response = ChatResponse(
            reply=OUT_OF_SCOPE_REPLY, intent=intent, action="out_of_scope",
            suggestions=[], cart_summary=get_cart(request.session_id),
        )
        return _finalize(request.session_id, response)

    # ── Intents that don't need recommendation ────────────────────────────────

    if intent == "CHITCHAT":
        ctx = {"intent": "CHITCHAT", "user_message": request.message, "suggestions": [],
               "cart": get_cart(request.session_id).model_dump()}
        reply = _try_llm_reply(request.message, ctx, history) or (
            "Mình là Yumi, trợ lý AI giúp bạn chọn món và chuẩn bị giỏ hàng. "
            "Bạn muốn gợi ý theo ngân sách, sức khỏe hay thời tiết hôm nay?"
        )
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="none",
            suggestions=[], cart_summary=get_cart(request.session_id),
        ))

    if intent == "VIEW_CART":
        return _finalize(request.session_id, ChatResponse(
            reply=_cart_reply(request.session_id), intent=intent, action="view_cart",
            suggestions=[], cart_summary=get_cart(request.session_id),
        ))

    if intent == "SAVE_PREFERENCE":
        key, value = _extract_preference(request.message, tool_args)
        save_preference(request.session_id, key, value)
        log_event(request.session_id, "save_preference", {"key": key, "value": value})
        ctx = {"intent": intent, "user_message": request.message, "saved": {key: value},
               "suggestions": [], "cart": get_cart(request.session_id).model_dump()}
        reply = _try_llm_reply(request.message, ctx, history) or (
            f"Yumi đã nhớ: {key} = {value}. Lần sau mình sẽ dùng thông tin này để gợi ý phù hợp hơn."
        )
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="save_preference",
            suggestions=[], cart_summary=get_cart(request.session_id),
        ))

    if intent == "GET_PREFERENCES":
        preferences = get_preferences(request.session_id)
        ctx = {"intent": intent, "user_message": request.message, "preferences": preferences,
               "suggestions": [], "cart": get_cart(request.session_id).model_dump()}
        if not preferences:
            reply = _try_llm_reply(request.message, ctx, history) or "Yumi chưa lưu sở thích nào của bạn."
        else:
            lines = [f"- {k}: {v}" for k, v in preferences.items()]
            ctx["preferences_text"] = "\n".join(lines)
            reply = _try_llm_reply(request.message, ctx, history) or (
                "Yumi đang nhớ:\n" + "\n".join(lines)
            )
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="get_preferences",
            suggestions=[], cart_summary=get_cart(request.session_id),
        ))

    if intent == "CHECK_AVAILABILITY":
        query = tool_args.get("restaurant_or_dish") or request.message
        availability_text = _availability_reply(query)
        ctx = {"intent": intent, "user_message": request.message,
               "availability": availability_text, "suggestions": [],
               "cart": get_cart(request.session_id).model_dump()}
        reply = _try_llm_reply(request.message, ctx, history) or availability_text
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="check_availability",
            suggestions=[], cart_summary=get_cart(request.session_id),
        ))

    if intent == "RECOMMEND_COMBO":
        budget = entities.budget_max or tool_args.get("budget_max")
        group_size = entities.group_size or tool_args.get("group_size")
        suggestions = _combo_suggestions(budget, group_size)
        _save_last_suggestions(request.session_id, suggestions)
        ctx = {"intent": intent, "user_message": request.message,
               "suggestions": [s.model_dump() for s in suggestions],
               "cart": get_cart(request.session_id).model_dump()}
        reply = _try_llm_reply(request.message, ctx, history) or "Yumi gợi ý vài combo dễ đặt từ menu."
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="recommend_combo",
            suggestions=suggestions, cart_summary=get_cart(request.session_id),
        ))

    if intent == "ADD_TO_CART":
        dish = _resolve_dish(request.session_id, request.message, entities.dish_ref)
        if not dish:
            return _finalize(request.session_id, ChatResponse(
                reply='Bạn muốn thêm món nào? Hãy nói "thêm món đầu tiên", "thêm món thứ hai" hoặc bấm nút Thêm trực tiếp trên thẻ món ăn nhé.',
                intent=intent, action="clarify",
                suggestions=_get_last_suggestions(request.session_id),
                cart_summary=get_cart(request.session_id),
                clarification_question=None,
            ))
        cart = add_to_cart(request.session_id, dish.id, entities.quantity)
        log_event(request.session_id, "add_to_cart", {"dish_id": dish.id, "name": dish.name, "quantity": entities.quantity})
        ctx = {"intent": intent, "user_message": request.message, "added_dish": dish.name,
               "cart": cart.model_dump(), "suggestions": []}
        reply = _try_llm_reply(request.message, ctx, history) or (
            f"Đã thêm {dish.name} vào giỏ. Hiện có {cart.item_count} món, tổng {cart.total:,}đ."
        )
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="add_to_cart",
            suggestions=[], cart_summary=cart,
        ))

    # ── Clarification needed ──────────────────────────────────────────────────
    if classification.confidence < 0.85:
        question = llm_question or "Bạn muốn ăn nhẹ hay ăn no bụng?"
        reply = "Yumi chưa rõ ý bạn lắm. Bạn vui lòng làm rõ giúp mình nhé:"
        return _finalize(request.session_id, ChatResponse(
            reply=reply, intent=intent, action="clarify",
            suggestions=[], cart_summary=get_cart(request.session_id),
            clarification_question=question,
        ))

    # ── Main recommendation flow (FIND_FOOD / BY_* intents) ──────────────────
    # Collect all tool results in parallel
    ctx = _collect_context(request, intent, entities, tool_args)

    # Build suggestions list from ctx — deduped and only when relevant
    suggestions_data = ctx.get("suggestions", [])
    suggestions = []
    seen_ids: set[str] = set()
    if suggestions_data and not ctx.get("is_restaurant_query"):
        dishes_by_id = {d.id: d for d in load_menu()}
        for s_dict in suggestions_data:
            dish_id = s_dict.get("id", "")
            if dish_id in seen_ids:
                continue
            seen_ids.add(dish_id)
            dish = dishes_by_id.get(dish_id)
            if dish:
                suggestions.append(Suggestion(
                    **dish.model_dump(),
                    reason=s_dict.get("reason", dish.description),
                    rating=s_dict.get("rating"),
                    is_open=s_dict.get("is_open"),
                    delivery_minutes=s_dict.get("delivery_minutes"),
                    delivery_fee=s_dict.get("delivery_fee"),
                    distance_km=s_dict.get("distance_km"),
                ))

    _save_last_suggestions(request.session_id, suggestions)

    # Generate reply: LLM first, fallback to template
    reply = _try_llm_reply(request.message, ctx, history) or _fallback_reply(intent, ctx)

    return _finalize(request.session_id, ChatResponse(
        reply=reply, intent=intent, action="search",
        suggestions=suggestions, cart_summary=get_cart(request.session_id),
    ))
