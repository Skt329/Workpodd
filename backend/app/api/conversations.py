"""Conversation API endpoints — DB-backed chat history."""

import json
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation

router = APIRouter()


@router.get("")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """List all conversations from the database."""
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [
        {
            "conversation_id": c.id,
            "customer_id": c.customer_id,
            "status": c.status,
            "message_count": len(json.loads(c.messages_json)) if c.messages_json else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in convs
    ]


@router.get("/{customer_id}/messages")
async def get_customer_messages(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get chat message history for a specific customer from the database.

    Returns messages in chronological order, formatted for the frontend.
    """
    result = await db.execute(
        select(Conversation)
        .where(Conversation.customer_id == customer_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    conv = result.scalar_one_or_none()

    if not conv or not conv.messages_json:
        return {"messages": [], "conversation_id": None}

    try:
        raw_messages = json.loads(conv.messages_json)
    except (json.JSONDecodeError, TypeError):
        return {"messages": [], "conversation_id": conv.id}

    # Format for frontend ChatMessage type
    messages = []
    for i, msg in enumerate(raw_messages):
        messages.append({
            "id": f"db-{i}",
            "role": "agent" if msg.get("role") == "assistant" else "user",
            "content": msg.get("content", ""),
            "timestamp": conv.updated_at.isoformat() if conv.updated_at else "",
        })

    return {
        "messages": messages,
        "conversation_id": conv.id,
    }
