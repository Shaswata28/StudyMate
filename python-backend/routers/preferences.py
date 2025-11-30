"""
Preferences router for managing user learning preferences.
Implements endpoints for creating, retrieving, and updating personalized preferences.
"""
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from models.schemas import UserPreferences, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("")
async def get_preferences(user: AuthUser = Depends(get_current_user)):
    """
    Get user's learning preferences.
    
    Returns the authenticated user's personalized learning preferences stored
    as JSONB, including detail level, learning pace, prior experience, and
    various preference sliders.
    
    Requirements: 4.1, 4.2, 4.3
    """
    try:
        client = get_user_client(user.access_token)
        
        result = client.table("personalized").select("*").eq("id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found"
            )
        
        logger.info(f"Preferences retrieved for user: {user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_preferences(
    preferences: UserPreferences,
    user: AuthUser = Depends(get_current_user)
):
    """
    Create user's learning preferences.
    
    Creates a new preferences record for the authenticated user with all
    personalization settings stored as JSONB. If preferences already exist,
    returns a 409 Conflict error.
    
    Requirements: 4.1, 4.2, 4.3
    """
    try:
        client = get_user_client(user.access_token)
        
        # Check if preferences already exist
        existing = client.table("personalized").select("id").eq("id", user.id).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Preferences already exist. Use PUT to update."
            )
        
        # Convert preferences to dict for JSONB storage
        prefs_dict = preferences.model_dump()
        
        # Insert preferences
        result = client.table("personalized").insert({
            "id": user.id,
            "prefs": prefs_dict
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create preferences"
            )
        
        logger.info(f"Preferences created for user: {user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create preferences"
        )


@router.put("", status_code=status.HTTP_200_OK)
async def update_preferences(
    preferences: UserPreferences,
    user: AuthUser = Depends(get_current_user)
):
    """
    Update user's learning preferences.
    
    Updates the authenticated user's personalized learning preferences.
    The JSONB structure allows flexible updates without schema changes.
    If no preferences exist, returns a 404 Not Found error.
    
    Requirements: 4.1, 4.2, 4.3
    """
    try:
        client = get_user_client(user.access_token)
        
        # Convert preferences to dict for JSONB storage
        prefs_dict = preferences.model_dump()
        
        # Update preferences
        result = client.table("personalized").update({
            "prefs": prefs_dict
        }).eq("id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found"
            )
        
        logger.info(f"Preferences updated for user: {user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )
