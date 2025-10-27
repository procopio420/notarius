"""
Tests for correlation ID functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from packages.observability.correlation import (
    get_correlation_id, set_correlation_id, 
    clear_correlation_id, correlation_id_context
)


class TestCorrelationID:
    """Test cases for correlation ID functionality."""
    
    def test_get_correlation_id_none(self):
        """Test getting correlation ID when none is set."""
        clear_correlation_id()
        correlation_id = get_correlation_id()
        
        assert correlation_id is None
    
    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = "test-correlation-id-123"
        
        set_correlation_id(test_id)
        correlation_id = get_correlation_id()
        
        assert correlation_id == test_id
    
    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        test_id = "test-correlation-id-123"
        
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
        
        clear_correlation_id()
        assert get_correlation_id() is None
    
    def test_correlation_id_context(self):
        """Test correlation ID context manager."""
        test_id = "test-correlation-id-123"
        
        with correlation_id_context(test_id):
            assert get_correlation_id() == test_id
        
        # Should be cleared after context
        assert get_correlation_id() is None
    
    def test_correlation_id_context_nested(self):
        """Test nested correlation ID contexts."""
        outer_id = "outer-correlation-id"
        inner_id = "inner-correlation-id"
        
        with correlation_id_context(outer_id):
            assert get_correlation_id() == outer_id
            
            with correlation_id_context(inner_id):
                assert get_correlation_id() == inner_id
            
            # Should restore outer ID
            assert get_correlation_id() == outer_id
        
        # Should be cleared after all contexts
        assert get_correlation_id() is None
    
    def test_correlation_id_context_exception(self):
        """Test correlation ID context with exception."""
        test_id = "test-correlation-id-123"
        
        try:
            with correlation_id_context(test_id):
                assert get_correlation_id() == test_id
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should be cleared even after exception
        assert get_correlation_id() is None
    
    def test_correlation_id_format(self):
        """Test correlation ID format."""
        test_id = "test-correlation-id-123"
        
        set_correlation_id(test_id)
        correlation_id = get_correlation_id()
        
        # Should preserve the exact format
        assert correlation_id == test_id
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0
    
    def test_correlation_id_thread_safety(self):
        """Test correlation ID thread safety."""
        import threading
        import time
        
        results = {}
        
        def set_and_get_id(thread_id):
            test_id = f"thread-{thread_id}-correlation-id"
            set_correlation_id(test_id)
            time.sleep(0.01)  # Small delay
            results[thread_id] = get_correlation_id()
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=set_and_get_id, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Each thread should have its own correlation ID
        for thread_id, correlation_id in results.items():
            assert correlation_id == f"thread-{thread_id}-correlation-id"
