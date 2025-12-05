"""
Material Processing Service for OCR and embedding generation.

This service handles the background processing of uploaded materials:
1. Extract text from PDFs and images using AI Brain OCR
2. Generate semantic embeddings using AI Brain embedding service
3. Track processing status (pending → processing → completed/failed)
4. Handle errors and timeouts gracefully
5. Semantic search across course materials using vector similarity
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import asyncio

from services.ai_brain_client import AIBrainClient, AIBrainClientError
from services.supabase_client import supabase_admin
from constants import STORAGE_BUCKET_NAME

logger = logging.getLogger(__name__)


class MaterialProcessingError(Exception):
    """Base exception raised for material processing errors."""
    pass


class MaterialNotFoundError(MaterialProcessingError):
    """Exception raised when material is not found in database."""
    pass


class StorageDownloadError(MaterialProcessingError):
    """Exception raised when file download from storage fails."""
    pass


class OCRProcessingError(MaterialProcessingError):
    """Exception raised when OCR text extraction fails."""
    pass


class EmbeddingGenerationError(MaterialProcessingError):
    """Exception raised when embedding generation fails."""
    pass


class DatabaseUpdateError(MaterialProcessingError):
    """Exception raised when database update fails."""
    pass


class MaterialProcessingService:
    """
    Service for processing uploaded materials with OCR and embedding generation.
    
    This service orchestrates the complete material processing workflow:
    - Downloads files from Supabase Storage
    - Extracts text using AI Brain OCR
    - Generates embeddings using AI Brain embedding service
    - Updates database with results and status
    """
    
    def __init__(
        self,
        ai_brain_client: AIBrainClient,
        timeout: float = 300.0
    ):
        """
        Initialize the material processing service.
        
        Args:
            ai_brain_client: Client for AI Brain service communication
            timeout: Processing timeout in seconds (default: 300 = 5 minutes)
        """
        self.ai_brain = ai_brain_client
        self.timeout = timeout
        
        logger.info(f"Material processing service initialized (timeout: {timeout}s)")
    
    async def process_material(self, material_id: str) -> None:
        """
        Process a material: extract text and generate embedding.
        
        This is the main processing workflow that:
        1. Updates status to 'processing'
        2. Downloads file from Supabase storage
        3. Extracts text using AI Brain OCR
        4. Generates embedding using AI Brain (if text is not empty)
        5. Updates database with results
        6. Updates status to 'completed' or 'failed'
        
        Args:
            material_id: UUID of the material to process
            
        Raises:
            MaterialProcessingError: If processing fails
        """
        processing_start_time = datetime.now(timezone.utc)
        logger.info(f"=" * 60)
        logger.info(f"Starting material processing: {material_id}")
        logger.info(f"Start time: {processing_start_time.isoformat()}")
        logger.info(f"=" * 60)
        
        try:
            # Update status to processing
            await self._update_status(material_id, "processing")
            logger.info(f"Material {material_id}: Status updated to 'processing'")
            
            # Get material record
            try:
                material = await self._get_material(material_id)
                if not material:
                    raise MaterialNotFoundError(f"Material not found: {material_id}")
                
                logger.info(
                    f"Material {material_id}: Retrieved metadata - "
                    f"Name: {material.get('name', 'unknown')}, "
                    f"Type: {material.get('file_type', 'unknown')}, "
                    f"Size: {material.get('file_size', 0)} bytes"
                )
            except MaterialNotFoundError:
                raise
            except Exception as e:
                raise DatabaseUpdateError(f"Failed to retrieve material: {e}") from e
            
            # Download file from storage
            try:
                logger.info(f"Material {material_id}: Downloading file from storage: {material['file_path']}")
                file_data = await self._download_file(material["file_path"])
                logger.info(f"Material {material_id}: File downloaded successfully ({len(file_data)} bytes)")
            except Exception as e:
                raise StorageDownloadError(f"Failed to download file: {e}") from e
            
            # Extract text using AI Brain with timeout
            try:
                logger.info(f"Material {material_id}: Starting OCR text extraction (timeout: {self.timeout}s)")
                ocr_start_time = datetime.now(timezone.utc)
                
                extracted_text = await asyncio.wait_for(
                    self.ai_brain.extract_text(
                        file_data=file_data,
                        filename=material["name"],
                        retry_on_failure=True
                    ),
                    timeout=self.timeout
                )
                
                ocr_duration = (datetime.now(timezone.utc) - ocr_start_time).total_seconds()
                logger.info(
                    f"Material {material_id}: OCR completed in {ocr_duration:.2f}s - "
                    f"Extracted {len(extracted_text)} characters"
                )
                
            except asyncio.TimeoutError:
                error_msg = f"OCR processing timeout after {self.timeout}s"
                logger.error(f"Material {material_id}: {error_msg}")
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                return
            except AIBrainClientError as e:
                error_msg = f"OCR processing failed: {str(e)}"
                logger.error(f"Material {material_id}: {error_msg}")
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                return
            
            # Generate embedding if text is not empty
            embedding = None
            if extracted_text and extracted_text.strip():
                try:
                    logger.info(f"Material {material_id}: Starting embedding generation (timeout: {self.timeout}s)")
                    embed_start_time = datetime.now(timezone.utc)
                    
                    embedding = await asyncio.wait_for(
                        self.ai_brain.generate_embedding(extracted_text, retry_on_failure=True),
                        timeout=self.timeout
                    )
                    
                    embed_duration = (datetime.now(timezone.utc) - embed_start_time).total_seconds()
                    logger.info(
                        f"Material {material_id}: Embedding generated in {embed_duration:.2f}s - "
                        f"Dimensions: {len(embedding)}"
                    )
                    
                except asyncio.TimeoutError:
                    error_msg = f"Embedding generation timeout after {self.timeout}s"
                    logger.error(f"Material {material_id}: {error_msg}")
                    await self._update_status(
                        material_id=material_id,
                        status="failed",
                        error_message=error_msg
                    )
                    return
                except AIBrainClientError as e:
                    error_msg = f"Embedding generation failed: {str(e)}"
                    logger.error(f"Material {material_id}: {error_msg}")
                    await self._update_status(
                        material_id=material_id,
                        status="failed",
                        error_message=error_msg
                    )
                    return
            else:
                logger.info(
                    f"Material {material_id}: No text extracted (empty or whitespace only), "
                    f"skipping embedding generation"
                )
            
            # Update database with results
            try:
                logger.info(f"Material {material_id}: Updating database with processing results")
                await self._update_material_data(
                    material_id=material_id,
                    extracted_text=extracted_text,
                    embedding=embedding,
                    status="completed"
                )
            except Exception as e:
                raise DatabaseUpdateError(f"Failed to update material data: {e}") from e
            
            processing_duration = (datetime.now(timezone.utc) - processing_start_time).total_seconds()
            logger.info(f"=" * 60)
            logger.info(
                f"Material processing completed successfully: {material_id} "
                f"(Total time: {processing_duration:.2f}s)"
            )
            logger.info(f"=" * 60)
            
        except MaterialNotFoundError as e:
            error_msg = f"Material not found: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}")
            # Don't update status - material doesn't exist
            
        except StorageDownloadError as e:
            error_msg = f"Storage download error: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            await self._update_status(
                material_id=material_id,
                status="failed",
                error_message=error_msg
            )
            
        except DatabaseUpdateError as e:
            error_msg = f"Database update error: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            await self._update_status(
                material_id=material_id,
                status="failed",
                error_message=error_msg
            )
            
        except AIBrainClientError as e:
            # AI Brain service errors (should be caught above, but just in case)
            error_msg = f"AI Brain service error: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            await self._update_status(
                material_id=material_id,
                status="failed",
                error_message=error_msg
            )
            
        except Exception as e:
            # Unexpected errors
            error_msg = f"Unexpected processing error: {type(e).__name__}: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            await self._update_status(
                material_id=material_id,
                status="failed",
                error_message=error_msg
            )
        
        finally:
            processing_duration = (datetime.now(timezone.utc) - processing_start_time).total_seconds()
            logger.info(
                f"Material {material_id}: Processing finished "
                f"(Total time: {processing_duration:.2f}s)"
            )
    
    async def _get_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve material record from database.
        
        Args:
            material_id: UUID of the material
            
        Returns:
            Material record as dictionary, or None if not found
        """
        try:
            result = supabase_admin.table("materials").select("*").eq("id", material_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                logger.warning(f"Material not found: {material_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve material {material_id}: {e}")
            raise MaterialProcessingError(f"Database error: {e}") from e
    
    async def _download_file(self, file_path: str) -> bytes:
        """
        Download file from Supabase Storage with retry logic.
        
        Args:
            file_path: Path to file in storage bucket
            
        Returns:
            File content as bytes
            
        Raises:
            StorageDownloadError: If download fails after retries
        """
        from config import config
        
        last_error = None
        max_attempts = config.MAX_RETRY_ATTEMPTS
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Downloading file from storage: {file_path} [Attempt {attempt}/{max_attempts}]")
                
                file_data = supabase_admin.storage.from_(STORAGE_BUCKET_NAME).download(file_path)
                
                logger.info(f"File downloaded successfully: {len(file_data)} bytes [Attempt {attempt}/{max_attempts}]")
                return file_data
                
            except Exception as e:
                error_msg = f"Failed to download file from storage"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = e
                
                # Retry on storage errors (transient network issues)
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Retrying download in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
        
        # If we exhausted all retries, raise error
        error_msg = f"Failed to download file from storage after {max_attempts} attempts: {last_error}"
        logger.error(error_msg)
        raise StorageDownloadError(error_msg) from last_error
    
    async def _update_status(
        self,
        material_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update material processing status in database.
        
        Args:
            material_id: UUID of the material
            status: New status ('pending', 'processing', 'completed', 'failed')
            error_message: Optional error message (for 'failed' status)
        """
        try:
            update_data = {
                "processing_status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if status == "completed":
                update_data["processed_at"] = datetime.now(timezone.utc).isoformat()
            
            supabase_admin.table("materials").update(update_data).eq("id", material_id).execute()
            
            logger.info(f"Material {material_id} status updated to: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update material status: {e}")
            # Don't raise here - we don't want status update failures to crash processing
    
    async def _update_material_data(
        self,
        material_id: str,
        extracted_text: str,
        embedding: Optional[list[float]],
        status: str
    ) -> None:
        """
        Update material with extracted text and embedding.
        
        Args:
            material_id: UUID of the material
            extracted_text: Extracted text content
            embedding: Vector embedding (or None if no text)
            status: Processing status
        """
        try:
            update_data = {
                "extracted_text": extracted_text,
                "processing_status": status,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Only include embedding if it exists
            if embedding:
                # Convert list to PostgreSQL array format for pgvector
                update_data["embedding"] = embedding
            
            supabase_admin.table("materials").update(update_data).eq("id", material_id).execute()
            
            logger.info(
                f"Material {material_id} data updated: "
                f"{len(extracted_text)} chars, "
                f"embedding: {len(embedding) if embedding else 0} dims"
            )
            
        except Exception as e:
            error_msg = f"Failed to update material data: {e}"
            logger.error(error_msg)
            raise MaterialProcessingError(error_msg) from e
    
    async def search_materials(
        self,
        course_id: str,
        query: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across course materials.
        
        This method:
        1. Generates an embedding for the search query
        2. Performs vector similarity search using pgvector
        3. Returns results ranked by similarity score
        4. Handles edge cases (empty course, no results)
        
        Args:
            course_id: UUID of the course to search within
            query: Search query text
            limit: Maximum number of results to return (default: 3)
            
        Returns:
            List of search results with material metadata and similarity scores
            
        Raises:
            MaterialProcessingError: If search fails
        """
        try:
            search_start_time = datetime.now(timezone.utc)
            logger.info(f"=" * 60)
            logger.info(f"Starting semantic search in course {course_id}")
            logger.info(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
            logger.info(f"Limit: {limit}")
            logger.info(f"=" * 60)
            
            # Generate embedding for the search query
            try:
                logger.info("Generating embedding for search query")
                embed_start_time = datetime.now(timezone.utc)
                
                query_embedding = await self.ai_brain.generate_embedding(query, retry_on_failure=True)
                
                embed_duration = (datetime.now(timezone.utc) - embed_start_time).total_seconds()
                logger.info(
                    f"Query embedding generated in {embed_duration:.2f}s "
                    f"({len(query_embedding)} dimensions)"
                )
            except AIBrainClientError as e:
                error_msg = f"Failed to generate query embedding: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise MaterialProcessingError(error_msg) from e
            
            # Perform vector similarity search using pgvector
            # We use the <=> operator for cosine distance (lower is more similar)
            # Only search materials that have embeddings (completed processing)
            try:
                # Convert embedding list to PostgreSQL array format
                embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
                
                # Query using RPC function for vector similarity search
                # Note: We need to use a custom SQL query for vector operations
                result = supabase_admin.rpc(
                    "search_materials_by_embedding",
                    {
                        "query_course_id": course_id,
                        "query_embedding": embedding_str,
                        "match_limit": limit
                    }
                ).execute()
                
                if not result.data:
                    logger.info(f"No materials found for course {course_id}")
                    return []
                
                # Format results
                search_results = []
                for row in result.data:
                    # Extract text excerpt (first 500 chars of extracted text)
                    excerpt = row.get("extracted_text", "")[:500]
                    if len(row.get("extracted_text", "")) > 500:
                        excerpt += "..."
                    
                    search_results.append({
                        "material_id": row["id"],
                        "name": row["name"],
                        "excerpt": excerpt,
                        "similarity_score": float(row["similarity"]),
                        "file_type": row["file_type"]
                    })
                
                search_duration = (datetime.now(timezone.utc) - search_start_time).total_seconds()
                logger.info(f"=" * 60)
                logger.info(
                    f"Semantic search completed successfully: {len(search_results)} results "
                    f"(Total time: {search_duration:.2f}s)"
                )
                logger.info(f"=" * 60)
                return search_results
                
            except Exception as e:
                # If RPC function doesn't exist, fall back to direct query
                logger.warning(f"RPC function not available, using direct query fallback: {e}")
                
                # Direct query approach using Supabase's vector operations
                # This requires the pgvector extension and proper indexing
                result = supabase_admin.table("materials").select(
                    "id, name, extracted_text, file_type, embedding"
                ).eq(
                    "course_id", course_id
                ).eq(
                    "processing_status", "completed"
                ).execute()
                
                if not result.data or len(result.data) == 0:
                    logger.info(f"No processed materials found for course {course_id}")
                    return []
                
                # Calculate similarity scores manually and sort
                materials_with_scores = []
                for material in result.data:
                    # Only process materials with embeddings
                    if material.get("embedding") and material["embedding"] is not None:
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(
                            query_embedding,
                            material["embedding"]
                        )
                        
                        # Extract text excerpt
                        excerpt = material.get("extracted_text", "")[:500]
                        if len(material.get("extracted_text", "")) > 500:
                            excerpt += "..."
                        
                        materials_with_scores.append({
                            "material_id": material["id"],
                            "name": material["name"],
                            "excerpt": excerpt,
                            "similarity_score": similarity,
                            "file_type": material["file_type"]
                        })
                
                # Sort by similarity score (descending) and limit results
                materials_with_scores.sort(key=lambda x: x["similarity_score"], reverse=True)
                search_results = materials_with_scores[:limit]
                
                search_duration = (datetime.now(timezone.utc) - search_start_time).total_seconds()
                logger.info(f"=" * 60)
                logger.info(
                    f"Semantic search completed (fallback method): {len(search_results)} results "
                    f"(Total time: {search_duration:.2f}s)"
                )
                logger.info(f"=" * 60)
                return search_results
                
        except MaterialProcessingError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error during material search: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MaterialProcessingError(error_msg) from e
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1, higher is more similar)
        """
        import math
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Ensure result is in [0, 1] range (cosine similarity is in [-1, 1])
        # For embeddings, we typically expect positive similarity
        return max(0.0, min(1.0, similarity))
