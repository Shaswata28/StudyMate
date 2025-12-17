"""
Pydantic models for Supabase database schema.
These models match the SQL schema definitions in migrations/002_create_tables.sql
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# Academic Table Models
# ============================================================================

class AcademicBase(BaseModel):
    """Base model for academic profile data."""
    grade: List[str] = Field(..., description="Array of degree levels (Bachelor, Masters)")
    semester_type: str = Field(..., description="Semester system type (double or tri)")
    semester: int = Field(..., ge=1, le=12, description="Current semester number (1-12)")
    subject: List[str] = Field(default_factory=list, description="Array of subjects")
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: List[str]) -> List[str]:
        """Validate that grade array contains only valid values."""
        valid_grades = {'Bachelor', 'Masters'}
        if not v:
            raise ValueError("Grade array cannot be empty")
        for grade in v:
            if grade not in valid_grades:
                raise ValueError(f"Invalid grade: {grade}. Must be one of {valid_grades}")
        return v
    
    @field_validator('semester_type')
    @classmethod
    def validate_semester_type(cls, v: str) -> str:
        """Validate semester type is either 'double' or 'tri'."""
        if v not in ('double', 'tri'):
            raise ValueError("semester_type must be 'double' or 'tri'")
        return v


class AcademicCreate(AcademicBase):
    """Model for creating a new academic profile."""
    pass


class AcademicUpdate(BaseModel):
    """Model for updating an academic profile (all fields optional)."""
    grade: Optional[List[str]] = None
    semester_type: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=12)
    subject: Optional[List[str]] = None
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate that grade array contains only valid values."""
        if v is not None:
            valid_grades = {'Bachelor', 'Masters'}
            if not v:
                raise ValueError("Grade array cannot be empty")
            for grade in v:
                if grade not in valid_grades:
                    raise ValueError(f"Invalid grade: {grade}. Must be one of {valid_grades}")
        return v
    
    @field_validator('semester_type')
    @classmethod
    def validate_semester_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate semester type is either 'double' or 'tri'."""
        if v is not None and v not in ('double', 'tri'):
            raise ValueError("semester_type must be 'double' or 'tri'")
        return v


class AcademicResponse(AcademicBase):
    """Model for academic profile responses."""
    id: UUID = Field(..., description="User ID (references auth.users)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Personalized Table Models
# ============================================================================

class PersonalizedBase(BaseModel):
    """Base model for personalized preferences."""
    prefs: Dict[str, Any] = Field(default_factory=dict, description="JSONB preferences object")


class PersonalizedCreate(PersonalizedBase):
    """Model for creating personalized preferences."""
    pass


class PersonalizedUpdate(BaseModel):
    """Model for updating personalized preferences."""
    prefs: Dict[str, Any] = Field(..., description="JSONB preferences object to update")


class PersonalizedResponse(PersonalizedBase):
    """Model for personalized preferences responses."""
    id: UUID = Field(..., description="User ID (references auth.users)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Courses Table Models
# ============================================================================

class CourseBase(BaseModel):
    """Base model for course data."""
    name: str = Field(..., min_length=1, max_length=255, description="Course name")


class CourseCreate(CourseBase):
    """Model for creating a new course."""
    pass


class CourseUpdate(BaseModel):
    """Model for updating a course."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Course name")


class CourseResponse(CourseBase):
    """Model for course responses."""
    id: UUID = Field(..., description="Course unique identifier")
    user_id: UUID = Field(..., description="Course owner (references auth.users)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Materials Table Models
# ============================================================================

class MaterialBase(BaseModel):
    """Base model for material data."""
    name: str = Field(..., min_length=1, max_length=255, description="Material filename")


class MaterialCreate(MaterialBase):
    """Model for creating a new material."""
    course_id: UUID = Field(..., description="Parent course ID")
    storage_object_id: Optional[UUID] = Field(None, description="Supabase Storage object ID")


class MaterialUpdate(BaseModel):
    """Model for updating a material."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Material filename")
    storage_object_id: Optional[UUID] = Field(None, description="Supabase Storage object ID")


class MaterialResponse(MaterialBase):
    """Model for material responses."""
    id: UUID = Field(..., description="Material unique identifier")
    course_id: UUID = Field(..., description="Parent course ID")
    storage_object_id: Optional[UUID] = Field(None, description="Supabase Storage object ID")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Chat History Table Models
# ============================================================================

class ChatMessage(BaseModel):
    """Model for a single chat message in the history array."""
    role: str = Field(..., description="Message role (user or model)")
    content: str = Field(..., min_length=1, description="Message content")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is either 'user' or 'model'."""
        if v not in ('user', 'model'):
            raise ValueError("role must be 'user' or 'model'")
        return v


class ChatHistoryBase(BaseModel):
    """Base model for chat history data."""
    history: List[Dict[str, Any]] = Field(default_factory=list, description="JSONB array of messages")


class ChatHistoryCreate(ChatHistoryBase):
    """Model for creating a new chat history record."""
    course_id: UUID = Field(..., description="Parent course ID")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (384 dimensions)")
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate that embedding has exactly 384 dimensions if provided."""
        if v is not None and len(v) != 384:
            raise ValueError("Embedding must have exactly 384 dimensions")
        return v


class ChatHistoryUpdate(BaseModel):
    """Model for updating chat history."""
    history: Optional[List[Dict[str, Any]]] = Field(None, description="JSONB array of messages")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (384 dimensions)")
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate that embedding has exactly 384 dimensions if provided."""
        if v is not None and len(v) != 384:
            raise ValueError("Embedding must have exactly 384 dimensions")
        return v


class ChatHistoryResponse(ChatHistoryBase):
    """Model for chat history responses."""
    id: UUID = Field(..., description="Chat history unique identifier")
    course_id: UUID = Field(..., description="Parent course ID")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (384 dimensions)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Export all models
# ============================================================================

__all__ = [
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
