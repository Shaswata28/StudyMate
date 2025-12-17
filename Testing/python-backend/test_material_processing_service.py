"""
Unit tests for MaterialProcessingService.

These tests verify the core functionality of the material processing service
including initialization, status updates, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.material_processing_service import MaterialProcessingService, MaterialProcessingError
from services.ai_brain_client import AIBrainClient, AIBrainClientError


class TestMaterialProcessingServiceInitialization:
    """Test service initialization."""
    
    def test_service_initialization(self):
        """Test that service initializes with correct parameters."""
        ai_brain_client = Mock(spec=AIBrainClient)
        
        service = MaterialProcessingService(
            ai_brain_client=ai_brain_client,
            timeout=300.0
        )
        
        assert service.ai_brain == ai_brain_client
        assert service.timeout == 300.0
    
    def test_service_default_timeout(self):
        """Test that service uses default timeout when not specified."""
        ai_brain_client = Mock(spec=AIBrainClient)
        
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        assert service.timeout == 300.0


class TestMaterialProcessingStatusUpdates:
    """Test status update functionality."""
    
    @pytest.mark.asyncio
    async def test_update_status_to_processing(self):
        """Test updating status to 'processing'."""
        ai_brain_client = Mock(spec=AIBrainClient)
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock()
            
            await service._update_status("test-id", "processing")
            
            # Verify update was called with correct status
            mock_supabase.table.assert_called_once_with("materials")
            update_call = mock_table.update.call_args[0][0]
            assert update_call["processing_status"] == "processing"
    
    @pytest.mark.asyncio
    async def test_update_status_to_failed_with_error(self):
        """Test updating status to 'failed' with error message."""
        ai_brain_client = Mock(spec=AIBrainClient)
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock()
            
            await service._update_status("test-id", "failed", error_message="Test error")
            
            # Verify update was called with status and error message
            update_call = mock_table.update.call_args[0][0]
            assert update_call["processing_status"] == "failed"
            assert update_call["error_message"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_update_status_to_completed_sets_timestamp(self):
        """Test that completing sets processed_at timestamp."""
        ai_brain_client = Mock(spec=AIBrainClient)
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock()
            
            await service._update_status("test-id", "completed")
            
            # Verify processed_at is set
            update_call = mock_table.update.call_args[0][0]
            assert update_call["processing_status"] == "completed"
            assert "processed_at" in update_call


class TestMaterialProcessingErrorHandling:
    """Test error handling in material processing."""
    
    @pytest.mark.asyncio
    async def test_process_material_handles_ai_brain_error(self):
        """Test that AI Brain errors are caught and status updated to failed."""
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        ai_brain_client.extract_text = AsyncMock(side_effect=AIBrainClientError("Service unavailable"))
        
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database operations
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": "test-id",
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test data"
            
            # Process material - should handle error gracefully
            await service.process_material("test-id")
            
            # Verify status was updated to failed
            # The last update call should be for failed status
            last_update_call = mock_table.update.call_args_list[-1][0][0]
            assert last_update_call["processing_status"] == "failed"
            assert "OCR processing failed" in last_update_call["error_message"]
    
    @pytest.mark.asyncio
    async def test_process_material_handles_timeout(self):
        """Test that processing timeouts are handled correctly."""
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        
        # Simulate a timeout by making extract_text take too long
        async def slow_extract(*args, **kwargs):
            import asyncio
            await asyncio.sleep(10)  # Longer than timeout
            return "text"
        
        ai_brain_client.extract_text = slow_extract
        
        service = MaterialProcessingService(ai_brain_client=ai_brain_client, timeout=0.1)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database operations
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": "test-id",
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test data"
            
            # Process material - should timeout
            await service.process_material("test-id")
            
            # Verify status was updated to failed with timeout message
            last_update_call = mock_table.update.call_args_list[-1][0][0]
            assert last_update_call["processing_status"] == "failed"
            assert "timeout" in last_update_call["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_process_material_handles_missing_material(self):
        """Test that missing materials are handled gracefully."""
        ai_brain_client = Mock(spec=AIBrainClient)
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database returning no material
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[])
            mock_table.update.return_value = mock_table
            
            # Process material - should handle missing material gracefully
            await service.process_material("nonexistent-id")
            
            # Verify that no status update was attempted (material doesn't exist)
            # The processing should complete without error but not update status
            # since you can't update the status of a non-existent material
            assert mock_table.update.call_count == 1  # Only the initial "processing" status update
            first_update_call = mock_table.update.call_args_list[0][0][0]
            assert first_update_call["processing_status"] == "processing"


class TestMaterialProcessingWorkflow:
    """Test complete processing workflow."""
    
    @pytest.mark.asyncio
    async def test_successful_processing_with_text_and_embedding(self):
        """Test successful processing that extracts text and generates embedding."""
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        ai_brain_client.extract_text = AsyncMock(return_value="Extracted text content")
        ai_brain_client.generate_embedding = AsyncMock(return_value=[0.1] * 1024)
        
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database operations
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": "test-id",
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test pdf data"
            
            # Process material
            await service.process_material("test-id")
            
            # Verify AI Brain methods were called
            ai_brain_client.extract_text.assert_called_once()
            ai_brain_client.generate_embedding.assert_called_once_with("Extracted text content", retry_on_failure=True)
            
            # Verify final update includes text and embedding
            final_update_call = mock_table.update.call_args_list[-1][0][0]
            assert final_update_call["extracted_text"] == "Extracted text content"
            assert final_update_call["embedding"] == [0.1] * 1024
            assert final_update_call["processing_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_processing_with_empty_text_skips_embedding(self):
        """Test that empty text extraction skips embedding generation."""
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.extract_text = AsyncMock(return_value="")
        ai_brain_client.generate_embedding = AsyncMock()
        
        service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database operations
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": "test-id",
                "name": "blank.pdf",
                "file_path": "path/to/blank.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"blank pdf"
            
            # Process material
            await service.process_material("test-id")
            
            # Verify embedding generation was NOT called
            ai_brain_client.generate_embedding.assert_not_called()
            
            # Verify status is still completed
            final_update_call = mock_table.update.call_args_list[-1][0][0]
            assert final_update_call["extracted_text"] == ""
            assert final_update_call["processing_status"] == "completed"
            assert "embedding" not in final_update_call or final_update_call["embedding"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
