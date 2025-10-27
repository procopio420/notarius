"""
Tests for core models.
"""
import pytest
from datetime import datetime
from packages.core.models import BaseModel, TimestampedModel


class TestBaseModel:
    """Test cases for BaseModel."""
    
    def test_base_model_creation(self):
        """Test creating a BaseModel instance."""
        model = BaseModel()
        
        assert hasattr(model, 'id')
        assert model.id is not None
    
    def test_base_model_id_uniqueness(self):
        """Test that BaseModel IDs are unique."""
        model1 = BaseModel()
        model2 = BaseModel()
        
        assert model1.id != model2.id
    
    def test_base_model_str_representation(self):
        """Test BaseModel string representation."""
        model = BaseModel()
        
        str_repr = str(model)
        assert "BaseModel" in str_repr
        assert str(model.id) in str_repr


class TestTimestampedModel:
    """Test cases for TimestampedModel."""
    
    def test_timestamped_model_creation(self):
        """Test creating a TimestampedModel instance."""
        model = TimestampedModel()
        
        assert hasattr(model, 'id')
        assert hasattr(model, 'created_at')
        assert hasattr(model, 'updated_at')
        
        assert model.created_at is not None
        assert model.updated_at is not None
    
    def test_timestamped_model_timestamps(self):
        """Test that timestamps are set correctly."""
        before_creation = datetime.utcnow()
        model = TimestampedModel()
        after_creation = datetime.utcnow()
        
        assert before_creation <= model.created_at <= after_creation
        assert before_creation <= model.updated_at <= after_creation
        assert model.created_at == model.updated_at
    
    def test_timestamped_model_update_timestamp(self):
        """Test that updated_at changes on update."""
        model = TimestampedModel()
        original_updated_at = model.updated_at
        
        # Simulate update
        model.updated_at = datetime.utcnow()
        
        assert model.updated_at > original_updated_at
        assert model.created_at < model.updated_at
    
    def test_timestamped_model_str_representation(self):
        """Test TimestampedModel string representation."""
        model = TimestampedModel()
        
        str_repr = str(model)
        assert "TimestampedModel" in str_repr
        assert str(model.id) in str_repr
