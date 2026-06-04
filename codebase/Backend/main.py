from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.cart import router as cart_router
from api.chat import router as chat_router
from api.menu import router as menu_router

app = FastAPI(title="Yumi Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu_router, prefix="/menu", tags=["menu"])
app.include_router(cart_router, prefix="/cart", tags=["cart"])
app.include_router(chat_router, tags=["chat"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
