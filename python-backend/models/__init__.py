"""
Models package for Pydantic schemas and data validation.
"""

# Import schemas for request/response validation
from .schemas import (
    Message,
    FileAttachment,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
)

# Import database models
from .database import (
    # Academic models
    AcademicBase,
    AcademicCreate,
    AcademicUpdate,
    AcademicResponse,
    # Personalized models
    PersonalizedBase,
    PersonalizedCreate,
    PersonalizedUpdate,
    PersonalizedResponse,
    # Course models
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    # Material models
    MaterialBase,
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    # Chat history models
    ChatMessage,
    ChatHistoryBase,
    ChatHistoryCreate,
    ChatHistoryUpdate,
    ChatHistoryResponse,
)

__all__ = [
    # Request/Response schemas
    'Message',
    'FileAttachment',
    'ChatRequest',
    'ChatResponse',
    'ErrorResponse',
    # Academic models
    'AcademicBase',
    'AcademicCreate',
    'AcademicUpdate',
    'AcademicResponse',
    # Personalized models
    'PersonalizedBase',
    'PersonalizedCreate',
    'PersonalizedUpdate',
    'PersonalizedResponse',
    # Course models
    'CourseBase',
    'CourseCreate',
    'CourseUpdate',
    'CourseResponse',
    # Material models
    'MaterialBase',
    'MaterialCreate',
    'MaterialUpdate',
    'MaterialResponse',
    # Chat history models
    'ChatMessage',
    'ChatHistoryBase',
    'ChatHistoryCreate',
    'ChatHistoryUpdate',
    'ChatHistoryResponse',
]
