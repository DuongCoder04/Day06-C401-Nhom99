from typing import Any, Literal

from pydantic import BaseModel, Field


Intent = Literal[
    "FIND_FOOD",
    "BY_BUDGET",
    "BY_DIET",
    "BY_CONTEXT",
    "BY_GROUP",
    "ADD_TO_CART",
    "VIEW_CART",
    "MODIFY_CART",
    "CHITCHAT",
    "SAVE_PREFERENCE",
    "GET_PREFERENCES",
    "CHECK_AVAILABILITY",
    "RECOMMEND_COMBO",
    "UNKNOWN",
]

PreferenceKey = Literal["budget", "diet", "cuisine", "spice", "avoid", "favorite"]


class Dish(BaseModel):
    id: str
    name: str
    price: int
    restaurant: str
    cuisine: str
    category: str
    diet_tags: list[str] = Field(default_factory=list)
    meal_tags: list[str] = Field(default_factory=list)
    is_hot: bool = False
    comfort_score: float = 0
    shareable: bool = False
    popularity: float = 0
    image_url: str
    description: str


class Suggestion(Dish):
    reason: str
    rating: float | None = None
    is_open: bool | None = None
    delivery_minutes: int | None = None
    delivery_fee: int | None = None
    distance_km: float | None = None


class Entities(BaseModel):
    budget_max: int | None = None
    diet_type: str | None = None
    weather: str | None = None
    group_size: int | None = None
    dish_ref: str | None = None
    quantity: int = 1
    meal_time: str | None = None
    preference_hint: str | None = None


class Classification(BaseModel):
    intent: Intent
    confidence: float
    entities: Entities


class CartItem(BaseModel):
    dish_id: str
    name: str
    price: int
    restaurant: str
    image_url: str
    quantity: int


class CartResponse(BaseModel):
    items: list[CartItem]
    total: int
    item_count: int


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    intent: Intent
    action: str
    suggestions: list[Suggestion] = Field(default_factory=list)
    cart_summary: CartResponse
    clarification_question: str | None = None


class AddToCartRequest(BaseModel):
    session_id: str
    dish_id: str
    quantity: int = 1


class UpdateCartRequest(BaseModel):
    session_id: str
    dish_id: str
    delta: int


class RemoveCartRequest(BaseModel):
    session_id: str
    dish_id: str


class SavePreferenceRequest(BaseModel):
    session_id: str
    preference_key: PreferenceKey
    preference_value: str
