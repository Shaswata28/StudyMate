"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal


class Message(BaseModel):
    """
    Represents a single message in the conversation history.
    """
    role: Literal["user", "model"]
    content: str


class FileAttachment(BaseModel):
    """
    Represents a file attachment (image or PDF) sent with a message.
    """
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., pattern=r"^(image/(jpeg|png|gif|webp)|application/pdf)$")
    data: str = Field(..., min_length=1)  # base64 encoded file data
    
    @field_validator('data')
    @classmethod
    def validate_base64_size(cls, v: str) -> str:
        """Validate that base64 data is not too large (max 10MB decoded)."""
        # Rough estimate: base64 is ~1.37x larger than original
        # 10MB * 1.37 ≈ 13.7MB base64
        max_base64_size = 14 * 1024 * 1024  # 14MB to be safe
        if len(v) > max_base64_size:
            raise ValueError("File size exceeds 10MB limit")
        return v


class ChatRequest(BaseModel):
    """
    Request schema for the chat endpoint.
    Validates incoming chat requests with message, optional history, and optional file attachments.
    """
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[Message]] = Field(default_factory=list, max_length=10)
    attachments: Optional[List[FileAttachment]] = Field(default_factory=list, max_length=5)


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
