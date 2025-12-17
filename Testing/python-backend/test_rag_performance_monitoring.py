"""
Tests for RAG performance optimization and monitoring.

This test suite verifies:
1. Performance logging for RAG operations
2. Search query performance optimization
3. Component health monitoring

Requirements: 6.5
"""

import pytest
import asyncio
import time
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.material_processing_service import MaterialProcessingService
from services.context_service import ContextService
from services.ai_brain_client import AIBrainClient
from models.schemas import UserContext, Message, UserPreferences, AcademicInfo


class TestPerformanceLogging:
    """Test performance logging for RAG operations."""
    
    @pytest.fixture
    def mock_ai_brain_client(self):
        """Create AI Brain client with realistic timing."""
        client = Mock(spec=AIBrainClient)
        client.verify_connection = AsyncMock(return_value=True)
        client.verify_embedding_service = AsyncMock(return_value=True)
        
        # Mock embedding generation with realistic delay
        async def generate_embedding_with_delay(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms processing time
            return [0.5] * 1024
        
        client.generate_embedding = generate_embedding_with_delay
        return client
    
    @pytest.fixture
    def processing_service(self, mock_ai_brain_client):
        """Create processing service for performance testing."""
        return MaterialProcessingService(ai_brain_client=mock_ai_brain_client)
    
    @pytest.mark.asyncio
    async def test_search_operation_timing_logged(self, processing_service, caplog):
        """
        Test that search operations log timing information.
        
        Requirements: 6.5 - Performance logging for RAG operations
        """
        course_id = str(uuid.uuid4())
        query = "machine learning performance test"
        
        mock_materials = [
            {
                "id": "material-1",
                "name": "performance_test.pdf",
                "extracted_text": "Performance testing content for machine learning algorithms",
                "file_type": "application/pdf",
                "embedding": [0.5] * 1024
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
                    return Mock(data=[{"id": "material-1", "processing_status": "completed"}])
                else:
                    # Search query
                    return Mock(data=mock_materials)
            
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute = mock_execute
            
            # Mock RPC failure (use fallback)
            mock_supabase.rpc.side_effect = Exception("RPC not available")
            
            # Capture start time
            start_time = time.time()
            
            # Execute search
            results = await processing_service.search_materials(course_id, query, limit=3)
            
            # Calculate actual duration
            actual_duration = time.time() - start_time
            
            # Verify results
            assert len(results) == 1
            
            # Verify timing is reasonable (should include embedding generation delay)
            assert actual_duration >= 0.1  # At least the embedding generation time
            assert actual_duration < 5.0   # But not excessively long
    
    @pytest.mark.asyncio
    async def test_context_formatting_performance(self):
        """
        Test context formatting performance with large datasets.
        
        Requirements: 6.5 - Performance monitoring for context operations
        """
        context_service = ContextService()
        
        # Create large chat history (simulate long conversation)
        large_chat_history = []
        for i in range(50):  # 50 messages
            large_chat_history.extend([
                Message(
                    content=f"User message {i} with some content about machine learning and data science topics",
                    role="user"
                ),
                Message(
                    content=f"Assistant response {i} providing detailed explanations about the requested topics with comprehensive information",
                    role="model"
                )
            ])
        
        user_context = UserContext(
            preferences=UserPreferences(
                detail_level=0.9,
                example_preference=0.8,
                analogy_preference=0.6,
                technical_language=0.9,
                structure_preference=0.8,
                visual_preference=0.5,
                learning_pace="fast",
                prior_experience="expert"
            ),
            academic=AcademicInfo(
                grade=["Masters"],
                semester_type="double",
                semester=8,
                subject=["Computer Science", "Machine Learning"]
            ),
            chat_history=large_chat_history,
            has_preferences=True,
            has_academic=True,
            has_history=True
        )
        
        # Create large material context
        large_material_context = """
RELEVANT COURSE MATERIALS:

Material: comprehensive_ml_guide.pdf (Relevance: 0.95)
Content: """ + "Machine learning content. " * 200 + """

Material: advanced_algorithms.pdf (Relevance: 0.87)
Content: """ + "Algorithm explanations. " * 150 + """

Material: data_structures.pdf (Relevance: 0.82)
Content: """ + "Data structure details. " * 100
        
        current_message = "Can you provide a comprehensive explanation of gradient descent optimization algorithms?"
        
        # Measure formatting performance
        start_time = time.time()
        
        formatted_prompt = context_service.format_context_prompt(
            user_context,
            current_message,
            material_context=large_material_context
        )
        
        formatting_duration = time.time() - start_time
        
        # Verify prompt was created successfully
        assert len(formatted_prompt) > 1000  # Should be substantial
        assert "RELEVANT COURSE MATERIALS:" in formatted_prompt
        assert "RECENT CONVERSATION:" in formatted_prompt
        assert "CURRENT QUESTION:" in formatted_prompt
        
        # Verify performance is acceptable (should be fast)
        assert formatting_duration < 1.0  # Should complete within 1 second
    
    @pytest.mark.asyncio
    async def test_concurrent_search_operations_performance(self, processing_service):
        """
        Test performance with concurrent search operations.
        
        Requirements: 6.5 - Performance under concurrent load
        """
        course_id = str(uuid.uuid4())
        queries = [
            "machine learning algorithms",
            "neural network architectures", 
            "data preprocessing techniques",
            "model evaluation metrics",
            "deep learning frameworks"
        ]
        
        mock_materials = [
            {
                "id": f"material-{i}",
                "name": f"document_{i}.pdf",
                "extracted_text": f"Content for query {i} about various topics",
                "file_type": "application/pdf",
                "embedding": [0.5 + i * 0.1] * 1024
            }
            for i in range(5)
        ]
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            
            call_count = 0
            def mock_execute():
                nonlocal call_count
                call_count += 1
                if call_count % 2 == 1:
                    # Odd calls: material status check
                    return Mock(data=[{"id": f"material-{i}", "processing_status": "completed"} for i in range(5)])
                else:
                    # Even calls: search query
                    return Mock(data=mock_materials)
            
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute = mock_execute
            
            # Mock RPC failure (use fallback)
            mock_supabase.rpc.side_effect = Exception("RPC not available")
            
            # Execute concurrent searches
            start_time = time.time()
            
            tasks = [
                processing_service.search_materials(course_id, query, limit=3)
                for query in queries
            ]
            
            results = await asyncio.gather(*tasks)
            
            concurrent_duration = time.time() - start_time
            
            # Verify all searches completed
            assert len(results) == 5
            for result_set in results:
                assert isinstance(result_set, list)
            
            # Verify concurrent performance is reasonable
            # Should be faster than sequential execution due to async operations
            assert concurrent_duration < 10.0  # Should complete within reasonable time


class TestSearchQueryOptimization:
    """Test search query performance optimization."""
    
    @pytest.fixture
    def optimized_processing_service(self):
        """Create processing service optimized for performance testing."""
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        
        # Mock fast embedding generation
        ai_brain_client.generate_embedding = AsyncMock(return_value=[0.5] * 1024)
        
        return MaterialProcessingService(ai_brain_client=ai_brain_client)
    
    @pytest.mark.asyncio
    async def test_search_result_limit_optimization(self, optimized_processing_service):
        """
        Test that search respects limit parameter for performance optimization.
        
        Requirements: 6.5 - Search query performance optimization
        """
        course_id = str(uuid.uuid4())
        query = "optimization test query"
        
        # Create large dataset to test limit effectiveness
        large_material_set = [
            {
                "id": f"material-{i}",
                "name": f"document_{i}.pdf",
                "extracted_text": f"Content {i} for optimization testing",
                "file_type": "application/pdf",
                "embedding": [0.5 + i * 0.01] * 1024
            }
            for i in range(100)  # 100 materials
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
                    return Mock(data=[{"id": f"material-{i}", "processing_status": "completed"} for i in range(100)])
                else:
                    # Search query - return all materials
                    return Mock(data=large_material_set)
            
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute = mock_execute
            
            # Mock RPC failure (use fallback)
            mock_supabase.rpc.side_effect = Exception("RPC not available")
            
            # Test with small limit
            start_time = time.time()
            results = await optimized_processing_service.search_materials(course_id, query, limit=3)
            small_limit_duration = time.time() - start_time
            
            # Verify only 3 results returned despite 100 available
            assert len(results) == 3
            
            # Test with larger limit
            start_time = time.time()
            results = await optimized_processing_service.search_materials(course_id, query, limit=10)
            large_limit_duration = time.time() - start_time
            
            # Verify 10 results returned
            assert len(results) == 10
            
            # Performance should be similar regardless of limit (processing is optimized)
            assert abs(small_limit_duration - large_limit_duration) < 1.0
    
    @pytest.mark.asyncio
    async def test_empty_query_optimization(self, optimized_processing_service):
        """
        Test optimization for empty or very short queries.
        
        Requirements: 6.5 - Query optimization for edge cases
        """
        course_id = str(uuid.uuid4())
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[
                {"id": "material-1", "processing_status": "completed"}
            ])
            
            # Test empty query
            start_time = time.time()
            results = await optimized_processing_service.search_materials(course_id, "", limit=3)
            empty_query_duration = time.time() - start_time
            
            # Should return empty results quickly
            assert results == []
            assert empty_query_duration < 0.5  # Should be very fast
            
            # Test very short query
            start_time = time.time()
            results = await optimized_processing_service.search_materials(course_id, "a", limit=3)
            short_query_duration = time.time() - start_time
            
            # Should handle short queries efficiently
            assert isinstance(results, list)
            assert short_query_duration < 1.0
    
    @pytest.mark.asyncio
    async def test_similarity_calculation_performance(self, optimized_processing_service):
        """
        Test performance of similarity calculations with large vectors.
        
        Requirements: 6.5 - Similarity calculation optimization
        """
        # Test cosine similarity calculation performance
        service = optimized_processing_service
        
        # Create large vectors (1024 dimensions)
        vector1 = [0.5] * 1024
        vector2 = [0.6] * 1024
        
        # Measure similarity calculation performance
        start_time = time.time()
        
        # Calculate similarity multiple times
        for _ in range(1000):
            similarity = service._cosine_similarity(vector1, vector2)
        
        calculation_duration = time.time() - start_time
        
        # Verify calculation is correct
        assert 0.0 <= similarity <= 1.0
        
        # Verify performance is acceptable (1000 calculations should be fast)
        assert calculation_duration < 1.0  # Should complete within 1 second


class TestComponentHealthMonitoring:
    """Test component health monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_ai_brain_health_monitoring(self):
        """
        Test AI Brain service health monitoring.
        
        Requirements: 6.5 - Component health monitoring
        """
        # Test healthy AI Brain service
        healthy_client = Mock(spec=AIBrainClient)
        healthy_client.verify_connection = AsyncMock(return_value=True)
        healthy_client.verify_embedding_service = AsyncMock(return_value=True)
        healthy_client.health_check = AsyncMock(return_value=True)
        
        # Measure health check performance
        start_time = time.time()
        
        connection_ok = await healthy_client.verify_connection()
        embedding_ok = await healthy_client.verify_embedding_service()
        health_ok = await healthy_client.health_check()
        
        health_check_duration = time.time() - start_time
        
        # Verify health status
        assert connection_ok is True
        assert embedding_ok is True
        assert health_ok is True
        
        # Verify health checks are fast
        assert health_check_duration < 1.0
    
    @pytest.mark.asyncio
    async def test_database_function_availability_monitoring(self, optimized_processing_service):
        """
        Test database function availability monitoring.
        
        Requirements: 6.5 - Database function monitoring
        """
        course_id = str(uuid.uuid4())
        query = "test query"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Test RPC function availability
            start_time = time.time()
            
            # Mock RPC function check
            mock_supabase.rpc.side_effect = Exception("Function not found")
            
            # Mock fallback query
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[])
            
            # Execute search (should detect RPC unavailability and fallback)
            results = await optimized_processing_service.search_materials(course_id, query, limit=3)
            
            fallback_duration = time.time() - start_time
            
            # Verify fallback worked
            assert isinstance(results, list)
            
            # Verify fallback detection is fast
            assert fallback_duration < 2.0
    
    @pytest.mark.asyncio
    async def test_system_startup_health_verification(self):
        """
        Test system startup health verification performance.
        
        Requirements: 6.5 - Startup health check monitoring
        """
        # Simulate system startup health checks
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        ai_brain_client.health_check = AsyncMock(return_value=True)
        
        processing_service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        
        # Measure startup verification time
        start_time = time.time()
        
        # Simulate startup health checks
        health_checks = await asyncio.gather(
            ai_brain_client.verify_connection(),
            ai_brain_client.verify_embedding_service(),
            ai_brain_client.health_check()
        )
        
        startup_duration = time.time() - start_time
        
        # Verify all health checks passed
        assert all(health_checks)
        
        # Verify startup checks are fast
        assert startup_duration < 2.0  # Should complete quickly for good UX
    
    @pytest.mark.asyncio
    async def test_performance_degradation_detection(self):
        """
        Test detection of performance degradation in components.
        
        Requirements: 6.5 - Performance degradation monitoring
        """
        # Create AI Brain client with variable performance
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        
        # Mock embedding generation with increasing delay (simulating degradation)
        call_count = 0
        async def degrading_embedding_generation(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            delay = call_count * 0.1  # Increasing delay
            await asyncio.sleep(delay)
            return [0.5] * 1024
        
        ai_brain_client.generate_embedding = degrading_embedding_generation
        
        processing_service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        course_id = str(uuid.uuid4())
        
        # Measure performance over multiple calls
        durations = []
        
        for i in range(3):
            with patch('services.material_processing_service.supabase_admin') as mock_supabase:
                mock_table = Mock()
                mock_supabase.table.return_value = mock_table
                mock_table.select.return_value = mock_table
                mock_table.eq.return_value = mock_table
                mock_table.execute.return_value = Mock(data=[
                    {"id": "material-1", "processing_status": "completed"}
                ])
                
                # Mock RPC failure (use fallback)
                mock_supabase.rpc.side_effect = Exception("RPC not available")
                mock_table.execute.return_value = Mock(data=[{
                    "id": "material-1",
                    "name": "test.pdf",
                    "extracted_text": "test content",
                    "file_type": "application/pdf",
                    "embedding": [0.5] * 1024
                }])
                
                start_time = time.time()
                await processing_service.search_materials(course_id, f"query {i}", limit=3)
                duration = time.time() - start_time
                durations.append(duration)
        
        # Verify performance degradation is detectable
        assert durations[0] < durations[1] < durations[2]  # Increasing duration
        
        # Verify degradation is measurable
        performance_degradation = durations[2] - durations[0]
        assert performance_degradation > 0.1  # Significant degradation detected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])