"""
Integration tests for complete RAG workflow.

This test suite verifies the end-to-end RAG functionality:
1. Upload PDF with known content
2. Verify processing completes successfully  
3. Test semantic search finds relevant content
4. Verify chat responses reference materials

Requirements: 1.1, 1.2, 1.3, 3.4
"""

import pytest
import asyncio
import uuid
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.material_processing_service import MaterialProcessingService
from services.context_service import ContextService
from services.ai_brain_client import AIBrainClient
from models.schemas import UserContext, Message, UserPreferences, AcademicInfo


class TestCompleteRAGWorkflow:
    """Test complete RAG workflow from upload to chat response."""
    
    @pytest.fixture
    def mock_ai_brain_client(self):
        """Create a mock AI Brain client with realistic responses."""
        client = Mock(spec=AIBrainClient)
        client.verify_connection = AsyncMock(return_value=True)
        client.verify_embedding_service = AsyncMock(return_value=True)
        client.health_check = AsyncMock(return_value=True)
        
        # Mock OCR extraction
        client.extract_text = AsyncMock(return_value="Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. Deep learning uses neural networks with multiple layers to learn complex patterns in data.")
        
        # Mock embedding generation with consistent vectors
        def generate_embedding_side_effect(text, **kwargs):
            if "machine learning" in text.lower():
                return [0.8] * 512 + [0.2] * 512  # High similarity for ML content
            elif "neural network" in text.lower():
                return [0.7] * 512 + [0.3] * 512  # Medium-high similarity
            else:
                return [0.1] * 1024  # Low similarity for other content
        
        client.generate_embedding = AsyncMock(side_effect=generate_embedding_side_effect)
        return client
    
    @pytest.fixture
    def processing_service(self, mock_ai_brain_client):
        """Create material processing service."""
        return MaterialProcessingService(ai_brain_client=mock_ai_brain_client)
    
    @pytest.fixture
    def context_service(self):
        """Create context service."""
        return ContextService()
    
    @pytest.mark.asyncio
    async def test_upload_and_process_pdf_workflow(self, processing_service, mock_ai_brain_client):
        """
        Test PDF upload and processing workflow.
        
        Requirements: 3.4 - Processing completes successfully and stores complete data
        """
        material_id = str(uuid.uuid4())
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock material retrieval
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            
            # Mock material data
            mock_table.execute.return_value = MagicMock(data=[{
                "id": material_id,
                "name": "machine_learning_guide.pdf",
                "file_path": f"materials/{material_id}/machine_learning_guide.pdf",
                "processing_status": "pending"
            }])
            
            # Mock update operations
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"PDF content data"
            
            # Process the material
            await processing_service.process_material(material_id)
            
            # Verify AI Brain methods were called
            mock_ai_brain_client.extract_text.assert_called_once()
            mock_ai_brain_client.generate_embedding.assert_called_once()
            
            # Verify status updates
            update_calls = mock_table.update.call_args_list
            
            # First call: status to processing
            processing_update = update_calls[0][0][0]
            assert processing_update["processing_status"] == "processing"
            
            # Final call: status to completed with data
            completed_update = update_calls[-1][0][0]
            assert completed_update["processing_status"] == "completed"
            assert completed_update["extracted_text"] == "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. Deep learning uses neural networks with multiple layers to learn complex patterns in data."
            assert len(completed_update["embedding"]) == 1024
            assert "processed_at" in completed_update
    
    @pytest.mark.asyncio
    async def test_semantic_search_finds_relevant_content(self, processing_service, mock_ai_brain_client):
        """
        Test that semantic search finds relevant content from processed materials.
        
        Requirements: 1.1, 1.2 - Search triggers and returns relevant results
        """
        course_id = str(uuid.uuid4())
        query = "What is machine learning?"
        
        # Mock processed materials in the course
        mock_materials = [
            {
                "id": "material-1",
                "name": "ml_guide.pdf",
                "extracted_text": "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. It enables computers to learn and improve from experience.",
                "file_type": "application/pdf",
                "embedding": [0.8] * 512 + [0.2] * 512  # High similarity
            },
            {
                "id": "material-2", 
                "name": "statistics.pdf",
                "extracted_text": "Statistical analysis involves collecting, organizing, and interpreting data to identify patterns and trends.",
                "file_type": "application/pdf",
                "embedding": [0.3] * 512 + [0.7] * 512  # Lower similarity
            }
        ]
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock material status check - return processed materials
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            
            call_count = 0
            def mock_execute():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # First call: material status check
                    return Mock(data=[
                        {"id": "material-1", "processing_status": "completed"},
                        {"id": "material-2", "processing_status": "completed"}
                    ])
                else:
                    # Second call: actual search query
                    return Mock(data=mock_materials)
            
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute = mock_execute
            
            # Mock RPC call failure (fallback to direct query)
            mock_supabase.rpc.side_effect = Exception("RPC not available")
            
            # Execute search
            results = await processing_service.search_materials(course_id, query, limit=3)
            
            # Verify results
            assert len(results) == 2
            
            # Verify most relevant result is first (ml_guide.pdf)
            assert results[0]["material_id"] == "material-1"
            assert results[0]["name"] == "ml_guide.pdf"
            assert "machine learning" in results[0]["excerpt"].lower()
            assert results[0]["similarity_score"] > results[1]["similarity_score"]
            
            # Verify result structure includes all required metadata
            for result in results:
                assert "material_id" in result
                assert "name" in result
                assert "excerpt" in result
                assert "similarity_score" in result
                assert "file_type" in result
    
    @pytest.mark.asyncio
    async def test_chat_context_integration_with_materials(self, context_service):
        """
        Test that chat context properly integrates materials and history.
        
        Requirements: 1.3 - Materials included in AI prompt with clear identification
        """
        # Mock user context with chat history
        chat_history = [
            Message(
                content="Hello, I'm studying machine learning",
                role="user"
            ),
            Message(
                content="Great! I can help you with machine learning concepts.",
                role="model"
            )
        ]
        
        user_context = UserContext(
            preferences=UserPreferences(
                detail_level=0.7,
                example_preference=0.8,
                analogy_preference=0.6,
                technical_language=0.5,
                structure_preference=0.7,
                visual_preference=0.9,
                learning_pace="moderate",
                prior_experience="intermediate"
            ),
            academic=AcademicInfo(
                grade=["Bachelor"],
                semester_type="double",
                semester=6,
                subject=["Computer Science"]
            ),
            chat_history=chat_history,
            has_preferences=True,
            has_academic=True,
            has_history=True
        )
        
        # Mock material context from search results
        material_context = """
RELEVANT COURSE MATERIALS:

Material: ml_guide.pdf (Relevance: 0.85)
Content: Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. It enables computers to learn and improve from experience without being explicitly programmed.

Material: neural_networks.pdf (Relevance: 0.72)
Content: Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information using connectionist approaches.
"""
        
        current_message = "Can you explain the difference between supervised and unsupervised learning?"
        
        # Format the context prompt
        formatted_prompt = context_service.format_context_prompt(
            user_context,
            current_message,
            material_context=material_context
        )
        
        # Verify prompt structure and content
        assert "RELEVANT COURSE MATERIALS:" in formatted_prompt
        assert "ml_guide.pdf" in formatted_prompt
        assert "neural_networks.pdf" in formatted_prompt
        assert "Machine learning is a subset" in formatted_prompt
        
        # Verify chat history is included
        assert "=== RECENT CONVERSATION ===" in formatted_prompt
        assert "Hello, I'm studying machine learning" in formatted_prompt
        assert "Great! I can help you" in formatted_prompt
        
        # Verify current question is included
        assert "=== CURRENT QUESTION ===" in formatted_prompt
        assert "difference between supervised and unsupervised" in formatted_prompt
        
        # Verify user preferences are included
        assert "=== LEARNING PREFERENCES ===" in formatted_prompt
        assert "moderate" in formatted_prompt
        
        # Verify academic info is included
        assert "=== STUDENT ACADEMIC CONTEXT ===" in formatted_prompt
        assert "Computer Science" in formatted_prompt
        assert "Bachelor" in formatted_prompt
    
    @pytest.mark.asyncio
    async def test_end_to_end_rag_pipeline(self, processing_service, context_service, mock_ai_brain_client):
        """
        Test complete end-to-end RAG pipeline simulation.
        
        Requirements: 1.1, 1.2, 1.3 - Complete RAG workflow
        """
        course_id = str(uuid.uuid4())
        material_id = str(uuid.uuid4())
        user_query = "What are the main types of machine learning?"
        
        # Step 1: Simulate material processing (already tested above)
        # This would have been done when PDF was uploaded
        
        # Step 2: Simulate material search
        mock_search_results = [
            {
                "material_id": material_id,
                "name": "ml_fundamentals.pdf",
                "excerpt": "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data to train models.",
                "similarity_score": 0.89,
                "file_type": "application/pdf"
            }
        ]
        
        with patch.object(processing_service, 'search_materials', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            # Execute search
            search_results = await processing_service.search_materials(course_id, user_query, limit=3)
            
            # Verify search was called and returned results
            mock_search.assert_called_once_with(course_id, user_query, limit=3)
            assert len(search_results) == 1
            assert search_results[0]["similarity_score"] > 0.8
        
        # Step 3: Format material context for AI prompt
        material_context = f"""
RELEVANT COURSE MATERIALS:

Material: {search_results[0]['name']} (Relevance: {search_results[0]['similarity_score']:.2f})
Content: {search_results[0]['excerpt']}
"""
        
        # Step 4: Create user context with empty history (new conversation)
        user_context = UserContext(
            preferences=UserPreferences(
                detail_level=0.9,
                example_preference=0.7,
                analogy_preference=0.5,
                technical_language=0.8,
                structure_preference=0.8,
                visual_preference=0.6,
                learning_pace="moderate",
                prior_experience="advanced"
            ),
            academic=AcademicInfo(
                grade=["Masters"],
                semester_type="double",
                semester=4,
                subject=["Data Science", "Statistics"]
            ),
            chat_history=[],
            has_preferences=True,
            has_academic=True,
            has_history=False
        )
        
        # Step 5: Format complete context prompt
        final_prompt = context_service.format_context_prompt(
            user_context,
            user_query,
            material_context=material_context
        )
        
        # Verify the final prompt contains all necessary components
        assert "RELEVANT COURSE MATERIALS:" in final_prompt
        assert "ml_fundamentals.pdf" in final_prompt
        assert "supervised learning, unsupervised learning, and reinforcement learning" in final_prompt
        assert "=== CURRENT QUESTION ===" in final_prompt
        assert "What are the main types of machine learning?" in final_prompt
        assert "=== LEARNING PREFERENCES ===" in final_prompt
        assert "moderate" in final_prompt
        
        # Verify prompt is well-structured for AI consumption
        sections = final_prompt.split("\n\n")
        assert len(sections) >= 4  # Should have multiple clear sections
        
        # The AI would now receive this comprehensive prompt and generate a response
        # that references the uploaded materials
    
    @pytest.mark.asyncio
    async def test_workflow_with_multiple_materials_ranking(self, processing_service, mock_ai_brain_client):
        """
        Test workflow with multiple materials to verify proper ranking.
        
        Requirements: 1.2 - Top 3 most semantically similar excerpts
        """
        course_id = str(uuid.uuid4())
        query = "neural networks and deep learning"
        
        # Mock multiple materials with different relevance scores
        mock_materials = [
            {
                "id": "material-1",
                "name": "deep_learning.pdf", 
                "extracted_text": "Deep learning is a subset of machine learning that uses neural networks with multiple hidden layers. These networks can learn complex patterns and representations from large amounts of data.",
                "file_type": "application/pdf",
                "embedding": [0.9] * 512 + [0.1] * 512  # Highest similarity
            },
            {
                "id": "material-2",
                "name": "neural_networks.pdf",
                "extracted_text": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes that process information through weighted connections.",
                "file_type": "application/pdf", 
                "embedding": [0.8] * 512 + [0.2] * 512  # High similarity
            },
            {
                "id": "material-3",
                "name": "statistics.pdf",
                "extracted_text": "Statistical methods are fundamental to data analysis. Regression analysis helps identify relationships between variables in datasets.",
                "file_type": "application/pdf",
                "embedding": [0.2] * 512 + [0.8] * 512  # Low similarity
            },
            {
                "id": "material-4",
                "name": "algorithms.pdf",
                "extracted_text": "Machine learning algorithms can be categorized into supervised, unsupervised, and reinforcement learning approaches.",
                "file_type": "application/pdf",
                "embedding": [0.6] * 512 + [0.4] * 512  # Medium similarity
            }
        ]
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            
            call_count = 0
            def mock_execute():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # Material status check
                    return Mock(data=[{"id": f"material-{i}", "processing_status": "completed"} for i in range(1, 5)])
                else:
                    # Search query
                    return Mock(data=mock_materials)
            
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute = mock_execute
            
            # Mock RPC failure
            mock_supabase.rpc.side_effect = Exception("RPC not available")
            
            # Execute search with limit of 3
            results = await processing_service.search_materials(course_id, query, limit=3)
            
            # Verify only top 3 results returned
            assert len(results) == 3
            
            # Verify results are ranked by similarity (descending)
            # Note: The actual ranking depends on cosine similarity calculation
            # Just verify that results are properly ranked
            
            # Verify similarity scores are in descending order
            assert results[0]["similarity_score"] >= results[1]["similarity_score"]
            assert results[1]["similarity_score"] >= results[2]["similarity_score"]
            
            # Verify statistics.pdf (lowest similarity) is not included
            material_ids = [r["material_id"] for r in results]
            assert "material-3" not in material_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])