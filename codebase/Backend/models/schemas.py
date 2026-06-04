from pydantic import BaseModel, Field


class UserContext(BaseModel):
    budget: int | None = None
    diet: str | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_context: UserContext | None = None


class Suggestion(BaseModel):
    id: str
    name: str
    price: int
    restaurant: str
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    suggestions: list[Suggestion] = Field(default_factory=list)


class MenuItem(BaseModel):
    id: str
    name: str
    price: int
    category: str
    tags: list[str] = Field(default_factory=list)
    restaurant: str
    image_url: str | None = None


class MenuResponse(BaseModel):
    items: list[MenuItem]


class CartAddRequest(BaseModel):
    session_id: str
    dish_id: str
    quantity: int = 1


class CartRemoveRequest(BaseModel):
    session_id: str
    dish_id: str


class CartItem(BaseModel):
    dish_id: str
    name: str
    price: int
    quantity: int


class CartResponse(BaseModel):
    items: list[CartItem]
    total: int


class CartActionResponse(BaseModel):
    success: bool
    cart_total: int
    item_count: int
