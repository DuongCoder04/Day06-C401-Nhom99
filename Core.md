# Yumi — AI Core Design

> Tài liệu kỹ thuật chi tiết về lớp AI của Yumi: system prompt, intent classification, tool calling, recommendation, memory và toàn bộ conversation flow.

---

## Mục lục

1. [Tổng quan kiến trúc AI](#1-tổng-quan-kiến-trúc-ai)
2. [System Prompt](#2-system-prompt)
3. [Intent Classification](#3-intent-classification)
4. [Entity Extraction](#4-entity-extraction)
5. [Tool Definitions](#5-tool-definitions)
6. [Recommendation Engine](#6-recommendation-engine)
7. [Memory & Context](#7-memory--context)
8. [Conversation Flow](#8-conversation-flow)
9. [Orchestrator Pipeline](#9-orchestrator-pipeline)
10. [Xử lý lỗi & Edge Cases](#10-xử-lý-lỗi--edge-cases)
11. [Code mẫu](#11-code-mẫu)

---

## 1. Tổng quan kiến trúc AI

Yumi không phải một chatbot đơn giản gọi LLM rồi trả về text. Đây là một **AI Agent** với pipeline nhiều tầng:

```
User Message
    │
    ▼
┌─────────────────────────────────────────────┐
│              AI Orchestrator                 │
│                                             │
│  1. Intent Classifier   → intent + entities │
│  2. Context Loader      → user profile,     │
│                            session history  │
│  3. Tool Router         → quyết định tool   │
│     ├── search_menu()                       │
│     ├── add_to_cart()                       │
│     └── view_cart()                         │
│  4. Recommendation Engine → top 3 dishes    │
│  5. Response Generator  → text + cards      │
└─────────────────────────────────────────────┘
    │
    ▼
AI Reply + Suggestion Cards
```

**Nguyên tắc thiết kế:**
- LLM chịu trách nhiệm hiểu ngôn ngữ tự nhiên và sinh text
- Code Python chịu trách nhiệm logic nghiệp vụ (filter, rank, cart)
- Không để LLM tự bịa dữ liệu — mọi món ăn phải từ `menu.json`

---

## 2. System Prompt

System prompt là nền tảng định hình toàn bộ hành vi của Yumi. Gồm 4 phần: Persona, Context, Rules, Output Format.

```
SYSTEM PROMPT — YUMI v1.0
=========================

## Persona
Bạn là Yumi, trợ lý đặt đồ ăn thông minh và thân thiện.
Bạn nói tiếng Việt, giọng trẻ trung, gần gũi, dùng "bạn/mình".
Bạn hiểu người dùng đang đói và cần quyết định nhanh — đừng hỏi quá nhiều.

## Nhiệm vụ
Giúp người dùng tìm món ăn phù hợp dựa trên nhu cầu của họ,
sau đó hỗ trợ thêm vào giỏ hàng.

## Context hiện tại (inject động)
- Thời gian: {current_time}
- Ngân sách user: {user_budget} VND
- Khẩu vị yêu thích: {user_preferences}
- Lịch sử gần đây: {recent_orders}
- Giỏ hàng hiện tại: {cart_summary}

## Rules — PHẢI tuân thủ
1. CHỈ gợi ý món có trong danh sách menu được cung cấp. KHÔNG được bịa tên món, giá, hay nhà hàng.
2. Tối đa 3 gợi ý mỗi lần. Nhiều hơn gây rối.
3. Khi không rõ nhu cầu → hỏi ĐỘC NHẤT 1 câu làm rõ. Không hỏi nhiều câu cùng lúc.
4. Khi người dùng chọn món → xác nhận trước khi thêm vào giỏ.
5. Luôn kết thúc reply bằng một câu action gợi ý tiếp theo.
6. Không nói về chính sách, không nhận xét về đối thủ cạnh tranh.
7. Giữ reply ngắn: tối đa 3-4 câu text + suggestion cards.

## Output Format
Trả về JSON với cấu trúc sau:

{
  "reply": "Tin nhắn text hiển thị cho user",
  "intent": "INTENT_NAME",
  "action": "none | search | add_to_cart | view_cart | clarify",
  "suggestions": [
    {
      "dish_id": "id của món từ menu",
      "reason": "Lý do ngắn tại sao phù hợp (1 câu)"
    }
  ],
  "clarification_question": "Câu hỏi làm rõ nếu action = clarify"
}
```

### Vì sao output là JSON?

LLM trả JSON thay vì plain text giúp backend:
- Parse `intent` để log và analytics
- Parse `suggestions` để lookup chi tiết món từ `menu.json`
- Parse `action` để biết cần gọi tool nào tiếp theo
- FE render đúng UI (text bubble vs suggestion cards)

---

## 3. Intent Classification

### 3.1 Danh sách intents

| Intent | Mô tả | Ví dụ câu |
|--------|-------|-----------|
| `FIND_FOOD` | Tìm món ăn chung chung | "Ăn gì giờ?", "Gợi ý món ngon" |
| `BY_BUDGET` | Có ràng buộc ngân sách | "Có gì dưới 80k?", "Ngân sách 50k" |
| `BY_DIET` | Theo chế độ ăn / sức khỏe | "Đang giảm cân", "Món low carb", "High protein" |
| `BY_CONTEXT` | Theo thời tiết / bối cảnh | "Trời mưa", "Ăn khuya", "Trời lạnh" |
| `BY_GROUP` | Đặt cho nhiều người | "Đặt cho 4 người", "Ăn cùng bạn bè" |
| `ADD_TO_CART` | Thêm món vào giỏ | "Thêm món đầu tiên", "Lấy cái đó" |
| `VIEW_CART` | Xem giỏ hàng | "Giỏ hàng của tôi", "Xem lại đơn" |
| `MODIFY_CART` | Sửa giỏ hàng | "Bỏ phở ra", "Thêm 1 phần nữa" |
| `CLARIFY` | Yumi cần hỏi lại | (auto — khi confidence thấp) |
| `CHITCHAT` | Hội thoại ngoài lề | "Yumi là ai?", "Cảm ơn nhé" |

### 3.2 Intent Classification Prompt

Đây là prompt riêng dùng để classify — **tách biệt hoàn toàn** với system prompt chính:

```
INTENT CLASSIFICATION PROMPT
=============================

Phân loại tin nhắn sau vào một trong các intent:
FIND_FOOD | BY_BUDGET | BY_DIET | BY_CONTEXT | BY_GROUP | ADD_TO_CART | VIEW_CART | MODIFY_CART | CHITCHAT

Tin nhắn: "{user_message}"
Lịch sử hội thoại gần nhất: {last_3_turns}

Trả về JSON:
{
  "intent": "INTENT_NAME",
  "confidence": 0.0-1.0,
  "entities": {
    "budget_max": null hoặc số (VND),
    "diet_type": null hoặc "low_carb|high_protein|vegetarian|low_cal",
    "weather": null hoặc "rain|cold|hot",
    "group_size": null hoặc số,
    "dish_ref": null hoặc "first|second|third|tên món",
    "quantity": null hoặc số
  }
}

Chỉ trả JSON, không giải thích.
```

### 3.3 Confidence routing

```python
if confidence >= 0.85:
    # Route thẳng theo intent
    route_to_handler(intent, entities)
elif confidence >= 0.60:
    # Hỏi làm rõ 1 câu
    ask_clarification(intent, entities)
else:
    # Fallback thân thiện
    return friendly_fallback()
```

---

## 4. Entity Extraction

Entities là các thông tin có cấu trúc được trích xuất từ câu của user.

### 4.1 Entity schema

```python
class Entities:
    budget_max: int | None        # VD: 80000 (VND)
    budget_min: int | None        # VD: 30000
    diet_type: str | None         # "low_carb" | "high_protein" | "vegetarian" | "low_cal"
    weather: str | None           # "rain" | "cold" | "hot"
    group_size: int | None        # 2, 4, 6...
    cuisine: str | None           # "vietnamese" | "japanese" | "korean"...
    dish_ref: str | None          # "first" | "second" | "phở bò"
    quantity: int | None          # 1, 2...
    time_context: str | None      # "breakfast" | "lunch" | "dinner" | "late_night"
```

### 4.2 Ví dụ extraction

| Câu user | Entities extracted |
|----------|--------------------|
| "Có gì dưới 80k?" | `budget_max: 80000` |
| "Tôi đang giảm cân" | `diet_type: "low_cal"` |
| "Trời lạnh muốn ăn nóng" | `weather: "cold"` |
| "Đặt cho 4 người" | `group_size: 4` |
| "Thêm món thứ 2" | `dish_ref: "second", quantity: 1` |
| "80k, không cay, giao nhanh" | `budget_max: 80000` + context note |

### 4.3 Merge với user context

Entities từ câu mới được **merge** với context từ session, không replace hoàn toàn:

```python
def merge_context(session_context: dict, new_entities: dict) -> dict:
    # Entities mới override entities cũ
    # User profile (budget, diet) làm default nếu không có entities mới
    merged = {**session_context["user_profile"], **session_context["current_entities"]}
    for key, value in new_entities.items():
        if value is not None:
            merged[key] = value
    return merged
```

---

## 5. Tool Definitions

Tools là các hàm Python mà AI Orchestrator gọi dựa trên intent. Đây là cách Yumi thực hiện hành động thực tế (không phải chỉ nói).

### 5.1 Tool: `search_menu`

**Khi nào gọi:** Intent là `FIND_FOOD`, `BY_BUDGET`, `BY_DIET`, `BY_CONTEXT`, `BY_GROUP`

```python
def search_menu(
    budget_max: int | None = None,
    diet_type: str | None = None,
    cuisine: str | None = None,
    weather: str | None = None,
    group_size: int | None = None,
    limit: int = 10
) -> list[dict]:
    """
    Filter món từ menu.json theo các tiêu chí.
    Trả về top N candidates để Recommendation Engine xếp hạng.
    """
    dishes = load_menu()  # đọc menu.json

    # Filter theo budget
    if budget_max:
        dishes = [d for d in dishes if d["price"] <= budget_max]

    # Filter theo diet
    if diet_type:
        dishes = [d for d in dishes if diet_type in d.get("diet_tags", [])]

    # Filter theo cuisine
    if cuisine:
        dishes = [d for d in dishes if d.get("cuisine") == cuisine]

    # Filter theo weather context
    if weather == "cold":
        # Ưu tiên món nóng
        dishes = sorted(dishes, key=lambda d: d.get("is_hot", False), reverse=True)
    elif weather == "rain":
        # Ưu tiên món comfort food
        dishes = sorted(dishes, key=lambda d: d.get("comfort_score", 0), reverse=True)

    # Filter theo group size
    if group_size and group_size >= 3:
        # Ưu tiên món có thể share
        dishes = [d for d in dishes if d.get("shareable", False)] or dishes

    return dishes[:limit]
```

**OpenAI function schema:**
```json
{
  "name": "search_menu",
  "description": "Tìm kiếm món ăn trong menu theo các tiêu chí: ngân sách, chế độ ăn, thời tiết, quy mô nhóm",
  "parameters": {
    "type": "object",
    "properties": {
      "budget_max": {
        "type": "integer",
        "description": "Giá tối đa (VND). Ví dụ: 80000"
      },
      "diet_type": {
        "type": "string",
        "enum": ["low_carb", "high_protein", "vegetarian", "low_cal"],
        "description": "Chế độ ăn của người dùng"
      },
      "cuisine": {
        "type": "string",
        "description": "Loại ẩm thực. Ví dụ: vietnamese, japanese, korean"
      },
      "weather": {
        "type": "string",
        "enum": ["cold", "rain", "hot"],
        "description": "Thời tiết hiện tại ảnh hưởng đến gợi ý"
      },
      "group_size": {
        "type": "integer",
        "description": "Số người ăn cùng"
      }
    }
  }
}
```

---

### 5.2 Tool: `add_to_cart`

**Khi nào gọi:** Intent là `ADD_TO_CART`, sau khi user confirm

```python
def add_to_cart(
    session_id: str,
    dish_id: str,
    quantity: int = 1
) -> dict:
    """
    Thêm món vào giỏ hàng trong-memory.
    """
    cart = carts.get(session_id, {"items": [], "total": 0})
    dish = get_dish_by_id(dish_id)  # lookup từ menu.json

    if not dish:
        return {"success": False, "error": "Không tìm thấy món này"}

    # Kiểm tra đã có trong giỏ chưa
    existing = next((i for i in cart["items"] if i["dish_id"] == dish_id), None)
    if existing:
        existing["quantity"] += quantity
    else:
        cart["items"].append({
            "dish_id": dish_id,
            "name": dish["name"],
            "price": dish["price"],
            "quantity": quantity
        })

    cart["total"] = sum(i["price"] * i["quantity"] for i in cart["items"])
    carts[session_id] = cart

    return {
        "success": True,
        "added_item": dish["name"],
        "cart_total": cart["total"],
        "item_count": len(cart["items"])
    }
```

**OpenAI function schema:**
```json
{
  "name": "add_to_cart",
  "description": "Thêm một món ăn vào giỏ hàng của người dùng",
  "parameters": {
    "type": "object",
    "properties": {
      "dish_id": {
        "type": "string",
        "description": "ID của món ăn cần thêm (từ danh sách suggestions)"
      },
      "quantity": {
        "type": "integer",
        "description": "Số lượng, mặc định là 1",
        "default": 1
      }
    },
    "required": ["dish_id"]
  }
}
```

---

### 5.3 Tool: `view_cart`

**Khi nào gọi:** Intent là `VIEW_CART`

```python
def view_cart(session_id: str) -> dict:
    """
    Trả về nội dung giỏ hàng hiện tại.
    """
    cart = carts.get(session_id, {"items": [], "total": 0})
    return {
        "items": cart["items"],
        "total": cart["total"],
        "item_count": len(cart["items"]),
        "summary": f"{len(cart['items'])} món, tổng {cart['total']:,}đ"
    }
```

---

### 5.4 Tool: `get_time_context`

**Khi nào gọi:** Tự động gọi đầu mỗi conversation turn để inject context thời gian

```python
def get_time_context() -> dict:
    """
    Trả về ngữ cảnh thời gian hiện tại để gợi ý phù hợp.
    """
    from datetime import datetime
    hour = datetime.now().hour
    if 6 <= hour < 10:
        meal = "breakfast"
        suggestion = "bữa sáng nhẹ nhàng"
    elif 10 <= hour < 14:
        meal = "lunch"
        suggestion = "bữa trưa nhanh gọn"
    elif 14 <= hour < 17:
        meal = "afternoon_snack"
        suggestion = "bữa xế nhẹ"
    elif 17 <= hour < 21:
        meal = "dinner"
        suggestion = "bữa tối"
    else:
        meal = "late_night"
        suggestion = "ăn khuya"

    return {"meal_time": meal, "suggestion_context": suggestion, "hour": hour}
```


---

## 6. Recommendation Engine

Sau khi `search_menu` trả về candidates (tối đa 10 món), Recommendation Engine xếp hạng lại và chọn top 3.

### 6.1 Ranking formula

```
Score = w1 × Relevance + w2 × Popularity + w3 × Diversity
```

| Weight | Ý nghĩa | Giá trị mặc định |
|--------|---------|-----------------|
| `w1` | Relevance — khớp với intent/entities | 0.5 |
| `w2` | Popularity — điểm rating, số order | 0.3 |
| `w3` | Diversity — khác với món đã gợi ý gần đây | 0.2 |

### 6.2 Relevance score

```python
def calc_relevance(dish: dict, context: dict) -> float:
    score = 0.0

    # Budget fit: càng gần budget_max càng tốt (không muốn rẻ quá)
    if context.get("budget_max"):
        ratio = dish["price"] / context["budget_max"]
        score += max(0, 1 - abs(ratio - 0.75))  # sweet spot ở 75% budget

    # Diet match
    if context.get("diet_type"):
        if context["diet_type"] in dish.get("diet_tags", []):
            score += 0.5

    # Weather match
    if context.get("weather") == "cold" and dish.get("is_hot"):
        score += 0.3
    if context.get("weather") == "rain" and dish.get("comfort_score", 0) > 0.6:
        score += 0.3

    # Time match
    if context.get("meal_time") in dish.get("meal_tags", []):
        score += 0.2

    return min(score, 1.0)
```

### 6.3 Diversity boost

Tránh recommend toàn phở hoặc toàn cơm:

```python
def apply_diversity(ranked_dishes: list, session_history: list) -> list:
    recently_shown = [d["dish_id"] for d in session_history[-6:]]
    recently_cuisines = [d.get("cuisine") for d in session_history[-3:]]

    for dish in ranked_dishes:
        # Penalty nếu đã gợi ý gần đây
        if dish["id"] in recently_shown:
            dish["_score"] *= 0.5
        # Penalty nhẹ nếu cùng cuisine liên tiếp
        if dish.get("cuisine") in recently_cuisines:
            dish["_score"] *= 0.8

    return sorted(ranked_dishes, key=lambda d: d["_score"], reverse=True)
```

### 6.4 LLM Re-ranking (optional nếu còn thời gian)

Sau khi có top 5 từ scoring, có thể gọi LLM thêm một lần để:
- Sinh `reason` cho mỗi gợi ý
- Re-order lần cuối dựa trên ngữ cảnh hội thoại tự nhiên

```
RE-RANKING PROMPT
=================
Dưới đây là 5 món ăn phù hợp với người dùng.
Hãy chọn TOP 3 phù hợp nhất và viết lý do ngắn (1 câu tiếng Việt) cho mỗi món.

Context người dùng:
- Vừa nói: "{last_message}"
- Ngân sách: {budget}
- Thời điểm: {meal_time}
- Sở thích: {preferences}

Danh sách món:
{dishes_json}

Trả về JSON:
[
  {"dish_id": "...", "reason": "..."},
  {"dish_id": "...", "reason": "..."},
  {"dish_id": "...", "reason": "..."}
]
```

---

## 7. Memory & Context

### 7.1 Cấu trúc Session (in-memory Python dict)

```python
sessions = {
    "session_id_abc123": {
        # User profile (từ onboarding, lưu localStorage → gửi lên)
        "user_profile": {
            "budget": 80000,          # ngân sách trung bình
            "diet": "none",           # none | low_carb | vegetarian | ...
            "preferred_cuisine": [],  # ["vietnamese", "japanese"]
        },

        # Conversation history (multi-turn context)
        "history": [
            {"role": "user", "content": "Ăn gì giờ?"},
            {"role": "assistant", "content": "..."},
        ],

        # Context của turn hiện tại
        "current_entities": {
            "budget_max": None,
            "diet_type": None,
            "weather": None,
            "group_size": None,
        },

        # Suggestions đã show trong session (để handle "thêm cái đầu tiên")
        "last_suggestions": [
            {"dish_id": "dish_01", "name": "Phở bò tái", "price": 65000},
            {"dish_id": "dish_02", "name": "Bún bò Huế", "price": 75000},
        ],

        # Cart
        "cart": {
            "items": [],
            "total": 0
        }
    }
}
```

### 7.2 Context injection vào System Prompt

Mỗi turn, inject context thực tế vào system prompt:

```python
def build_system_prompt(session: dict) -> str:
    profile = session["user_profile"]
    cart = session["cart"]
    time_ctx = get_time_context()

    cart_summary = (
        f"{len(cart['items'])} món trong giỏ, tổng {cart['total']:,}đ"
        if cart["items"] else "Giỏ hàng trống"
    )

    return SYSTEM_PROMPT_TEMPLATE.format(
        current_time=time_ctx["suggestion_context"],
        user_budget=f"{profile['budget']:,}đ" if profile.get("budget") else "chưa biết",
        user_preferences=", ".join(profile.get("preferred_cuisine", [])) or "chưa biết",
        recent_orders="chưa có lịch sử",  # lab đơn giản không cần
        cart_summary=cart_summary
    )
```

### 7.3 Xử lý "thêm món đầu tiên / thứ hai"

Người dùng hay nói "thêm cái đầu tiên" mà không nói tên. Handle bằng `last_suggestions`:

```python
def resolve_dish_ref(dish_ref: str, last_suggestions: list) -> str | None:
    ref_map = {"first": 0, "second": 1, "third": 2, "đầu tiên": 0, "thứ hai": 1, "thứ ba": 2}
    idx = ref_map.get(dish_ref.lower())
    if idx is not None and idx < len(last_suggestions):
        return last_suggestions[idx]["dish_id"]
    # Thử match tên món
    for dish in last_suggestions:
        if dish_ref.lower() in dish["name"].lower():
            return dish["dish_id"]
    return None
```

---

## 8. Conversation Flow

### 8.1 Happy path — Discovery to Cart

```
Turn 1:
  User:  "Ăn gì giờ nhỉ?"
  Intent: FIND_FOOD (confidence: 0.95)
  Action: search_menu() → top 10 → rank → top 3
  Reply:  "Tối nay Yumi gợi ý 3 món này cho bạn 😊"
          [Card: Phở bò tái - 65k]
          [Card: Cơm gà - 70k]
          [Card: Bún bò - 75k]
          "Bạn muốn thêm món nào vào giỏ không?"

Turn 2:
  User:  "Thêm cái đầu tiên"
  Intent: ADD_TO_CART (confidence: 0.97)
  Entities: dish_ref = "first" → resolve → "dish_01"
  Action: Xác nhận → "Thêm Phở bò tái vào giỏ nhé?"
  Reply:  "Đã thêm Phở bò tái (65.000đ) vào giỏ hàng ✓
           Giỏ hàng: 1 món · 65.000đ
           Bạn muốn thêm gì nữa không?"

Turn 3:
  User:  "Xem giỏ hàng"
  Intent: VIEW_CART
  Action: view_cart(session_id)
  Reply:  "Giỏ hàng của bạn:
           • Phở bò tái × 1 — 65.000đ
           ──────────────────
           Tổng: 65.000đ
           Bạn muốn đặt hàng không?"
```

### 8.2 Budget flow

```
User:  "Có gì dưới 60k không?"
Intent: BY_BUDGET, entities: { budget_max: 60000 }
Action: search_menu(budget_max=60000)
Reply:  "Có 3 món dưới 60k đang có sẵn:
         [Card: Bánh mì thịt - 30k]
         [Card: Cơm bình dân - 45k]
         [Card: Bún riêu - 55k]"
```

### 8.3 Diet flow

```
User:  "Tôi đang giảm cân"
Intent: BY_DIET, entities: { diet_type: "low_cal" }
Action: search_menu(diet_type="low_cal")
Reply:  "Yumi tìm 3 món ít calo cho bạn:
         [Card: Salad cá ngừ - 280kcal - 55k]
         [Card: Ức gà hấp - 320kcal - 65k]
         [Card: Gỏi cuốn - 180kcal - 40k]"
```

### 8.4 Ambiguous flow — Clarification

```
User:  "Ăn gì cũng được"
Intent: FIND_FOOD, confidence: 0.72 → CLARIFY
Reply:  "Bạn đang đói nhiều hay chỉ ăn nhẹ thôi? 😊"

User:  "Đói thật sự"
Intent: FIND_FOOD, thêm context: "hearty meal"
Action: search_menu() với ưu tiên món no bụng
Reply:  [3 món no bụng gợi ý]
```

### 8.5 Group order flow

```
User:  "Đặt cho 4 người"
Intent: BY_GROUP, entities: { group_size: 4 }
Action: search_menu(group_size=4) → ưu tiên món shareable/combo
Reply:  "Cho 4 người Yumi gợi ý mấy món dễ chia sẻ:
         [Card: Lẩu thái - 280k]
         [Card: Cơm phần combo 4 - 220k]
         [Card: Pizza cỡ lớn - 180k]"
```

---

## 9. Orchestrator Pipeline

Đây là hàm trung tâm xử lý mỗi message từ user.

```python
async def orchestrate(message: str, session_id: str, user_context: dict) -> dict:
    """
    Main AI pipeline. Gọi từ POST /chat endpoint.
    """
    # 1. Load hoặc tạo session
    session = get_or_create_session(session_id, user_context)

    # 2. Thêm message vào history
    session["history"].append({"role": "user", "content": message})

    # 3. Classify intent + extract entities
    classification = await classify_intent(
        message=message,
        history=session["history"][-6:]  # 3 turns gần nhất
    )
    intent = classification["intent"]
    entities = classification["entities"]
    confidence = classification["confidence"]

    # 4. Merge entities với session context
    merged_context = merge_context(session, entities)

    # 5. Confidence check
    if confidence < 0.60:
        reply = build_fallback_reply()
        session["history"].append({"role": "assistant", "content": reply["reply"]})
        return reply

    if confidence < 0.85:
        clarify = build_clarification(intent, merged_context)
        session["history"].append({"role": "assistant", "content": clarify["reply"]})
        return clarify

    # 6. Route theo intent
    suggestions = []
    if intent in ["FIND_FOOD", "BY_BUDGET", "BY_DIET", "BY_CONTEXT", "BY_GROUP"]:
        candidates = search_menu(**extract_search_params(merged_context))
        suggestions = rank_and_select(candidates, merged_context, session)
        session["last_suggestions"] = suggestions  # lưu để handle "cái đầu tiên"

    elif intent == "ADD_TO_CART":
        dish_id = resolve_dish_ref(
            entities.get("dish_ref", ""),
            session["last_suggestions"]
        )
        if dish_id:
            result = add_to_cart(session_id, dish_id, entities.get("quantity", 1))
            session["cart"] = get_cart(session_id)

    elif intent == "VIEW_CART":
        cart_data = view_cart(session_id)

    # 7. Build system prompt với context mới nhất
    system_prompt = build_system_prompt(session)

    # 8. Gọi LLM để sinh reply
    llm_response = await call_llm(
        system_prompt=system_prompt,
        history=session["history"],
        suggestions=suggestions,
        intent=intent,
        context=merged_context
    )

    # 9. Parse response
    parsed = parse_llm_response(llm_response)

    # 10. Enrich suggestions với full dish data
    enriched_suggestions = [
        {**get_dish_by_id(s["dish_id"]), "reason": s["reason"]}
        for s in parsed.get("suggestions", [])
        if get_dish_by_id(s["dish_id"])
    ]

    # 11. Lưu reply vào history
    session["history"].append({"role": "assistant", "content": parsed["reply"]})
    save_session(session_id, session)

    return {
        "reply": parsed["reply"],
        "intent": intent,
        "suggestions": enriched_suggestions,
        "cart_summary": session["cart"]
    }
```

---

## 10. Xử lý lỗi & Edge Cases

### 10.1 Bảng edge cases

| Tình huống | Cách xử lý |
|------------|-----------|
| LLM timeout | Retry 1 lần, sau đó trả lỗi thân thiện: "Yumi bị lag xíu, bạn thử lại nhé 😅" |
| Không có món nào khớp filter | Nới lỏng filter (bỏ diet_type), gợi ý popular dishes |
| `dish_ref` không resolve được | Hỏi lại: "Bạn muốn thêm món nào? Phở bò hay cơm gà?" |
| LLM trả invalid JSON | Parse fallback: dùng regex extract hoặc trả plain text |
| User hỏi ngoài topic đồ ăn | Intent = CHITCHAT → trả lời ngắn rồi redirect về ordering |
| Session không tồn tại | Tự động tạo session mới |
| Giỏ hàng trống khi VIEW_CART | "Giỏ hàng của bạn đang trống. Bạn muốn Yumi gợi ý gì không?" |

### 10.2 JSON parse fallback

```python
def parse_llm_response(raw: str) -> dict:
    try:
        # Thử parse JSON trực tiếp
        return json.loads(raw)
    except json.JSONDecodeError:
        # Thử extract JSON từ trong text (LLM hay thêm markdown)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        # Fallback: wrap plain text vào format chuẩn
        return {
            "reply": raw[:500],  # truncate nếu quá dài
            "intent": "UNKNOWN",
            "action": "none",
            "suggestions": []
        }
```

### 10.3 No results fallback

```python
def handle_no_results(context: dict) -> list:
    """Khi không có món nào khớp, trả popular dishes."""
    # Thử nới lỏng budget 20%
    if context.get("budget_max"):
        relaxed = search_menu(budget_max=int(context["budget_max"] * 1.2))
        if relaxed:
            return relaxed[:3]

    # Fallback: top 3 món phổ biến nhất
    all_dishes = load_menu()
    return sorted(all_dishes, key=lambda d: d.get("popularity", 0), reverse=True)[:3]
```

---

## 11. Code mẫu

### 11.1 `prompts.py` — Toàn bộ prompt templates

```python
SYSTEM_PROMPT = """
Bạn là Yumi, trợ lý đặt đồ ăn thông minh và thân thiện.
Bạn nói tiếng Việt, giọng trẻ trung, dùng "bạn/mình".

## Context hiện tại
- Thời điểm: {current_time}
- Ngân sách: {user_budget}
- Sở thích: {user_preferences}
- Giỏ hàng: {cart_summary}

## Rules
1. CHỈ gợi ý món trong danh sách được cung cấp. KHÔNG bịa.
2. Tối đa 3 gợi ý mỗi lần.
3. Hỏi tối đa 1 câu làm rõ nếu mơ hồ.
4. Reply ngắn: 2-3 câu text + suggestions.
5. Kết thúc bằng câu gợi ý hành động tiếp theo.

## Output Format
{{
  "reply": "...",
  "intent": "INTENT_NAME",
  "action": "none|search|add_to_cart|view_cart|clarify",
  "suggestions": [{{"dish_id": "...", "reason": "..."}}],
  "clarification_question": null
}}
"""

INTENT_CLASSIFICATION_PROMPT = """
Phân loại tin nhắn vào một intent:
FIND_FOOD | BY_BUDGET | BY_DIET | BY_CONTEXT | BY_GROUP | ADD_TO_CART | VIEW_CART | MODIFY_CART | CHITCHAT

Tin nhắn: "{message}"
Context gần nhất: {recent_context}

Trả về JSON:
{{
  "intent": "...",
  "confidence": 0.0-1.0,
  "entities": {{
    "budget_max": null,
    "diet_type": null,
    "weather": null,
    "group_size": null,
    "dish_ref": null,
    "quantity": null
  }}
}}
"""
```

### 11.2 `menu.json` — Cấu trúc mock data

```json
[
  {
    "id": "dish_01",
    "name": "Phở bò tái",
    "price": 65000,
    "restaurant": "Phở Hà Nội",
    "cuisine": "vietnamese",
    "category": "noodle",
    "diet_tags": [],
    "meal_tags": ["lunch", "dinner"],
    "is_hot": true,
    "comfort_score": 0.9,
    "shareable": false,
    "popularity": 0.95,
    "image_url": "https://images.unsplash.com/photo-1555126634-323283e090fa?w=400",
    "description": "Phở bò truyền thống Hà Nội, nước dùng trong vắt"
  },
  {
    "id": "dish_02",
    "name": "Salad cá ngừ",
    "price": 55000,
    "restaurant": "Fresh Bowl",
    "cuisine": "western",
    "category": "salad",
    "diet_tags": ["low_cal", "high_protein"],
    "meal_tags": ["lunch", "dinner"],
    "is_hot": false,
    "comfort_score": 0.4,
    "shareable": false,
    "popularity": 0.72,
    "calories": 280,
    "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
    "description": "Salad rau xanh với cá ngừ ngâm dầu ô liu"
  }
]
```

### 11.3 `chat.py` — POST /chat endpoint

```python
from fastapi import APIRouter
from pydantic import BaseModel
from ai.orchestrator import orchestrate

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_context: dict = {}

class ChatResponse(BaseModel):
    reply: str
    intent: str
    suggestions: list
    cart_summary: dict

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await orchestrate(
        message=req.message,
        session_id=req.session_id,
        user_context=req.user_context
    )
    return result
```

---

*Yumi AI Core Design · Lab Day · 2026-06-03*
