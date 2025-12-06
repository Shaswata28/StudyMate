"""
Application constants and enums.

This file contains all constant values used across the application,
ensuring consistency between frontend and backend.
"""

# Academic Profile Constants

# Valid grade levels
VALID_GRADES = ['Bachelor', 'Masters']

# Valid semester types
VALID_SEMESTER_TYPES = ['double', 'tri']

# Valid semester range
MIN_SEMESTER = 1
MAX_SEMESTER = 12

# Valid subjects (must match frontend options)
VALID_SUBJECTS = [
    'computer science',
    'electrical and electronics engineering',
    'english',
    'business administration',
    'economics'
]

# Subject display names (for frontend)
SUBJECT_DISPLAY_NAMES = {
    'computer science': 'CS',
    'electrical and electronics engineering': 'EEE',
    'english': 'English',
    'business administration': 'BA',
    'economics': 'Economics'
}

# User Preferences Constants

# Valid learning pace values
VALID_LEARNING_PACE = ['slow', 'moderate', 'fast']

# Valid prior experience levels
VALID_PRIOR_EXPERIENCE = ['beginner', 'intermediate', 'advanced', 'expert']

# File Upload Constants

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/markdown',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
]

# File extension to MIME type mapping
FILE_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp'
}

# Storage Constants

# Storage bucket name
STORAGE_BUCKET_NAME = 'course-materials'

# Chat History Constants

# Valid chat message roles
VALID_CHAT_ROLES = ['user', 'model', 'assistant']

# Vector embedding dimension (for pgvector)
EMBEDDING_DIMENSION = 384

# Default User Preferences

# Default moderate learning preferences (used when user has no preferences set)
DEFAULT_PREFERENCES = {
    "detail_level": 0.5,
    "example_preference": 0.5,
    "analogy_preference": 0.5,
    "technical_language": 0.5,
    "structure_preference": 0.5,
    "visual_preference": 0.5,
    "learning_pace": "moderate",
    "prior_experience": "intermediate"
}
