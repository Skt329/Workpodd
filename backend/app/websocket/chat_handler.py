"""Chat WebSocket handler — handles customer conversations with the agent."""

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
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.agent.prompts import build_system_prompt


# In-memory conversation message history (per customer session)
_conversation_histories: dict[str, list] = {}
_conversation_ids: dict[str, str] = {}
_customer_contexts: dict[str, str] = {}  # cached system prompts with customer context


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


async def chat_websocket_endpoint(websocket: WebSocket, customer_id: str):
    """WebSocket endpoint for customer chat sessions.

    URL: /ws/chat/{customer_id}

    Incoming messages: { "type": "chat_message", "message": "..." }
    Outgoing messages:
        - { "type": "agent_typing" }
        - { "type": "agent_message", "message": "..." }
        - { "type": "refund_status", "status": "APPROVED|DENIED|..." }
        - { "type": "error", "message": "..." }
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

    # Emit conversation start event to admin
    await manager.broadcast("admin", {
        "type": "CONVERSATION_START",
        "conversation_id": conversation_id,
        "customer_id": customer_id,
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
                # Send typing indicator
                await manager.send_personal(websocket, {
                    "type": "agent_typing",
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Emit user message event to admin
                await manager.broadcast("admin", {
                    "type": "USER_MESSAGE",
                    "conversation_id": conversation_id,
                    "customer_id": customer_id,
                    "input_data": {"message": message_text},
                    "step_index": len(_conversation_histories.get(customer_id, [])),
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Add user message to conversation history
                history = _conversation_histories.setdefault(customer_id, [])
                history.append(HumanMessage(content=message_text))

                # Build messages with customer-specific system prompt
                system_prompt = _customer_contexts.get(customer_id, "")
                messages = [SystemMessage(content=system_prompt)] + history

                # Event callback for streaming to admin dashboard
                async def event_callback(event: dict):
                    await manager.broadcast("admin", event)

                try:
                    # Run the agent
                    result = await run_agent(
                        customer_id=customer_id,
                        conversation_id=conversation_id,
                        messages=messages,
                        event_callback=event_callback,
                    )

                    response_text = result.get("response", "I'm sorry, I encountered an issue. Please try again.")

                    # Store assistant response in history
                    history.append(AIMessage(content=response_text))

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

                    # Emit agent response event to admin
                    await manager.broadcast("admin", {
                        "type": "AGENT_RESPONSE",
                        "conversation_id": conversation_id,
                        "customer_id": customer_id,
                        "output_data": {"response": response_text[:300]},
                        "step_index": len(history),
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                except Exception as e:
                    error_msg = f"I apologize, but I encountered a technical issue. Please try again in a moment."
                    print(f"[ERROR] Agent error for {customer_id}: {e}")

                    await manager.send_personal(websocket, {
                        "type": "agent_message",
                        "message": error_msg,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    # Emit error event to admin
                    await manager.broadcast("admin", {
                        "type": "AGENT_ERROR",
                        "conversation_id": conversation_id,
                        "customer_id": customer_id,
                        "output_data": {"error": str(e)[:500]},
                        "timestamp": datetime.utcnow().isoformat(),
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        await manager.broadcast("admin", {
            "type": "CONVERSATION_END",
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
