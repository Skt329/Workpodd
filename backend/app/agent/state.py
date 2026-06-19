"""Agent state schema for LangGraph."""

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State that flows through the LangGraph agent graph.

    Attributes:
        messages: Chat history with LLM (user + assistant + tool messages)
        customer_id: Currently identified customer's ID
        conversation_id: Unique ID for this conversation session
        step_index: Counter for reasoning steps (for event logging)
    """
    messages: Annotated[list[BaseMessage], add_messages]
    customer_id: str
    conversation_id: str
    step_index: int
