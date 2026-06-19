"""Event API endpoints — agent reasoning logs."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.event_service import EventService

router = APIRouter()


@router.get("")
async def list_events(
    conversation_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get agent reasoning events.

    If conversation_id is provided, returns events for that conversation.
    Otherwise, returns the most recent events across all conversations.
    """
    svc = EventService(db)
    if conversation_id:
        return await svc.get_conversation_events(conversation_id)
    return await svc.get_recent_events(limit=limit)
