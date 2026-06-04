import re
from app.ai.text import extract_budget, extract_group_size, normalize
from app.data.menu_store import load_menu
from app.models.schemas import Classification, Entities


def _infer_meal_time_from_text(text: str) -> str | None:
    """
    Only return a meal_time when the user EXPLICITLY mentions a time context.
    No fallback to datetime.now() here — that belongs in the recommender layer
    where it influences scoring without affecting intent classification.
    Uses word-boundary-aware matching to avoid false positives like "tôi" → "toi".
    """
    # Use whole-word patterns to avoid matching "toi" in "tôi" (I/me)
    import re
    if re.search(r'\b(sang|an sang|breakfast|buoi sang)\b', text):
        return "breakfast"
    if re.search(r'\b(trua|an trua|lunch|buoi trua)\b', text):
        return "lunch"
    # "toi nay" / "buoi toi" / "an toi" — must be followed by context, not standalone "toi" (= I/me)
    if re.search(r'\b(toi nay|buoi toi|an toi|dinner)\b', text):
        return "dinner"
    if re.search(r'\b(khuya|dem|late night|an khuya)\b', text):
        return "late_night"
    return None


def classify_intent(message: str) -> Classification:
    text = normalize(message)
    entities = Entities()
    entities.budget_max = extract_budget(message)
    entities.group_size = extract_group_size(message)
    # meal_time is only set when user explicitly mentions a meal/time keyword
    entities.meal_time = _infer_meal_time_from_text(text)

    # Extract dish name or category keyword from the message
    dishes = load_menu()
    matched_dish = None
    for dish in sorted(dishes, key=lambda d: len(d.name), reverse=True):
        if normalize(dish.name) in text:
            matched_dish = dish.name
            break
    if matched_dish:
        entities.dish_name = matched_dish
    else:
        # Check categories and Vietnamese synonyms
        category_map = {
            "com": "rice",
            "pho": "noodle",
            "bun": "noodle",
            "salad": "salad",
            "lau": "hotpot",
            "pizza": "pizza",
            "sushi": "sushi",
            "tra sua": "drink",
            "sinh to": "drink",
            "banh mi": "sandwich",
            "uc ga": "healthy",
        }
        for keyword, cat in category_map.items():
            if keyword in text:
                entities.dish_name = keyword
                break

    # Diet / preference signals
    if any(token in text for token in ["giam can", "it calo", "healthy", "low cal", "nhe bung", "an nhe", "it dau", "eat clean"]):
        entities.diet_type = "low_cal"
        entities.preference_hint = "healthy"
    if any(token in text for token in ["protein", "tap gym", "the hinh"]):
        entities.diet_type = "high_protein"
        entities.preference_hint = "high_protein"
    if any(token in text for token in ["chay", "vegetarian", "an chay", "mon chay"]):
        entities.diet_type = "vegetarian"
        entities.preference_hint = "vegetarian"
    if any(token in text for token in ["no bung", "an no", "chac bung"]):
        entities.preference_hint = "hearty"
    if any(token in text for token in ["nhe bung", "an nhe", "thanh", "de an"]):
        entities.preference_hint = "light"
    if any(token in text for token in ["troi mua", "mua", "lanh", "nong"]):
        entities.weather = "rain" if "mua" in text else "cold" if "lanh" in text else "hot"

    # Explicit delivery/speed context
    if any(token in text for token in ["ship nhanh", "giao nhanh", "giao som", "can gap", "co lien",
                                        "giao som nhat", "can giao", "phi ship", "ship", "giao hang"]):
        # treat as context-aware search if no stronger signal
        entities.preference_hint = entities.preference_hint or "fast_delivery"

    # Dish reference for ADD_TO_CART
    if any(token in text for token in ["dau tien", "mon 1", "thu nhat", "first"]):
        entities.dish_ref = "first"
    if any(token in text for token in ["thu 2", "thu hai", "mon 2", "second"]):
        entities.dish_ref = "second"
    if any(token in text for token in ["thu 3", "thu ba", "mon 3", "third"]):
        entities.dish_ref = "third"

    # ── Intent routing (ordered by specificity) ──────────────────────────────

    if any(token in text for token in ["gio hang", "xem gio", "tong tien", "cart", "gio co gi", "don cua toi", "toi da chon gi"]):
        return Classification(intent="VIEW_CART", confidence=0.96, entities=entities)

    if any(token in text for token in ["nho rang", "nho la", "toi thich", "toi khong thich", "khong cay", "di ung", "khong hai san", "khong bo", "di ung voi"]):
        return Classification(intent="SAVE_PREFERENCE", confidence=0.88, entities=entities)

    if any(token in text for token in ["so thich cua toi", "ban nho gi ve toi", "preference"]):
        return Classification(intent="GET_PREFERENCES", confidence=0.9, entities=entities)

    if any(token in text for token in ["them", "lay", "chon", "add"]):
        return Classification(intent="ADD_TO_CART", confidence=0.92, entities=entities)

    # CHECK_AVAILABILITY — restaurant/delivery queries
    if any(token in text for token in ["giao bao lau", "con mo", "dang mo", "phi ship", "bao nhieu phi",
                                        "ship bao nhieu", "giao bao nhieu", "con hang", "het hang"]):
        return Classification(intent="CHECK_AVAILABILITY", confidence=0.92, entities=entities)

    # RECOMMEND_COMBO — must be before BY_BUDGET to handle "combo dưới 120k"
    if any(token in text for token in ["combo", "set an", "set ", "phan an", "goi y combo", "combo an"]):
        return Classification(intent="RECOMMEND_COMBO", confidence=0.92, entities=entities)

    if entities.budget_max:
        return Classification(intent="BY_BUDGET", confidence=0.95, entities=entities)

    if entities.diet_type:
        return Classification(intent="BY_DIET", confidence=0.9, entities=entities)

    if entities.group_size:
        return Classification(intent="BY_GROUP", confidence=0.95, entities=entities)

    # BY_CONTEXT — explicit weather must be checked FIRST (before FIND_FOOD catch-all)
    if entities.weather:
        return Classification(intent="BY_CONTEXT", confidence=0.92, entities=entities)

    # BY_CONTEXT — delivery speed signals (before FIND_FOOD to avoid falling through)
    if any(token in text for token in ["ship nhanh", "giao nhanh", "giao som", "can gap", "co lien",
                                        "can giao", "giao som nhat", "giao nhanh nhat"]):
        return Classification(intent="BY_CONTEXT", confidence=0.90, entities=entities)

    if entities.dish_name:
        return Classification(intent="FIND_FOOD", confidence=0.9, entities=entities)

    # FIND_FOOD — general hunger/food discovery signals
    # Placed before meal_time/delivery-speed BY_CONTEXT to match "tối nay ăn gì" correctly
    find_food_tokens = [
        "an gi", "goi y", "mon ngon", "doi", "doi bung", "do an", "an no", "no bung", "bung",
        "chua biet an", "khong biet an", "co mon nao", "chon gi", "thom ngon", "lua gi",
        "toi nay an gi", "trua nay an gi", "doi qua", "bung doi", "reo", "an gi ngon",
        "an gi on", "an gi tot",
    ]
    if any(token in text for token in find_food_tokens):
        confidence = 0.68 if any(token in text for token in ["gi cung duoc", "sao cung duoc", "goi y mon di"]) else 0.9
        return Classification(intent="FIND_FOOD", confidence=confidence, entities=entities)

    # BY_CONTEXT — meal time or delivery urgency (after FIND_FOOD to avoid false positives)
    if entities.meal_time:
        return Classification(intent="BY_CONTEXT", confidence=0.87, entities=entities)

    if any(token in text for token in ["ship nhanh", "giao nhanh", "giao som", "can gap", "co lien",
                                        "can giao", "giao som nhat"]):
        return Classification(intent="BY_CONTEXT", confidence=0.90, entities=entities)

    # Preference hints without explicit diet type → still FIND_FOOD (no/light/hearty)
    if entities.preference_hint in {"hearty", "light", "fast_delivery"}:
        return Classification(intent="FIND_FOOD", confidence=0.88, entities=entities)

    # Remaining diet signals
    if entities.preference_hint:
        return Classification(intent="BY_DIET", confidence=0.9, entities=entities)

    has_hi_or_chao = bool(re.search(r'\b(hi|chao)\b', text))
    if any(token in text for token in ["yumi", "ban la ai", "cam on", "hello"]) or has_hi_or_chao:
        return Classification(intent="CHITCHAT", confidence=0.9, entities=entities)

    return Classification(intent="UNKNOWN", confidence=0.3, entities=entities)
