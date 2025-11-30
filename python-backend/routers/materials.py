"""
Materials management router for file upload/download operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
import logging
import io

from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from models.schemas import MaterialCreate, MaterialResponse, MessageResponse
from constants import MAX_FILE_SIZE, ALLOWED_MIME_TYPES, STORAGE_BUCKET_NAME

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["materials"])


@router.post("/courses/{course_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    course_id: str,
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user)
):
    """
    Upload a material file to a course.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Verify course ownership
        course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
        if not course_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024)}MB limit"
            )
        
        # Upload to storage: {user_id}/{course_id}/{filename}
        file_path = f"{user.id}/{course_id}/{file.filename}"
        
        storage_result = client.storage.from_(STORAGE_BUCKET_NAME).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Create material record in database
        material_result = client.table("materials").insert({
            "course_id": course_id,
            "name": file.filename,
            "file_path": file_path,
            "file_type": file.content_type,
            "file_size": file_size
        }).execute()
        
        if not material_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create material record"
            )
        
        material_data = material_result.data[0]
        logger.info(f"Material uploaded: {material_data['id']} for course: {course_id}")
        
        return MaterialResponse(
            id=material_data["id"],
            course_id=material_data["course_id"],
            name=material_data["name"],
            file_path=material_data["file_path"],
            file_type=material_data["file_type"],
            file_size=material_data["file_size"],
            created_at=material_data["created_at"],
            updated_at=material_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload material: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload material: {str(e)}"
        )


@router.get("/courses/{course_id}/materials", response_model=List[MaterialResponse])
async def list_materials(
    course_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    List all materials for a course.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Verify course ownership
        course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
        if not course_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        result = client.table("materials").select("*").eq("course_id", course_id).order("created_at", desc=True).execute()
        
        materials = [
            MaterialResponse(
                id=m["id"],
                course_id=m["course_id"],
                name=m["name"],
                file_path=m["file_path"],
                file_type=m["file_type"],
                file_size=m["file_size"],
                created_at=m["created_at"],
                updated_at=m["updated_at"]
            )
            for m in result.data
        ]
        
        return materials
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list materials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve materials"
        )


@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Get material metadata.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Get material with course ownership check
        result = client.table("materials").select("*, courses!inner(user_id)").eq("id", material_id).execute()
        
        if not result.data or result.data[0]["courses"]["user_id"] != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )
        
        material_data = result.data[0]
        return MaterialResponse(
            id=material_data["id"],
            course_id=material_data["course_id"],
            name=material_data["name"],
            file_path=material_data["file_path"],
            file_type=material_data["file_type"],
            file_size=material_data["file_size"],
            created_at=material_data["created_at"],
            updated_at=material_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get material: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve material"
        )


@router.get("/materials/{material_id}/download")
async def download_material(
    material_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Download a material file.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Get material with course ownership check
        result = client.table("materials").select("*, courses!inner(user_id)").eq("id", material_id).execute()
        
        if not result.data or result.data[0]["courses"]["user_id"] != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )
        
        material_data = result.data[0]
        file_path = material_data["file_path"]
        
        # Download from storage
        file_data = client.storage.from_(STORAGE_BUCKET_NAME).download(file_path)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=material_data["file_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{material_data["name"]}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download material: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download material"
        )


@router.delete("/materials/{material_id}", response_model=MessageResponse)
async def delete_material(
    material_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Delete a material and its file from storage.
    """
    try:
        client = get_user_client(user.access_token)
        
        # Get material with course ownership check
        result = client.table("materials").select("*, courses!inner(user_id)").eq("id", material_id).execute()
        
        if not result.data or result.data[0]["courses"]["user_id"] != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )
        
        material_data = result.data[0]
        file_path = material_data["file_path"]
        
        # Delete from storage
        client.storage.from_(STORAGE_BUCKET_NAME).remove([file_path])
        
        # Delete from database
        client.table("materials").delete().eq("id", material_id).execute()
        
        logger.info(f"Material deleted: {material_id}")
        return MessageResponse(message="Material deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete material: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete material"
        )
