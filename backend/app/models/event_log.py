"""Agent reasoning event log ORM model."""

import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventType(str, enum.Enum):
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    LLM_THINKING = "LLM_THINKING"
    DECISION = "DECISION"
    ERROR = "ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    SECURITY_WARNING = "SECURITY_WARNING"
    RETRY = "RETRY"
    CONVERSATION_START = "CONVERSATION_START"
    CONVERSATION_END = "CONVERSATION_END"
    USER_MESSAGE = "USER_MESSAGE"
    AGENT_RESPONSE = "AGENT_RESPONSE"


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
