"""API router — aggregates all REST API route modules."""

from fastapi import APIRouter

from app.api.customers import router as customers_router
from app.api.orders import router as orders_router
from app.api.refunds import router as refunds_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.conversations import router as conversations_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(customers_router, prefix="/customers", tags=["Customers"])
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(refunds_router, prefix="/refunds", tags=["Refunds"])
api_router.include_router(events_router, prefix="/events", tags=["Events"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
