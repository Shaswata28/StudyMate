"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Literal, Any
from datetime import datetime
from constants import (
    VALID_GRADES,
    VALID_SEMESTER_TYPES,
    MIN_SEMESTER,
    MAX_SEMESTER,
    VALID_SUBJECTS,
    VALID_LEARNING_PACE,
    VALID_PRIOR_EXPERIENCE
)


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


class TestAccuracyInfo(BaseModel):
    """
    Schema for test accuracy information when question matches test dataset.
    """
    is_test_question: bool = Field(..., description="Whether this question matched a test dataset entry")
    accuracy: float = Field(..., ge=0, le=100, description="Accuracy percentage (0-100)")
    expected_response: Optional[str] = Field(None, description="Expected response from test dataset (truncated)")


class ChatResponse(BaseModel):
    """
    Response schema for successful chat requests.
    """
    response: str
    timestamp: str
    test_accuracy: Optional[TestAccuracyInfo] = Field(None, description="Accuracy info if question matches test dataset")


class ErrorResponse(BaseModel):
    """
    Response schema for error cases.
    """
    error: str
    code: str


# Database Schemas

class AcademicProfile(BaseModel):
    """
    Schema for academic profile data.
    """
    grade: List[str] = Field(..., description="Grade levels (e.g., ['Bachelor', 'Masters'])")
    semester_type: str = Field(..., description="Semester type: 'double' or 'tri'")
    semester: int = Field(..., ge=MIN_SEMESTER, le=MAX_SEMESTER, description=f"Current semester ({MIN_SEMESTER}-{MAX_SEMESTER})")
    subject: List[str] = Field(default_factory=list, description="List of subjects")
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: List[str]) -> List[str]:
        """Validate that all grades are valid."""
        if not v:
            raise ValueError("At least one grade must be specified")
        invalid_grades = [g for g in v if g not in VALID_GRADES]
        if invalid_grades:
            raise ValueError(f"Invalid grades: {invalid_grades}. Must be one of: {VALID_GRADES}")
        return v
    
    @field_validator('semester_type')
    @classmethod
    def validate_semester_type(cls, v: str) -> str:
        """Validate semester type."""
        if v not in VALID_SEMESTER_TYPES:
            raise ValueError(f"Invalid semester type: {v}. Must be one of: {VALID_SEMESTER_TYPES}")
        return v
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: List[str]) -> List[str]:
        """Validate that all subjects are valid."""
        invalid_subjects = [s for s in v if s not in VALID_SUBJECTS]
        if invalid_subjects:
            raise ValueError(f"Invalid subjects: {invalid_subjects}. Must be one of: {VALID_SUBJECTS}")
        return v


class UserPreferences(BaseModel):
    """
    Schema for user preferences (stored as JSONB).
    """
    detail_level: float = Field(..., ge=0, le=1, description="Detail preference (0-1)")
    example_preference: float = Field(..., ge=0, le=1, description="Example preference (0-1)")
    analogy_preference: float = Field(..., ge=0, le=1, description="Analogy preference (0-1)")
    technical_language: float = Field(..., ge=0, le=1, description="Technical language preference (0-1)")
    structure_preference: float = Field(..., ge=0, le=1, description="Structure preference (0-1)")
    visual_preference: float = Field(..., ge=0, le=1, description="Visual preference (0-1)")
    learning_pace: str = Field(..., description="Learning pace: 'slow', 'moderate', or 'fast'")
    prior_experience: str = Field(..., description="Experience level: 'beginner', 'intermediate', 'advanced', or 'expert'")
    
    @field_validator('learning_pace')
    @classmethod
    def validate_learning_pace(cls, v: str) -> str:
        """Validate learning pace."""
        if v not in VALID_LEARNING_PACE:
            raise ValueError(f"Invalid learning pace: {v}. Must be one of: {VALID_LEARNING_PACE}")
        return v
    
    @field_validator('prior_experience')
    @classmethod
    def validate_prior_experience(cls, v: str) -> str:
        """Validate prior experience level."""
        if v not in VALID_PRIOR_EXPERIENCE:
            raise ValueError(f"Invalid prior experience: {v}. Must be one of: {VALID_PRIOR_EXPERIENCE}")
        return v


