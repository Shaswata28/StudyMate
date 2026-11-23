from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SubjectProfile = Literal["general", "stem", "life_sciences", "humanities"]


class AcademicProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    grade: str = Field("", max_length=80)
    subject: str = Field("", max_length=100)


class LocalProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    academic: AcademicProfile = Field(default_factory=AcademicProfile)
    avatar: str | None = Field(None, max_length=400_000, pattern=r"^data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/]+={0,2}$")
    institution: str = Field("", max_length=120)
    goal: str = Field("", max_length=240)
    terms_accepted: bool = False


class UserPreferences(BaseModel):
    detail_level: float = Field(0.5, ge=0.0, le=1.0)
    example_preference: float = Field(0.5, ge=0.0, le=1.0)
    analogy_preference: float = Field(0.5, ge=0.0, le=1.0)
    technical_language: float = Field(0.5, ge=0.0, le=1.0)
    structure_preference: float = Field(0.5, ge=0.0, le=1.0)
    learning_pace: str | None = "moderate"
    prior_experience: str | None = "intermediate"


class CourseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    color: str = Field("#FEAE01", pattern=r"^#[0-9a-fA-F]{6}$")
    subject_profile: SubjectProfile = "general"


class CourseResponse(CourseCreate):
    id: str
    created_at: str


class MaterialResponse(BaseModel):
    id: str
    course_id: str
    name: str
    file_type: str
    file_size: int
    processing_status: str = "completed"
    processing_error: str | None = None
    created_at: str


class FileAttachment(BaseModel):
    filename: str
    mime_type: str
    data: str = Field(max_length=8_000_000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=4000)
    material_id: str | None = None
    attachments: list[FileAttachment] = Field(default_factory=list, max_length=1)


class ChatResponse(BaseModel):
    id: int
    response: str
    timestamp: str
