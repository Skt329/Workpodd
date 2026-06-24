"""LangGraph agent graph — the core agent loop with tool orchestration.

Security: Each session creates a graph with customer-scoped tools.
The LLM cannot access data belonging to other customers.
"""

import json
from datetime import datetime
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.tools import create_scoped_tools
from app.config import get_settings


def _create_llm():
    """Create the Azure OpenAI LLM instance."""
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint.replace("/openai/v1", ""),
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        temperature=0.1,
        max_tokens=1024,
        streaming=True,  # Enable streaming for token-by-token output
    )


_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = _create_llm()
    return _llm


def create_session_graph(customer_id: str):
    """Build and compile a LangGraph agent graph scoped to a customer session."""
    llm = _get_llm()
    scoped_tools = create_scoped_tools(customer_id)
    llm_with_tools = llm.bind_tools(scoped_tools)

    async def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response], "step_index": state.get("step_index", 0) + 1}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(scoped_tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


_session_graphs: dict[str, object] = {}


def get_session_graph(customer_id: str):
    if customer_id not in _session_graphs:
        _session_graphs[customer_id] = create_session_graph(customer_id)
    return _session_graphs[customer_id]


def _now() -> str:
    return datetime.utcnow().isoformat()


async def run_agent(
    customer_id: str,
    conversation_id: str,
    messages: list,
    event_callback=None,
    token_callback=None,
) -> dict:
    """Run the agent graph and collect all events.

    Args:
        customer_id: The customer being served (used for tool scoping)
        conversation_id: Unique conversation identifier
        messages: List of LangChain message objects (chat history)
        event_callback: Async callback for admin event streaming
        token_callback: Async callback for streaming response tokens to the customer
    """
    import asyncio

    graph = get_session_graph(customer_id)
    events = []
    step_index = 0

    initial_state = {
        "messages": messages,
        "customer_id": customer_id,
        "conversation_id": conversation_id,
        "step_index": 0,
    }

    final_response = ""
    is_streaming_final = False

    async def _run():
        nonlocal final_response, is_streaming_final, step_index

        async for event in graph.astream_events(initial_state, version="v2"):
            kind = event.get("event", "")
            data = event.get("data", {})

            if kind == "on_chat_model_start":
                step_index += 1
                is_streaming_final = False
                ev = {
                    "type": "LLM_THINKING",
                    "conversation_id": conversation_id,
                    "customer_id": customer_id,
                    "step_index": step_index,
                    "timestamp": _now(),
                }
                events.append(ev)
                if event_callback:
                    await event_callback(ev)

            elif kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if not (hasattr(chunk, "tool_calls") and chunk.tool_calls):
                        is_streaming_final = True
                        if token_callback:
                            await token_callback(chunk.content)

            elif kind == "on_chat_model_end":
                output = data.get("output")
                if output and hasattr(output, "tool_calls") and output.tool_calls:
                    is_streaming_final = False
                    for tc in output.tool_calls:
                        ev = {
                            "type": "TOOL_CALL",
                            "conversation_id": conversation_id,
                            "customer_id": customer_id,
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
                        "customer_id": customer_id,
                        "step_index": step_index,
                        "output_data": {"response": final_response[:300]},
                        "timestamp": _now(),
                    }
                    events.append(ev)
                    if event_callback:
                        await event_callback(ev)

            elif kind == "on_tool_end":
                output = data.get("output", "")
                tool_output = str(output)[:500] if output else ""
                try:
                    parsed = json.loads(tool_output) if tool_output else {}
                except (json.JSONDecodeError, TypeError):
                    parsed = {"raw": tool_output}

                ev = {
                    "type": "TOOL_RESULT",
                    "conversation_id": conversation_id,
                    "customer_id": customer_id,
                    "step_index": step_index,
                    "tool_name": event.get("name", "unknown"),
                    "output_data": parsed,
                    "timestamp": _now(),
                }
                events.append(ev)
                if event_callback:
                    await event_callback(ev)

    try:
        # Timeout after 90 seconds to prevent indefinite hangs
        await asyncio.wait_for(_run(), timeout=90.0)
    except asyncio.TimeoutError:
        print(f"[ERROR] Agent timed out for customer {customer_id}")
        ev = {
            "type": "AGENT_ERROR",
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "step_index": step_index,
            "output_data": {"error": "Agent response timed out after 90 seconds"},
            "timestamp": _now(),
        }
        events.append(ev)
        if event_callback:
            await event_callback(ev)
    except Exception as e:
        print(f"[ERROR] Agent error for customer {customer_id}: {e}")
        ev = {
            "type": "AGENT_ERROR",
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "step_index": step_index,
            "output_data": {"error": str(e)[:500]},
            "timestamp": _now(),
        }
        events.append(ev)
        if event_callback:
            await event_callback(ev)

    return {
        "response": final_response or "I apologize, but I encountered a technical issue. Please try again.",
        "events": events,
    }

