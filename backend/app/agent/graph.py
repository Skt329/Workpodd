"""LangGraph agent graph — the core agent loop with tool orchestration."""

import json
import time
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS
from app.agent.prompts import SYSTEM_PROMPT
from app.config import get_settings


def create_llm():
    """Create the Azure OpenAI LLM instance."""
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint.replace("/openai/v1", ""),
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        temperature=0.1,  # Low temperature for consistent policy decisions
        max_tokens=1024,
    )


def create_agent_graph():
    """Build and compile the LangGraph agent graph.

    The graph follows this flow:
    1. agent_node: LLM decides whether to call a tool or respond directly
    2. If tool call → tool_node executes the tool → back to agent_node
    3. If no tool call → END (response is ready)

    This creates a ReAct-style loop: Reason → Act → Observe → Reason → ...
    """
    llm = create_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    async def agent_node(state: AgentState) -> dict:
        """The reasoning node — LLM decides next action."""
        messages = state["messages"]

        # Inject system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response], "step_index": state.get("step_index", 0) + 1}

    def should_continue(state: AgentState) -> str:
        """Route: if the LLM wants to call a tool, go to tool_node; else END."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    # Set entry point
    graph.set_entry_point("agent")

    # Add conditional edge from agent
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})

    # After tools execute, go back to agent for next reasoning step
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled agent graph (singleton)
_agent_graph = None


def get_agent_graph():
    """Get or create the compiled agent graph."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


async def run_agent(
    customer_id: str,
    conversation_id: str,
    messages: list,
    event_callback=None,
) -> dict:
    """Run the agent graph and collect all events.

    Args:
        customer_id: The customer being served
        conversation_id: Unique conversation identifier
        messages: List of LangChain message objects (chat history)
        event_callback: Async callback for real-time event streaming

    Returns:
        dict with 'response' (str) and 'events' (list of event dicts)
    """
    graph = get_agent_graph()
    events = []
    step_index = 0

    initial_state = {
        "messages": messages,
        "customer_id": customer_id,
        "conversation_id": conversation_id,
        "step_index": 0,
    }

    # Stream events from the graph execution
    final_response = ""
    async for event in graph.astream_events(initial_state, version="v2"):
        kind = event.get("event", "")
        data = event.get("data", {})

        if kind == "on_chat_model_start":
            step_index += 1
            ev = {
                "type": "LLM_THINKING",
                "conversation_id": conversation_id,
                "step_index": step_index,
                "timestamp": _now(),
            }
            events.append(ev)
            if event_callback:
                await event_callback(ev)

        elif kind == "on_chat_model_end":
            output = data.get("output")
            if output and hasattr(output, "tool_calls") and output.tool_calls:
                for tc in output.tool_calls:
                    ev = {
                        "type": "TOOL_CALL",
                        "conversation_id": conversation_id,
                        "step_index": step_index,
                        "tool_name": tc.get("name", "unknown"),
                        "input_data": tc.get("args", {}),
                        "timestamp": _now(),
                    }
                    events.append(ev)
                    if event_callback:
                        await event_callback(ev)
            elif output and hasattr(output, "content") and output.content:
                final_response = output.content
                ev = {
                    "type": "AGENT_RESPONSE",
                    "conversation_id": conversation_id,
                    "step_index": step_index,
                    "output_data": {"response": final_response[:200]},
                    "timestamp": _now(),
                }
                events.append(ev)
                if event_callback:
                    await event_callback(ev)

        elif kind == "on_tool_end":
            output = data.get("output", "")
            tool_output = str(output)[:500] if output else ""
            # Try to parse as JSON for structured display
            try:
                parsed = json.loads(tool_output) if tool_output else {}
            except (json.JSONDecodeError, TypeError):
                parsed = {"raw": tool_output}

            ev = {
                "type": "TOOL_RESULT",
                "conversation_id": conversation_id,
                "step_index": step_index,
                "tool_name": event.get("name", "unknown"),
                "output_data": parsed,
                "timestamp": _now(),
            }
            events.append(ev)
            if event_callback:
                await event_callback(ev)

    # Get final response from the last AI message
    if not final_response:
        # Fallback: run without streaming to get final state
        result = await graph.ainvoke(initial_state)
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                final_response = msg.content
                break

    return {
        "response": final_response,
        "events": events,
    }


def _now() -> str:
    """ISO format timestamp."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
