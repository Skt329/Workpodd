"""Event Service — structured agent event logging and broadcasting."""

import uuid
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_log import AgentEvent, EventType


class EventService:
    """Manages agent reasoning events — persists to DB and broadcasts via WebSocket."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._broadcast_callback = None

    def set_broadcast_callback(self, callback):
        """Set a callback function for broadcasting events via WebSocket."""
        self._broadcast_callback = callback

    async def emit_event(
        self,
        conversation_id: str,
        event_type: str,
        step_index: int,
        tool_name: str | None = None,
        input_data: dict | None = None,
        output_data: dict | None = None,
        latency_ms: int | None = None,
    ) -> dict:
        """Create and persist an agent event, then broadcast it."""
        event = AgentEvent(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            event_type=EventType(event_type),
            step_index=step_index,
            tool_name=tool_name,
            input_data=json.dumps(input_data) if input_data else None,
            output_data=json.dumps(output_data) if output_data else None,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )
        self._session.add(event)
        await self._session.flush()

        event_dict = {
            "id": event.id,
            "conversation_id": event.conversation_id,
            "event_type": event.event_type.value,
            "step_index": event.step_index,
            "tool_name": event.tool_name,
            "input_data": input_data,
            "output_data": output_data,
            "latency_ms": event.latency_ms,
            "timestamp": event.timestamp.isoformat(),
        }

        # Broadcast to admin WebSocket listeners
        if self._broadcast_callback:
            await self._broadcast_callback(event_dict)

        return event_dict

    async def get_conversation_events(self, conversation_id: str) -> list[dict]:
        """Get all events for a specific conversation."""
        result = await self._session.execute(
            select(AgentEvent)
            .where(AgentEvent.conversation_id == conversation_id)
            .order_by(AgentEvent.step_index, AgentEvent.timestamp)
        )
        events = result.scalars().all()
        return [self._event_to_dict(e) for e in events]

    async def get_recent_events(self, limit: int = 100) -> list[dict]:
        """Get the most recent events across all conversations."""
        result = await self._session.execute(
            select(AgentEvent)
            .order_by(AgentEvent.timestamp.desc())
            .limit(limit)
        )
        events = result.scalars().all()
        return [self._event_to_dict(e) for e in events]

    def _event_to_dict(self, e: AgentEvent) -> dict:
        return {
            "id": e.id,
            "conversation_id": e.conversation_id,
            "event_type": e.event_type.value,
            "step_index": e.step_index,
            "tool_name": e.tool_name,
            "input_data": json.loads(e.input_data) if e.input_data else None,
            "output_data": json.loads(e.output_data) if e.output_data else None,
            "latency_ms": e.latency_ms,
            "timestamp": e.timestamp.isoformat(),
        }