class CourseCreate(BaseModel):
    """
    Schema for creating a new course.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Course name")


class CourseResponse(BaseModel):
    """
    Schema for course response.
    """
    id: str
    user_id: str
    name: str
    created_at: str
    updated_at: str


class MaterialCreate(BaseModel):
    """
    Schema for creating a material record (after file upload).
    """
    course_id: str = Field(..., description="Course ID this material belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="File name")
    file_path: str = Field(..., description="Path in storage bucket")
    file_type: str = Field(..., description="MIME type (e.g., 'application/pdf')")
    file_size: int = Field(..., gt=0, description="File size in bytes")


class MaterialResponse(BaseModel):
    """
    Schema for material response.
    """
    id: str
    course_id: str
    name: str
    file_path: str
    file_type: str
    file_size: int
    processing_status: str = "pending"  # pending, processing, completed, failed
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    has_embedding: bool = False  # Computed: embedding IS NOT NULL
    created_at: str
    updated_at: str


# Authentication Schemas

class SignupRequest(BaseModel):
    """
    Request schema for user registration.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100, description="User's password (min 8 characters)")


class LoginRequest(BaseModel):
    """
    Request schema for user login.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, max_length=100, description="User's password")


class AuthResponse(BaseModel):
    """
    Response schema for successful authentication (signup/login).
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: str = Field(..., description="Refresh token for obtaining new access tokens")
    user: dict = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """
    Request schema for refreshing access token.
    """
    refresh_token: str = Field(..., description="Refresh token")


class SessionResponse(BaseModel):
    """
    Response schema for session information.
    """
    user: dict = Field(..., description="User information")
    session: Optional[dict] = Field(None, description="Session information")


class MessageResponse(BaseModel):
    """
    Generic message response.
    """
    message: str = Field(..., description="Response message")


class MaterialSearchResult(BaseModel):
    """
    Schema for semantic search result.
    """
    material_id: str = Field(..., description="Material UUID")
    name: str = Field(..., description="Material filename")
    excerpt: str = Field(..., description="Relevant text excerpt")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1, higher is more relevant)")
    file_type: str = Field(..., description="MIME type")


class MaterialSearchRequest(BaseModel):
    """
    Schema for semantic search request.
    """
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=3, ge=1, le=10, description="Maximum number of results")


# Context Service Schemas

class AcademicInfo(BaseModel):
    """
    User academic information from academic table.
    Used for context-aware chat responses.
    """
    grade: List[str] = Field(..., description="Grade levels (e.g., ['Bachelor', 'Masters'])")
    semester_type: str = Field(..., description="Semester type: 'double' or 'tri'")
    semester: int = Field(..., description="Current semester number")
    subject: List[str] = Field(default_factory=list, description="List of subjects")


class UserContext(BaseModel):
    """
    Complete user context for AI chat.
    Aggregates preferences, academic info, and chat history.
    """
    preferences: Optional[UserPreferences] = None
    academic: Optional[AcademicInfo] = None
    chat_history: List[Message] = Field(default_factory=list)
    has_preferences: bool = False
    has_academic: bool = False
    has_history: bool = False


# RAG Operation Schemas

class RAGOperationResult(BaseModel):
    """
    Result of a RAG operation with detailed status.
    Used for tracking and debugging RAG pipeline operations.
    """
    success: bool = Field(..., description="Whether the operation succeeded")
    operation: str = Field(..., description="Operation type (e.g., 'material_search', 'chat_history', 'context_format')")
    data: Optional[Any] = Field(None, description="Operation result data")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")
    execution_time: float = Field(..., ge=0, description="Operation execution time in seconds")
    timestamp: str = Field(..., description="ISO timestamp when operation completed")


class EnhancedMaterialSearchResult(BaseModel):
    """
    Enhanced search result with additional metadata for better RAG operations.
    Extends MaterialSearchResult with processing and debugging information.
    """
    material_id: str = Field(..., description="Material UUID")
    name: str = Field(..., description="Material filename")
    excerpt: str = Field(..., description="Relevant text excerpt")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1, higher is more relevant)")
    file_type: str = Field(..., description="MIME type")
    processing_status: str = Field(..., description="Material processing status (pending, processing, completed, failed)")
    processed_at: Optional[str] = Field(None, description="ISO timestamp when material was processed")
    excerpt_length: int = Field(..., ge=0, description="Length of excerpt in characters (for prompt optimization)")


class RAGContext(BaseModel):
    """
    Complete RAG context with operation results.
    Tracks the entire RAG pipeline execution for debugging and monitoring.
    """
    user_context: UserContext = Field(..., description="Base user context (preferences, academic, history)")
    material_search_result: RAGOperationResult = Field(..., description="Result of material search operation")
    chat_history_result: RAGOperationResult = Field(..., description="Result of chat history retrieval operation")
    prompt_format_result: RAGOperationResult = Field(..., description="Result of prompt formatting operation")
    total_execution_time: float = Field(..., ge=0, description="Total RAG pipeline execution time in seconds")
