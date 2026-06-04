from app.ai.text import extract_budget, extract_group_size, normalize
from app.models.schemas import Classification, Entities


def classify_intent(message: str) -> Classification:
    text = normalize(message)
    entities = Entities()
    entities.budget_max = extract_budget(message)
    entities.group_size = extract_group_size(message)

    if any(token in text for token in ["giam can", "it calo", "healthy", "low cal", "nhe bung", "an nhe", "it dau", "eat clean"]):
        entities.diet_type = "low_cal"
    if any(token in text for token in ["protein", "tap gym", "the hinh"]):
        entities.diet_type = "high_protein"
    if any(token in text for token in ["chay", "vegetarian", "an chay", "mon chay"]):
        entities.diet_type = "vegetarian"
    if any(token in text for token in ["troi mua", "mua", "lanh", "nong", "an khuya", "dem roi", "toi roi"]):
        entities.weather = "rain" if "mua" in text else "cold" if "lanh" in text else "hot"

    if any(token in text for token in ["dau tien", "mon 1", "thu nhat", "first"]):
        entities.dish_ref = "first"
    if any(token in text for token in ["thu 2", "thu hai", "mon 2", "second"]):
        entities.dish_ref = "second"
    if any(token in text for token in ["thu 3", "thu ba", "mon 3", "third"]):
        entities.dish_ref = "third"

    if any(token in text for token in ["gio hang", "xem gio", "tong tien", "cart", "gio co gi", "don cua toi", "toi da chon gi"]):
        return Classification(intent="VIEW_CART", confidence=0.96, entities=entities)
    if any(token in text for token in ["combo", "goi y set", "set an", "mon kem", "dat ca nhom", "ca nhom an gi"]):
        return Classification(intent="RECOMMEND_COMBO", confidence=0.9, entities=entities)
    if any(token in text for token in ["giao nhanh", "duoi 20 phut", "giao duoi", "ship nhanh", "co lien", "can gap", "nhanh nhat", "giao som"]):
        return Classification(intent="BY_CONTEXT", confidence=0.9, entities=entities)
    if any(token in text for token in ["nho rang", "nho la", "toi thich", "toi khong thich", "khong cay", "di ung", "khong hai san", "khong bo"]):
        return Classification(intent="SAVE_PREFERENCE", confidence=0.88, entities=entities)
    if any(token in text for token in ["so thich cua toi", "ban nho gi ve toi", "preference"]):
        return Classification(intent="GET_PREFERENCES", confidence=0.9, entities=entities)
    if any(token in text for token in ["quan co mo", "dang mo", "giao bao lau", "con mo khong", "giao mat bao lau", "may phut", "phi ship"]):
        return Classification(intent="CHECK_AVAILABILITY", confidence=0.86, entities=entities)
    if any(token in text for token in ["them", "lay", "chon", "add"]):
        return Classification(intent="ADD_TO_CART", confidence=0.92, entities=entities)
    if entities.budget_max:
        return Classification(intent="BY_BUDGET", confidence=0.95, entities=entities)
    if entities.diet_type:
        return Classification(intent="BY_DIET", confidence=0.94, entities=entities)
    if entities.group_size:
        return Classification(intent="BY_GROUP", confidence=0.95, entities=entities)
    if entities.weather or any(token in text for token in ["troi", "bua toi", "bua trua", "khuya"]):
        return Classification(intent="BY_CONTEXT", confidence=0.86, entities=entities)
    if any(
        token in text
        for token in [
            "an gi",
            "goi y",
            "mon ngon",
            "doi",
            "doi bung",
            "do an",
            "an no",
            "no bung",
            "bung",
            "reo",
            "chua biet an",
            "khong biet an",
            "co mon nao",
            "chon gi",
            "thom ngon",
            "an tam",
            "lua gi",
        ]
    ):
        confidence = 0.7 if any(token in text for token in ["gi cung duoc", "sao cung duoc"]) else 0.93
        return Classification(intent="FIND_FOOD", confidence=confidence, entities=entities)
    if any(token in text for token in ["yumi", "ban la ai", "cam on", "hello", "hi", "chao"]):
        return Classification(intent="CHITCHAT", confidence=0.9, entities=entities)

    return Classification(intent="UNKNOWN", confidence=0.3, entities=entities)
