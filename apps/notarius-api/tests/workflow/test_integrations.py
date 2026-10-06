"""
Tests for integration stubs.
"""

import pytest
from workflow_orchestrator.integrations.enotariado import ENotariadoClient
from workflow_orchestrator.integrations.ri_central import RICentralClient
from workflow_orchestrator.integrations.rtdpj_central import RTDPJCentralClient
from workflow_orchestrator.integrations.protesto_central import ProtestoCentralClient


class TestENotariadoClient:
    """Test e-notariado client."""
    
    def test_create_session_returns_guid(self):
        """Test that create_session returns a GUID."""
        client = ENotariadoClient()
        session_id = client.create_session()
        
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format
    
    def test_submit_returns_guid(self):
        """Test that submit returns a GUID."""
        client = ENotariadoClient()
        submission_id = client.submit({"doc": "data"})
        
        assert isinstance(submission_id, str)
        assert len(submission_id) == 36
    
    def test_status_returns_dict(self):
        """Test that status returns a dictionary."""
        client = ENotariadoClient()
        session_id = client.create_session()
        status = client.status(session_id)
        
        assert isinstance(status, dict)
        assert "session_id" in status
        assert "status" in status


class TestRICentralClient:
    """Test RI central client."""
    
    def test_submit_returns_guid(self):
        """Test that submit returns a GUID."""
        client = RICentralClient()
        submission_id = client.submit(b"pdf bytes", {"metadata": "data"})
        
        assert isinstance(submission_id, str)
        assert len(submission_id) == 36
    
    def test_status_returns_dict(self):
        """Test that status returns a dictionary."""
        client = RICentralClient()
        submission_id = client.submit(b"pdf", {})
        status = client.status(submission_id)
        
        assert isinstance(status, dict)
        assert "submission_id" in status
        assert "status" in status


class TestRTDPJCentralClient:
    """Test RTD/RCPJ central client."""
    
    def test_register_returns_guid(self):
        """Test that register returns a GUID."""
        client = RTDPJCentralClient()
        registration_id = client.register(b"pdf bytes")
        
        assert isinstance(registration_id, str)
        assert len(registration_id) == 36
    
    def test_status_returns_dict(self):
        """Test that status returns a dictionary."""
        client = RTDPJCentralClient()
        registration_id = client.register(b"pdf")
        status = client.status(registration_id)
        
        assert isinstance(status, dict)
        assert "registration_id" in status
        assert "status" in status


class TestProtestoCentralClient:
    """Test Protesto central client."""
    
    def test_distribute_returns_guid(self):
        """Test that distribute returns a GUID."""
        client = ProtestoCentralClient()
        distribution_id = client.distribute({"title": "data"})
        
        assert isinstance(distribution_id, str)
        assert len(distribution_id) == 36
    
    def test_status_returns_dict(self):
        """Test that status returns a dictionary."""
        client = ProtestoCentralClient()
        distribution_id = client.distribute({"title": "data"})
        status = client.status(distribution_id)
        
        assert isinstance(status, dict)
        assert "distribution_id" in status
        assert "status" in status

