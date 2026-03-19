"""Conversation and message models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    tool_call_id: str | None = None
    name: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: str | None = Field(None, description="Resume existing conversation")
    stream: bool = Field(False, description="Stream response via SSE")


class ToolCall(BaseModel):
    name: str
    arguments: dict


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    tool_calls_made: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    conversation_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
