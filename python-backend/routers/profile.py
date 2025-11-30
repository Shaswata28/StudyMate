"""
User profile router for academic and preference management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging

from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from models.schemas import AcademicProfile, UserPreferences, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post("/academic", status_code=status.HTTP_200_OK)
async def upsert_academic_profile(
    profile: AcademicProfile,
    user: AuthUser = Depends(get_current_user)
):
    """
    Create or update user's academic profile.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Upsert academic profile
        result = client.table("academic").upsert({
            "id": user.id,
            "grade": profile.grade,
            "semester_type": profile.semester_type,
            "semester": profile.semester,
            "subject": profile.subject
        }).execute()
        
        logger.info(f"Academic profile updated for user: {user.id}")
        return MessageResponse(message="Academic profile saved successfully")
        
    except Exception as e:
        logger.error(f"Failed to save academic profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save academic profile"
        )


@router.get("/academic")
async def get_academic_profile(user: AuthUser = Depends(get_current_user)):
    """
    Get user's academic profile.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("academic").select("*").eq("id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic profile not found"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get academic profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve academic profile"
        )


@router.post("/preferences", status_code=status.HTTP_200_OK)
async def upsert_preferences(
    preferences: UserPreferences,
    user: AuthUser = Depends(get_current_user)
):
    """
    Create or update user's learning preferences.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Convert preferences to dict for JSONB storage
        prefs_dict = preferences.model_dump()
        
        # Upsert preferences
        result = client.table("personalized").upsert({
            "id": user.id,
            "prefs": prefs_dict
        }).execute()
        
        logger.info(f"Preferences updated for user: {user.id}")
        return MessageResponse(message="Preferences saved successfully")
        
    except Exception as e:
        logger.error(f"Failed to save preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save preferences"
        )


@router.get("/preferences")
async def get_preferences(user: AuthUser = Depends(get_current_user)):
    """
    Get user's learning preferences.
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("personalized").select("*").eq("id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )
