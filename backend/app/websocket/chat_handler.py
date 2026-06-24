"""Chat WebSocket handler — handles customer conversations with the agent.

Responsibilities:
1. Manage WebSocket sessions per customer
2. Inject customer context into system prompt
3. Persist conversations to DB
4. Persist + broadcast agent events for admin observability
5. Apply input guardrails (prompt injection detection)
"""

import json
import uuid
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from app.websocket.manager import manager
from app.agent.graph import run_agent
from app.database import AsyncSessionLocal
from app.services.crm_service import CRMService
from app.services.event_service import EventService
from app.models.conversation import Conversation
from app.security import sanitize_input
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.agent.prompts import build_system_prompt


# In-memory conversation message history (per customer session)
_conversation_histories: dict[str, list] = {}
_conversation_ids: dict[str, str] = {}
_customer_contexts: dict[str, str] = {}


async def _build_customer_context(customer_id: str) -> str:
    """Fetch customer profile + orders and build a context-injected system prompt."""
    async with AsyncSessionLocal() as session:
        crm = CRMService(session)
        customer = await crm.lookup_customer(customer_id)
        orders = await crm.get_customer_orders(customer_id)
        refund_history = await crm.get_refund_history(customer_id, days=90)

    if not customer:
        return build_system_prompt(customer_id, None, [], [])

    return build_system_prompt(customer_id, customer, orders or [], refund_history or [])


async def _persist_conversation(customer_id: str, conversation_id: str, history: list):
    """Persist conversation messages to the database."""
    try:
        messages_json = json.dumps([
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in history
        ])

        async with AsyncSessionLocal() as session:
            # Check if conversation exists
            from sqlalchemy import select
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = result.scalar_one_or_none()

            if conv:
                conv.messages_json = messages_json
                conv.updated_at = datetime.utcnow()
            else:
                conv = Conversation(
                    id=conversation_id,
                    customer_id=customer_id,
                    status="active",
                    messages_json=messages_json,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(conv)

            await session.commit()
    except Exception as e:
        print(f"[WARN] Failed to persist conversation {conversation_id}: {e}")


# Buffer for batch-persisting events after an agent run
_event_buffer: list[dict] = []


async def _broadcast_event(event: dict):
    """Broadcast an event to admin WebSocket in real-time + buffer for batch DB write."""
    await manager.broadcast("admin", event)
    _event_buffer.append(event)


async def _flush_event_buffer():
    """Persist all buffered events to the DB in a single session/transaction."""
    if not _event_buffer:
        return

    events_to_persist = list(_event_buffer)
    _event_buffer.clear()

    try:
        async with AsyncSessionLocal() as session:
            event_svc = EventService(session)
            for event in events_to_persist:
                await event_svc.emit_event(
                    conversation_id=event.get("conversation_id", ""),
                    event_type=event.get("type", "UNKNOWN"),
                    step_index=event.get("step_index", 0),
                    tool_name=event.get("tool_name"),
                    input_data=event.get("input_data"),
                    output_data=event.get("output_data"),
                    latency_ms=event.get("latency_ms"),
                )
            await session.commit()
    except Exception as e:
        print(f"[WARN] Failed to batch-persist {len(events_to_persist)} events: {e}")



async def chat_websocket_endpoint(websocket: WebSocket, customer_id: str):
    """WebSocket endpoint for customer chat sessions.

    URL: /ws/chat/{customer_id}

    Incoming messages: { "type": "chat_message", "message": "..." }
    Outgoing messages:
        - { "type": "agent_typing" }
        - { "type": "agent_message", "message": "..." }
        - { "type": "refund_status", "status": "APPROVED|DENIED|..." }
        - { "type": "error", "message": "..." }
        - { "type": "security_warning", "message": "..." }
    """
    channel = f"chat:{customer_id}"
    await manager.connect(websocket, channel)

    # Get or create conversation ID for this customer
    if customer_id not in _conversation_ids:
        _conversation_ids[customer_id] = str(uuid.uuid4())
        _conversation_histories[customer_id] = []

    conversation_id = _conversation_ids[customer_id]

    # Build customer context (system prompt with profile + orders pre-loaded)
    if customer_id not in _customer_contexts:
        _customer_contexts[customer_id] = await _build_customer_context(customer_id)

    # Emit conversation start event (persisted + broadcast)
    await _broadcast_event({
        "type": "CONVERSATION_START",
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "step_index": 0,
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid message format",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                continue

            msg_type = msg.get("type", "")
            message_text = msg.get("message", "")

            if msg_type == "chat_message" and message_text:
                # ── Security: Input Sanitization ─────────────────────────
                sanitization = sanitize_input(message_text)

                if not sanitization.sanitized_message:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "Please enter a valid message.",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue

                # Log injection attempts to admin dashboard
                if not sanitization.is_safe:
                    await _broadcast_event({
                        "type": "SECURITY_WARNING",
                        "conversation_id": conversation_id,
                        "customer_id": customer_id,
                        "step_index": len(_conversation_histories.get(customer_id, [])),
                        "input_data": {
                            "violations": sanitization.violations,
                            "original_message": message_text[:200],
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                # Use sanitized message
                clean_message = sanitization.sanitized_message

                # ── Send typing indicator ────────────────────────────────
                await manager.send_personal(websocket, {
                    "type": "agent_typing",
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # ── Emit user message event ──────────────────────────────
                step = len(_conversation_histories.get(customer_id, []))
                await _broadcast_event({
                    "type": "USER_MESSAGE",
                    "conversation_id": conversation_id,
                    "customer_id": customer_id,
                    "input_data": {"message": clean_message[:200]},
                    "step_index": step,
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # ── Add to conversation history ──────────────────────────
                history = _conversation_histories.setdefault(customer_id, [])
                history.append(HumanMessage(content=clean_message))

                # Build messages with customer-specific system prompt
                system_prompt = _customer_contexts.get(customer_id, "")
                messages = [SystemMessage(content=system_prompt)] + history

                # ── Event callback (persists + broadcasts) ───────────────
                async def event_callback(event: dict):
                    await _broadcast_event(event)

                # ── Token callback (streams response to customer) ─────────
                async def token_callback(token: str):
                    await manager.send_personal(websocket, {
                        "type": "agent_token",
                        "message": token,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                try:
                    # Run the agent with scoped tools + streaming
                    result = await run_agent(
                        customer_id=customer_id,
                        conversation_id=conversation_id,
                        messages=messages,
                        event_callback=event_callback,
                        token_callback=token_callback,
                    )

                    response_text = result.get("response", "I'm sorry, I encountered an issue. Please try again.")

                    # Store assistant response in history
                    history.append(AIMessage(content=response_text))

                    # Persist conversation to DB
                    await _persist_conversation(customer_id, conversation_id, history)

                    # Send agent response to customer
                    await manager.send_personal(websocket, {
                        "type": "agent_message",
                        "message": response_text,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    # Check for refund status in events
                    for event in result.get("events", []):
                        if event.get("type") == "TOOL_CALL" and event.get("tool_name") in ("process_refund", "escalate_to_human"):
                            status = "ESCALATED" if event["tool_name"] == "escalate_to_human" else "PROCESSED"
                            await manager.send_personal(websocket, {
                                "type": "refund_status",
                                "status": status,
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                    # Batch-persist all events from this agent run in one DB transaction
                    await _flush_event_buffer()

                except Exception as e:
                    error_msg = "I apologize, but I encountered a technical issue. Please try again in a moment."
                    print(f"[ERROR] Agent error for {customer_id}: {e}")

                    await manager.send_personal(websocket, {
                        "type": "agent_message",
                        "message": error_msg,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    await _broadcast_event({
                        "type": "AGENT_ERROR",
                        "conversation_id": conversation_id,
                        "customer_id": customer_id,
                        "step_index": len(history),
                        "output_data": {"error": str(e)[:500]},
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    await _flush_event_buffer()

    except WebSocketDisconnect:
        await manager.disconnect(websocket, channel)
        await _broadcast_event({
            "type": "CONVERSATION_END",
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "step_index": 0,
            "timestamp": datetime.utcnow().isoformat(),
        })
        await _flush_event_buffer()
