"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Message(BaseModel):
    """
    Represents a single message in the conversation history.
    """
    role: Literal["user", "model"]
    content: str


class ChatRequest(BaseModel):
    """
    Request schema for the chat endpoint.
    Validates incoming chat requests with message and optional history.
    """
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[Message]] = Field(default_factory=list, max_length=10)


class ChatResponse(BaseModel):
    """
    Response schema for successful chat requests.
    """
    response: str
    timestamp: str


class ErrorResponse(BaseModel):
    """
    Response schema for error cases.
    """
    error: str
    code: str
