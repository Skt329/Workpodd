"""Conversation API endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_conversations():
    """List active conversations (from in-memory store)."""
    from app.websocket.chat_handler import _conversation_ids, _conversation_histories
    conversations = []
    for customer_id, conv_id in _conversation_ids.items():
        history = _conversation_histories.get(customer_id, [])
        conversations.append({
            "conversation_id": conv_id,
            "customer_id": customer_id,
            "message_count": len(history),
            "status": "active" if history else "idle",
        })
    return conversations
