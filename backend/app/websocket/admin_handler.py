"""Admin WebSocket handler — streams agent reasoning events in real-time."""

import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from app.websocket.manager import manager


async def admin_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for the admin dashboard.

    URL: /ws/admin

    This is a receive-only connection for the admin. All agent reasoning
    events are broadcast to this channel by the chat handler.

    Outgoing messages (all agent events):
        - { "type": "CONVERSATION_START", ... }
        - { "type": "USER_MESSAGE", ... }
        - { "type": "LLM_THINKING", ... }
        - { "type": "TOOL_CALL", "tool_name": "...", "input_data": {...} }
        - { "type": "TOOL_RESULT", "tool_name": "...", "output_data": {...} }
        - { "type": "AGENT_RESPONSE", ... }
        - { "type": "DECISION", ... }
        - { "type": "ERROR", ... }
        - { "type": "CONVERSATION_END", ... }
    """
    await manager.connect(websocket, "admin")

    # Send initial connection confirmation
    await manager.send_personal(websocket, {
        "type": "admin_connected",
        "message": "Connected to admin event stream",
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            # Keep the connection alive; admin doesn't send messages typically
            # but we handle pings/keep-alive here
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket, "admin")
