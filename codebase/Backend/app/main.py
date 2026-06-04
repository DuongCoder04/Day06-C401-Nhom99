from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, cart, chat, menu, preferences
from app.ai.llm_client import has_llm_config, provider_mode
from app.db.sqlite_store import init_db


app = FastAPI(title="Yumi API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(menu.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "yumi-api"}


@app.get("/api/config")
def config() -> dict:
    return {
        "llm_enabled": has_llm_config(),
        "mode": provider_mode(),
    }
