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
            # Step 1: AI Brain service verification before processing
            logger.info(f"Material {material_id}: Performing AI Brain service verification before processing")
            verification_start_time = datetime.now(timezone.utc)
            
            # Verify basic connection
            if not await self.ai_brain.verify_connection():
                error_msg = "AI Brain service connection verification failed - service unavailable"
                logger.error(f"Material {material_id}: {error_msg}")
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                return
            
            # Verify embedding service specifically
            if not await self.ai_brain.verify_embedding_service():
                error_msg = "AI Brain embedding service verification failed"
                logger.error(f"Material {material_id}: {error_msg}")
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                return
            
            verification_duration = (datetime.now(timezone.utc) - verification_start_time).total_seconds()
            logger.info(f"Material {material_id}: AI Brain service verification completed in {verification_duration:.2f}s")
            
            # Step 2: Update status to processing
            await self._update_status(material_id, "processing")
            logger.info(f"Material {material_id}: Status updated to 'processing'")
            
            # Step 3: Get material record with enhanced error handling
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
                error_msg = f"Failed to retrieve material metadata: {e}"
                logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
                raise DatabaseUpdateError(error_msg) from e
            
            # Step 4: Download file from storage with enhanced error handling
            try:
                logger.info(f"Material {material_id}: Downloading file from storage: {material['file_path']}")
                download_start_time = datetime.now(timezone.utc)
                
                file_data = await self._download_file(material["file_path"])
                
                download_duration = (datetime.now(timezone.utc) - download_start_time).total_seconds()
                logger.info(
                    f"Material {material_id}: File downloaded successfully in {download_duration:.2f}s "
                    f"({len(file_data)} bytes)"
                )
            except Exception as e:
                error_msg = f"Failed to download file from storage: {e}"
                logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                raise StorageDownloadError(error_msg) from e
            
            # Step 5: Extract text using AI Brain with enhanced error handling and status tracking
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
                    f"Material {material_id}: OCR completed successfully in {ocr_duration:.2f}s - "
                    f"Extracted {len(extracted_text)} characters"
                )
                
                # Log text extraction quality for debugging
                if len(extracted_text) == 0:
                    logger.warning(f"Material {material_id}: OCR extracted no text - file may be empty or unsupported format")
                elif len(extracted_text) < 50:
                    logger.warning(f"Material {material_id}: OCR extracted very little text ({len(extracted_text)} chars) - file may have issues")
                
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
                logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                return
            except Exception as e:
                error_msg = f"Unexpected OCR processing error: {type(e).__name__}: {str(e)}"
                logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                return
            
            # Step 6: Generate embedding if text is not empty with enhanced error handling and status tracking
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
                        f"Material {material_id}: Embedding generated successfully in {embed_duration:.2f}s - "
                        f"Dimensions: {len(embedding)}"
                    )
                    
                    # Validate embedding quality for debugging
                    if len(embedding) != 1024:
                        logger.warning(f"Material {material_id}: Unexpected embedding dimension: {len(embedding)} (expected 1024)")
                    
                    # Check for zero vectors (potential issue)
                    if all(x == 0.0 for x in embedding):
                        logger.warning(f"Material {material_id}: Generated embedding is all zeros - may indicate processing issue")
                    
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
                    logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
                    await self._update_status(
                        material_id=material_id,
                        status="failed",
                        error_message=error_msg
                    )
                    return
                except Exception as e:
                    error_msg = f"Unexpected embedding generation error: {type(e).__name__}: {str(e)}"
                    logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
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
                logger.warning(
                    f"Material {material_id}: Material will not be searchable without embedding - "
                    f"consider checking file content or OCR quality"
                )
            
            # Step 7: Update database with results and comprehensive status tracking
            try:
                logger.info(f"Material {material_id}: Updating database with processing results")
                db_update_start_time = datetime.now(timezone.utc)
                
                await self._update_material_data(
                    material_id=material_id,
                    extracted_text=extracted_text,
                    embedding=embedding,
                    status="completed"
                )
                
                db_update_duration = (datetime.now(timezone.utc) - db_update_start_time).total_seconds()
                logger.info(f"Material {material_id}: Database update completed in {db_update_duration:.2f}s")
                
                # Log final processing summary for debugging
                logger.info(
                    f"Material {material_id}: Processing summary - "
                    f"Text: {len(extracted_text)} chars, "
                    f"Embedding: {len(embedding) if embedding else 0} dims, "
                    f"Status: completed"
                )
                
            except Exception as e:
                error_msg = f"Failed to update material data in database: {e}"
                logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
                await self._update_status(
                    material_id=material_id,
                    status="failed",
                    error_message=error_msg
                )
                raise DatabaseUpdateError(error_msg) from e
            
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
            # Status already updated in the download section
            
        except DatabaseUpdateError as e:
            error_msg = f"Database update error: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            # Status already updated in the database update section
            
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
            # Unexpected errors with comprehensive logging
            error_msg = f"Unexpected processing error: {type(e).__name__}: {str(e)}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            
            # Log additional debugging information
            processing_duration = (datetime.now(timezone.utc) - processing_start_time).total_seconds()
            logger.error(
                f"Material {material_id}: Processing failed after {processing_duration:.2f}s - "
                f"Error occurred during material processing workflow"
            )
            
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
        Update material processing status in database with comprehensive logging.
        
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
                logger.info(f"Material {material_id}: Recording error message: {error_message}")
            
            if status == "completed":
                update_data["processed_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"Material {material_id}: Recording completion timestamp")
            
            supabase_admin.table("materials").update(update_data).eq("id", material_id).execute()
            
            logger.info(f"Material {material_id}: Status updated successfully to '{status}'")
            
            # Log status transition for debugging
            if status == "failed" and error_message:
                logger.error(f"Material {material_id}: Processing failed - {error_message}")
            elif status == "completed":
                logger.info(f"Material {material_id}: Processing completed successfully")
            
        except Exception as e:
            logger.error(f"Material {material_id}: Failed to update status to '{status}': {e}", exc_info=True)
            # Don't raise here - we don't want status update failures to crash processing
    
    async def _update_material_data(
        self,
        material_id: str,
        extracted_text: str,
        embedding: Optional[list[float]],
        status: str
    ) -> None:
        """
        Update material with extracted text and embedding with comprehensive logging.
        
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
                logger.info(f"Material {material_id}: Including {len(embedding)}-dimensional embedding in database update")
            else:
                logger.warning(f"Material {material_id}: No embedding to store - material will not be searchable")
            
            # Clear any previous error message on successful completion
            if status == "completed":
                update_data["error_message"] = None
            
            supabase_admin.table("materials").update(update_data).eq("id", material_id).execute()
            
            logger.info(
                f"Material {material_id}: Data updated successfully - "
                f"Text: {len(extracted_text)} chars, "
                f"Embedding: {len(embedding) if embedding else 0} dims, "
                f"Status: {status}"
            )
            
            # Log searchability status for debugging
            if embedding and len(embedding) == 1024:
                logger.info(f"Material {material_id}: Material is now searchable with proper 1024-dim embedding")
            elif embedding:
                logger.warning(f"Material {material_id}: Embedding dimension mismatch: {len(embedding)} (expected 1024)")
            else:
                logger.warning(f"Material {material_id}: Material is not searchable (no embedding)")
            
        except Exception as e:
            error_msg = f"Failed to update material data in database: {e}"
            logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
            raise MaterialProcessingError(error_msg) from e
    
    async def search_materials(
        self,
        course_id: str,
        query: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across course materials with comprehensive edge case handling.
        
        This method:
        1. Handles short or empty search queries (Requirement 8.3)
        2. Handles courses without materials (Requirement 8.1)
        3. Handles unprocessed materials appropriately (Requirement 8.2)
        4. Performs AI Brain service health check before search operations
        5. Generates an embedding for the search query
        6. Verifies database search function exists
        7. Performs vector similarity search using pgvector
        8. Returns results ranked by similarity score
        9. Handles all edge cases with graceful degradation
        
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
            
            # EDGE CASE 1: Handle short or empty search queries (Requirement 8.3)
            if not query or not query.strip():
                logger.info(f"Course {course_id}: Empty search query - skipping material search")
                logger.info("Graceful degradation: proceeding with conversation history only")
                return []
            
            # Check for very short queries that may not be meaningful for semantic search
            query_stripped = query.strip()
            if len(query_stripped) < 3:
                logger.info(f"Course {course_id}: Very short search query ('{query_stripped}') - skipping material search")
                logger.info("Graceful degradation: proceeding with conversation history only")
                return []
            
            # EDGE CASE 2: Check if course has any materials at all (Requirement 8.1)
            logger.info(f"Course {course_id}: Checking if course has any uploaded materials")
            try:
                materials_check = supabase_admin.table("materials").select("id, processing_status").eq("course_id", course_id).execute()
                
                if not materials_check.data or len(materials_check.data) == 0:
                    logger.info(f"Course {course_id}: No materials have been uploaded to this course")
                    logger.info("Graceful degradation: proceeding with conversation history only (Requirement 8.1)")
                    return []
                
                # EDGE CASE 3: Check material processing status (Requirement 8.2)
                total_materials = len(materials_check.data)
                processed_materials = [m for m in materials_check.data if m.get("processing_status") == "completed"]
                processing_materials = [m for m in materials_check.data if m.get("processing_status") == "processing"]
                failed_materials = [m for m in materials_check.data if m.get("processing_status") == "failed"]
                pending_materials = [m for m in materials_check.data if m.get("processing_status") == "pending"]
                
                logger.info(
                    f"Course {course_id}: Material status summary - "
                    f"Total: {total_materials}, "
                    f"Processed: {len(processed_materials)}, "
                    f"Processing: {len(processing_materials)}, "
                    f"Failed: {len(failed_materials)}, "
                    f"Pending: {len(pending_materials)}"
                )
                
                if len(processed_materials) == 0:
                    if len(processing_materials) > 0:
                        logger.info(f"Course {course_id}: Materials exist but are still being processed ({len(processing_materials)} in progress)")
                        logger.info("Graceful degradation: proceeding without material context (Requirement 8.2)")
                    elif len(failed_materials) > 0:
                        logger.info(f"Course {course_id}: Materials exist but processing failed ({len(failed_materials)} failed)")
                        logger.info("Graceful degradation: proceeding without material context (Requirement 8.2)")
                    elif len(pending_materials) > 0:
                        logger.info(f"Course {course_id}: Materials exist but are pending processing ({len(pending_materials)} pending)")
                        logger.info("Graceful degradation: proceeding without material context (Requirement 8.2)")
                    else:
                        logger.info(f"Course {course_id}: Materials exist but none have completed processing")
                        logger.info("Graceful degradation: proceeding without material context (Requirement 8.2)")
                    return []
                
                logger.info(f"Course {course_id}: Found {len(processed_materials)} processed materials available for search")
                
            except Exception as e:
                logger.error(f"Course {course_id}: Failed to check material status: {e}", exc_info=True)
                logger.warning("Graceful degradation: proceeding without material context due to status check failure")
                return []
            
            # Step 1: AI Brain service health check before search operations
            logger.info("Performing AI Brain service health check before search")
            health_check_start = datetime.now(timezone.utc)
            
            if not await self.ai_brain.verify_connection():
                error_msg = "AI Brain service health check failed - service unavailable"
                logger.error(error_msg)
                logger.warning("Graceful degradation: returning empty search results due to AI Brain unavailability")
                return []
            
            if not await self.ai_brain.verify_embedding_service():
                error_msg = "AI Brain embedding service verification failed"
                logger.error(error_msg)
                logger.warning("Graceful degradation: returning empty search results due to embedding service unavailability")
                return []
            
            health_check_duration = (datetime.now(timezone.utc) - health_check_start).total_seconds()
            logger.info(f"AI Brain service health check passed in {health_check_duration:.2f}s")
            
            # Step 2: Verify database search function exists and determine search strategy
            logger.info("Verifying database search function availability")
            function_check_start = datetime.now(timezone.utc)
            
            use_rpc_function = await self._verify_search_function()
            
            if not use_rpc_function:
                error_msg = "Database search function 'search_materials_by_embedding' not available"
                logger.warning(error_msg)
                logger.info("Implementing fallback strategy: will use direct database query with manual similarity calculation")
            else:
                function_check_duration = (datetime.now(timezone.utc) - function_check_start).total_seconds()
                logger.info(f"Database search function verified in {function_check_duration:.2f}s - using optimized RPC function")
            
            # Step 3: Generate embedding for the search query with enhanced error handling
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
                logger.warning("Graceful degradation: returning empty search results due to embedding generation failure")
                return []
            
            # Step 4: Perform vector similarity search using appropriate strategy
            # Strategy is determined by database function verification result
            try:
                logger.info("Executing vector similarity search")
                vector_search_start = datetime.now(timezone.utc)
                
                # Convert embedding list to PostgreSQL array format
                embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
                
                if use_rpc_function:
                    # Use optimized RPC function for vector similarity search
                    try:
                        logger.info("Using optimized database RPC function for search")
                        result = supabase_admin.rpc(
                            "search_materials_by_embedding",
                            {
                                "query_course_id": course_id,
                                "query_embedding": embedding_str,
                                "match_limit": limit
                            }
                        ).execute()
                        
                        if not result.data:
                            logger.info(f"No materials found for course {course_id} using RPC function")
                            return []
                        
                        # Format results from RPC function
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
                        
                        vector_search_duration = (datetime.now(timezone.utc) - vector_search_start).total_seconds()
                        search_duration = (datetime.now(timezone.utc) - search_start_time).total_seconds()
                        logger.info(f"=" * 60)
                        logger.info(
                            f"Semantic search completed successfully using RPC function: {len(search_results)} results "
                            f"(Vector search: {vector_search_duration:.2f}s, Total time: {search_duration:.2f}s)"
                        )
                        logger.info(f"=" * 60)
                        return search_results
                        
                    except Exception as rpc_error:
                        # RPC function failed unexpectedly - log and fall back
                        logger.error(f"RPC function failed unexpectedly: {rpc_error}")
                        logger.warning("Falling back to direct query method")
                        use_rpc_function = False  # Force fallback for this search
                
                # Use fallback method: direct query with manual similarity calculation
                if not use_rpc_function:
                    logger.info("Using fallback method: direct database query with manual similarity calculation")
                    result = supabase_admin.table("materials").select(
                        "id, name, extracted_text, file_type, embedding"
                    ).eq(
                        "course_id", course_id
                    ).eq(
                        "processing_status", "completed"
                    ).execute()
                    
                    if not result.data or len(result.data) == 0:
                        logger.info(f"No processed materials found for course {course_id} using direct query")
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
                    
                    vector_search_duration = (datetime.now(timezone.utc) - vector_search_start).total_seconds()
                    search_duration = (datetime.now(timezone.utc) - search_start_time).total_seconds()
                    logger.info(f"=" * 60)
                    logger.info(
                        f"Semantic search completed using fallback method: {len(search_results)} results "
                        f"(Vector search: {vector_search_duration:.2f}s, Total time: {search_duration:.2f}s)"
                    )
                    logger.info(f"=" * 60)
                    return search_results
                    
            except Exception as search_error:
                error_msg = f"Vector similarity search failed: {str(search_error)}"
                logger.error(error_msg, exc_info=True)
                logger.warning("Graceful degradation: returning empty search results due to vector search failure")
                return []
                
        except MaterialProcessingError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error during material search: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.warning("Graceful degradation: returning empty search results due to unexpected error")
            return []
    
    async def _verify_search_function(self) -> bool:
        """
        Verify that the search_materials_by_embedding database function exists and is accessible.
        
        This method implements comprehensive database function verification:
        1. Tests function execution with dummy parameters (primary method)
        2. Optionally checks function existence using PostgreSQL system catalogs
        3. Validates function permissions and accessibility
        4. Provides detailed error diagnostics for troubleshooting
        
        Returns:
            True if function is available and accessible, False otherwise
        """
        try:
            logger.info("Verifying database search function 'search_materials_by_embedding'")
            
            # Primary verification: Test function execution with dummy parameters
            logger.debug("Testing function execution with dummy parameters")
            try:
                # Use a dummy UUID and embedding for testing
                dummy_course_id = "00000000-0000-0000-0000-000000000000"
                dummy_embedding = "[" + ",".join(["0.0"] * 1024) + "]"
                
                result = supabase_admin.rpc(
                    "search_materials_by_embedding",
                    {
                        "query_course_id": dummy_course_id,
                        "query_embedding": dummy_embedding,
                        "match_limit": 1
                    }
                ).execute()
                
                # If we get here, function is callable and accessible
                logger.info("Database search function 'search_materials_by_embedding' verified successfully")
                logger.debug(f"Function test returned {len(result.data) if result.data else 0} results (expected for dummy data)")
                
                # Optional: Try to get additional function information if exec_sql is available
                try:
                    function_check_query = """
                    SELECT 
                        proname as function_name,
                        pronargs as num_args,
                        prorettype::regtype as return_type
                    FROM pg_proc 
                    WHERE proname = 'search_materials_by_embedding'
                    AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                    """
                    
                    catalog_result = supabase_admin.rpc('exec_sql', {
                        'query': function_check_query
                    }).execute()
                    
                    if catalog_result.data and len(catalog_result.data) > 0:
                        function_info = catalog_result.data[0]
                        logger.debug(f"Function details: {function_info['function_name']} with {function_info['num_args']} arguments")
                    
                except Exception as catalog_error:
                    logger.debug(f"Could not query system catalog (not critical): {catalog_error}")
                
                return True
                
            except Exception as execution_error:
                logger.error(f"Database search function execution failed: {execution_error}")
                
                # Provide detailed error diagnostics
                error_str = str(execution_error).lower()
                if "permission denied" in error_str or "access denied" in error_str:
                    logger.error("Function exists but user lacks execute permissions")
                    logger.error("Check that GRANT EXECUTE ON FUNCTION search_materials_by_embedding TO authenticated; was run")
                elif "function" in error_str and "does not exist" in error_str:
                    logger.error("Function 'search_materials_by_embedding' does not exist in database")
                    logger.error("Run migration 006_add_vector_search_function.sql to create the function")
                elif "relation" in error_str and "does not exist" in error_str:
                    logger.error("Required tables (materials) may not exist")
                    logger.error("Ensure database migrations have been run properly")
                elif "type" in error_str and "vector" in error_str:
                    logger.error("pgvector extension may not be installed or vector type not available")
                    logger.error("Ensure pgvector extension is installed: CREATE EXTENSION IF NOT EXISTS vector;")
                else:
                    logger.error(f"Unknown function execution error: {execution_error}")
                
                return False
                
        except Exception as e:
            logger.error(f"Database search function verification failed with unexpected error: {e}", exc_info=True)
            return False
    
    async def verify_all_database_functions(self) -> Dict[str, bool]:
        """
        Verify all required database functions for RAG operations.
        
        This method provides a comprehensive check of all database functions
        required for RAG functionality, allowing for detailed status reporting
        and selective fallback strategies.
        
        Returns:
            Dictionary mapping function names to their availability status
        """
        logger.info("Verifying all database functions required for RAG operations")
        
        function_status = {}
        
        # Check search_materials_by_embedding function
        function_status["search_materials_by_embedding"] = await self._verify_search_function()
        
        # Future: Add other database function checks here
        # function_status["other_function"] = await self._verify_other_function()
        
        # Log summary
        available_functions = [name for name, status in function_status.items() if status]
        unavailable_functions = [name for name, status in function_status.items() if not status]
        
        logger.info(f"Database function verification summary:")
        logger.info(f"  Available functions: {available_functions}")
        if unavailable_functions:
            logger.warning(f"  Unavailable functions: {unavailable_functions}")
        
        return function_status
    
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
