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
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.prompts import SYSTEM_PROMPT


# In-memory conversation message history (per customer session)
_conversation_histories: dict[str, list] = {}
_conversation_ids: dict[str, str] = {}


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

                # Build messages with system prompt
                messages = [SystemMessage(content=SYSTEM_PROMPT)] + history

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
                    from langchain_core.messages import AIMessage
                    history.append(AIMessage(content=response_text))

                    # Send agent response to customer
                    await manager.send_personal(websocket, {
                        "type": "agent_message",
                        "message": response_text,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    # Check for refund status in events
                    for event in result.get("events", []):
                        output = event.get("output_data", {})
                        if isinstance(output, dict):
                            if "recommendation" in output:
                                await manager.send_personal(websocket, {
                                    "type": "refund_status",
                                    "status": output["recommendation"],
                                    "timestamp": datetime.utcnow().isoformat(),
                                })
                            elif output.get("success") and "refund_id" in output:
                                await manager.send_personal(websocket, {
                                    "type": "refund_status",
                                    "status": output.get("status", "APPROVED"),
                                    "refund_id": output.get("refund_id"),
                                    "timestamp": datetime.utcnow().isoformat(),
                                })

                except Exception as e:
                    error_msg = f"Agent error: {str(e)}"
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "I'm experiencing technical difficulties. Please try again in a moment.",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    # Emit error event to admin
                    await manager.broadcast("admin", {
                        "type": "ERROR",
                        "conversation_id": conversation_id,
                        "output_data": {"error": error_msg},
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            elif msg_type == "reset_conversation":
                # Clear conversation history for this customer
                _conversation_histories[customer_id] = []
                _conversation_ids[customer_id] = str(uuid.uuid4())
                conversation_id = _conversation_ids[customer_id]
                await manager.send_personal(websocket, {
                    "type": "conversation_reset",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket, channel)
        # Emit conversation end event to admin
        await manager.broadcast("admin", {
            "type": "CONVERSATION_END",
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
