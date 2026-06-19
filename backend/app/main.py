"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base, run_seed
from app.api.router import api_router
from app.websocket.chat_handler import chat_websocket_endpoint
from app.websocket.admin_handler import admin_websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: setup DB tables and seed data on startup."""
    settings = get_settings()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await run_seed()
    yield


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="ReturnShield AI Agent",
        description="AI Customer Support Agent for e-commerce refund processing",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST API routes
    app.include_router(api_router, prefix="/api")

    # WebSocket endpoints
    app.add_api_websocket_route("/ws/chat/{customer_id}", chat_websocket_endpoint)
    app.add_api_websocket_route("/ws/admin", admin_websocket_endpoint)

    return app


app = create_app()
