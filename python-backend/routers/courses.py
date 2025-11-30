"""
Course management router for CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging

from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from models.schemas import CourseCreate, CourseResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreate,
    user: AuthUser = Depends(get_current_user)
):
    """
    Create a new course.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("courses").insert({
            "user_id": user.id,
            "name": course.name
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create course"
            )
        
        course_data = result.data[0]
        logger.info(f"Course created: {course_data['id']} for user: {user.id}")
        
        return CourseResponse(
            id=course_data["id"],
            user_id=course_data["user_id"],
            name=course_data["name"],
            created_at=course_data["created_at"],
            updated_at=course_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )


@router.get("", response_model=List[CourseResponse])
async def list_courses(user: AuthUser = Depends(get_current_user)):
    """
    List all courses for the authenticated user.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("courses").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        
        courses = [
            CourseResponse(
                id=c["id"],
                user_id=c["user_id"],
                name=c["name"],
                created_at=c["created_at"],
                updated_at=c["updated_at"]
            )
            for c in result.data
        ]
        
        return courses
        
    except Exception as e:
        logger.error(f"Failed to list courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve courses"
        )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Get a specific course by ID.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("courses").select("*").eq("id", course_id).eq("user_id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        course_data = result.data[0]
        return CourseResponse(
            id=course_data["id"],
            user_id=course_data["user_id"],
            name=course_data["name"],
            created_at=course_data["created_at"],
            updated_at=course_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve course"
        )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course: CourseCreate,
    user: AuthUser = Depends(get_current_user)
):
    """
    Update a course name.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("courses").update({
            "name": course.name
        }).eq("id", course_id).eq("user_id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        course_data = result.data[0]
        logger.info(f"Course updated: {course_id}")
        
        return CourseResponse(
            id=course_data["id"],
            user_id=course_data["user_id"],
            name=course_data["name"],
            created_at=course_data["created_at"],
            updated_at=course_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )


@router.delete("/{course_id}", response_model=MessageResponse)
async def delete_course(
    course_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Delete a course and all associated materials and chat history.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("courses").delete().eq("id", course_id).eq("user_id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        logger.info(f"Course deleted: {course_id}")
        return MessageResponse(message="Course deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )
