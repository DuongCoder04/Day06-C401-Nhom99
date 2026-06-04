from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, cart, chat, menu, preferences
from app.ai.llm_client import has_llm_config, provider_mode
from app.db.sqlite_store import init_db

import os


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    init_db()
    yield
    # Shutdown (nothing needed for SQLite)


app = FastAPI(title="Yumi API", version="1.0.0", lifespan=lifespan)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Read allowed origins from env var (comma-separated) with localhost fallback
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins
    else [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(menu.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "yumi-api"}


@app.get("/api/config")
def config() -> dict:
    return {
        "llm_enabled": has_llm_config(),
        "mode": provider_mode(),
    }
