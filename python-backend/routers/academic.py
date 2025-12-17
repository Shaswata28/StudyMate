"""
Academic profile router for managing user academic information.
Implements endpoints for creating, retrieving, and updating academic profiles.
"""
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from models.schemas import AcademicProfile, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/academic", tags=["academic"])


@router.get("")
async def get_academic_profile(user: AuthUser = Depends(get_current_user)):
    """
    Get user's academic profile.
    
    Returns the authenticated user's academic information including grade level,
    semester type, current semester, and subjects.
    
    Requirements: 3.1, 3.3, 3.4
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("academic").select("*").eq("id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic profile not found"
            )
        
        logger.info(f"Academic profile retrieved for user: {user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get academic profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve academic profile"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_academic_profile(
    profile: AcademicProfile,
    user: AuthUser = Depends(get_current_user)
):
    """
    Create user's academic profile.
    
    Creates a new academic profile for the authenticated user with grade level,
    semester type, current semester, and subjects. If a profile already exists,
    returns a 409 Conflict error.
    
    Requirements: 3.1, 3.3, 3.4
    """
    try:
        client = get_user_client(user.access_token)
        
        # Check if profile already exists
        existing = client.table("academic").select("id").eq("id", user.id).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Academic profile already exists. Use PUT to update."
            )
        
        # Insert academic profile
        result = client.table("academic").insert({
            "id": user.id,
            "grade": profile.grade,
            "semester_type": profile.semester_type,
            "semester": profile.semester,
            "subject": profile.subject
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create academic profile"
            )
        
        logger.info(f"Academic profile created for user: {user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create academic profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create academic profile"
        )


@router.put("", status_code=status.HTTP_200_OK)
async def update_academic_profile(
    profile: AcademicProfile,
    user: AuthUser = Depends(get_current_user)
):
    """
    Update user's academic profile.
    
    Updates the authenticated user's academic information. If no profile exists,
    returns a 404 Not Found error.
    
    Requirements: 3.1, 3.3, 3.4
    """
    try:
        client = get_user_client(user.access_token)
        
        # Update academic profile
        result = client.table("academic").update({
            "grade": profile.grade,
            "semester_type": profile.semester_type,
            "semester": profile.semester,
            "subject": profile.subject
        }).eq("id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic profile not found"
            )
        
        logger.info(f"Academic profile updated for user: {user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update academic profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update academic profile"
        )
