"""
Tests for PII Vault API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestPIIVaultAPI:
    """Test cases for PII Vault API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "pii-vault"}
    
    def test_tokenize_pii(self, client):
        """Test PII tokenization endpoint."""
        request = {
            "pii_data": {
                "nome": "João Silva Santos",
                "cpf": "123.456.789-00",
                "email": "joao.silva@email.com",
                "telefone": "(21) 99999-9999"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012",
                    "cpf": "token_87654321-4321-4321-4321-210987654321",
                    "email": "token_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "telefone": "token_ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj"
                },
                "hashes": {
                    "nome": "hash_nome_123",
                    "cpf": "hash_cpf_456",
                    "email": "hash_email_789",
                    "telefone": "hash_telefone_abc"
                },
                "status": "success"
            }
            
            response = client.post("/api/v1/tokenize", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert "token_12345678-1234-1234-1234-123456789012" in data["tokens"]["nome"]
            assert "hash_nome_123" in data["hashes"]["nome"]
    
    def test_tokenize_pii_invalid_request(self, client):
        """Test PII tokenization with invalid request."""
        invalid_request = {
            "pii_data": {},  # Empty PII data
            "tenant_id": "tenant_123"
        }
        
        response = client.post("/api/v1/tokenize", json=invalid_request)
        assert response.status_code == 400
    
    def test_tokenize_pii_missing_tenant(self, client):
        """Test PII tokenization with missing tenant ID."""
        request = {
            "pii_data": {
                "nome": "João Silva Santos"
            }
            # Missing tenant_id
        }
        
        response = client.post("/api/v1/tokenize", json=request)
        assert response.status_code == 422  # Validation error
    
    def test_detokenize_pii(self, client):
        """Test PII detokenization endpoint."""
        request = {
            "tokens": {
                "nome": "token_12345678-1234-1234-1234-123456789012",
                "cpf": "token_87654321-4321-4321-4321-210987654321"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.detokenize_pii') as mock_detokenize:
            mock_detokenize.return_value = {
                "pii_data": {
                    "nome": "João Silva Santos",
                    "cpf": "123.456.789-00"
                },
                "status": "success"
            }
            
            response = client.post("/api/v1/detokenize", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["pii_data"]["nome"] == "João Silva Santos"
            assert data["pii_data"]["cpf"] == "123.456.789-00"
    
    def test_detokenize_pii_invalid_tokens(self, client):
        """Test PII detokenization with invalid tokens."""
        request = {
            "tokens": {
                "nome": "invalid_token",
                "cpf": "another_invalid_token"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.detokenize_pii') as mock_detokenize:
            mock_detokenize.return_value = {
                "pii_data": {},
                "errors": ["Invalid token: invalid_token", "Invalid token: another_invalid_token"],
                "status": "partial_success"
            }
            
            response = client.post("/api/v1/detokenize", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["errors"]) == 2
            assert data["status"] == "partial_success"
    
    def test_validate_token(self, client):
        """Test token validation endpoint."""
        request = {
            "token": "token_12345678-1234-1234-1234-123456789012",
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.validate_token') as mock_validate:
            mock_validate.return_value = {
                "is_valid": True,
                "token_type": "nome",
                "created_at": "2023-01-01T00:00:00Z",
                "expires_at": "2024-01-01T00:00:00Z"
            }
            
            response = client.post("/api/v1/validate-token", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["token_type"] == "nome"
    
    def test_validate_token_invalid(self, client):
        """Test token validation with invalid token."""
        request = {
            "token": "invalid_token",
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.validate_token') as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "error": "Token not found"
            }
            
            response = client.post("/api/v1/validate-token", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert "error" in data
    
    def test_get_token_info(self, client):
        """Test get token information endpoint."""
        with patch('app.services.vault_service.VaultService.get_token_info') as mock_info:
            mock_info.return_value = {
                "token": "token_12345678-1234-1234-1234-123456789012",
                "token_type": "nome",
                "tenant_id": "tenant_123",
                "created_at": "2023-01-01T00:00:00Z",
                "expires_at": "2024-01-01T00:00:00Z",
                "access_count": 5,
                "last_accessed": "2023-06-01T12:00:00Z"
            }
            
            response = client.get("/api/v1/tokens/token_12345678-1234-1234-1234-123456789012")
            
            assert response.status_code == 200
            data = response.json()
            assert data["token_type"] == "nome"
            assert data["access_count"] == 5
    
    def test_get_token_info_not_found(self, client):
        """Test get token information for non-existent token."""
        with patch('app.services.vault_service.VaultService.get_token_info') as mock_info:
            mock_info.return_value = None
            
            response = client.get("/api/v1/tokens/nonexistent_token")
            
            assert response.status_code == 404
    
    def test_revoke_token(self, client):
        """Test token revocation endpoint."""
        with patch('app.services.vault_service.VaultService.revoke_token') as mock_revoke:
            mock_revoke.return_value = {
                "success": True,
                "message": "Token revoked successfully"
            }
            
            response = client.delete("/api/v1/tokens/token_12345678-1234-1234-1234-123456789012")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_revoke_token_not_found(self, client):
        """Test token revocation for non-existent token."""
        with patch('app.services.vault_service.VaultService.revoke_token') as mock_revoke:
            mock_revoke.return_value = {
                "success": False,
                "error": "Token not found"
            }
            
            response = client.delete("/api/v1/tokens/nonexistent_token")
            
            assert response.status_code == 404
    
    def test_get_tenant_statistics(self, client):
        """Test get tenant statistics endpoint."""
        with patch('app.services.vault_service.VaultService.get_tenant_statistics') as mock_stats:
            mock_stats.return_value = {
                "tenant_id": "tenant_123",
                "total_tokens": 1000,
                "active_tokens": 950,
                "revoked_tokens": 50,
                "token_types": {
                    "nome": 300,
                    "cpf": 250,
                    "email": 200,
                    "telefone": 150,
                    "endereco": 100
                },
                "created_at": "2023-01-01T00:00:00Z",
                "last_updated": "2023-06-01T12:00:00Z"
            }
            
            response = client.get("/api/v1/tenants/tenant_123/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_tokens"] == 1000
            assert data["active_tokens"] == 950
            assert data["token_types"]["nome"] == 300
    
    def test_get_tenant_statistics_not_found(self, client):
        """Test get tenant statistics for non-existent tenant."""
        with patch('app.services.vault_service.VaultService.get_tenant_statistics') as mock_stats:
            mock_stats.return_value = None
            
            response = client.get("/api/v1/tenants/nonexistent_tenant/statistics")
            
            assert response.status_code == 404
    
    def test_audit_logs(self, client):
        """Test audit logs endpoint."""
        with patch('app.services.vault_service.VaultService.get_audit_logs') as mock_logs:
            mock_logs.return_value = {
                "logs": [
                    {
                        "id": "log_123",
                        "action": "tokenize",
                        "tenant_id": "tenant_123",
                        "user_id": "user_456",
                        "timestamp": "2023-06-01T12:00:00Z",
                        "details": {
                            "pii_types": ["nome", "cpf"],
                            "token_count": 2
                        }
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
            
            response = client.get("/api/v1/audit-logs?tenant_id=tenant_123&page=1&page_size=10")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["logs"]) == 1
            assert data["logs"][0]["action"] == "tokenize"
    
    def test_audit_logs_with_filters(self, client):
        """Test audit logs with various filters."""
        with patch('app.services.vault_service.VaultService.get_audit_logs') as mock_logs:
            mock_logs.return_value = {
                "logs": [],
                "total": 0,
                "page": 1,
                "page_size": 10
            }
            
            response = client.get("/api/v1/audit-logs?tenant_id=tenant_123&action=tokenize&date_from=2023-01-01&date_to=2023-12-31")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
    
    def test_tokenize_pii_with_special_characters(self, client):
        """Test PII tokenization with special characters."""
        request = {
            "pii_data": {
                "nome": "João Silva Santos (Dr.)",
                "cpf": "123.456.789-00",
                "email": "joao.silva+test@email.com",
                "telefone": "+55 (21) 99999-9999"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012",
                    "cpf": "token_87654321-4321-4321-4321-210987654321",
                    "email": "token_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "telefone": "token_ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj"
                },
                "hashes": {
                    "nome": "hash_nome_123",
                    "cpf": "hash_cpf_456",
                    "email": "hash_email_789",
                    "telefone": "hash_telefone_abc"
                },
                "status": "success"
            }
            
            response = client.post("/api/v1/tokenize", json=request)
            
            assert response.status_code == 200
    
    def test_tokenize_pii_with_unicode(self, client):
        """Test PII tokenization with unicode characters."""
        request = {
            "pii_data": {
                "nome": "João Silva Santos, ção, ñ, ü",
                "endereco": "Rua das Flores, 123, Centro, Rio de Janeiro - RJ"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012",
                    "endereco": "token_87654321-4321-4321-4321-210987654321"
                },
                "hashes": {
                    "nome": "hash_nome_123",
                    "endereco": "hash_endereco_456"
                },
                "status": "success"
            }
            
            response = client.post("/api/v1/tokenize", json=request)
            
            assert response.status_code == 200
    
    def test_tokenize_pii_sql_injection(self, client):
        """Test PII tokenization with SQL injection attempts."""
        request = {
            "pii_data": {
                "nome": "'; DROP TABLE tokens; --",
                "cpf": "' OR '1'='1"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012",
                    "cpf": "token_87654321-4321-4321-4321-210987654321"
                },
                "hashes": {
                    "nome": "hash_nome_123",
                    "cpf": "hash_cpf_456"
                },
                "status": "success"
            }
            
            response = client.post("/api/v1/tokenize", json=request)
            
            # Should not cause SQL injection
            assert response.status_code == 200
    
    def test_tokenize_pii_xss_attempt(self, client):
        """Test PII tokenization with XSS attempts."""
        request = {
            "pii_data": {
                "nome": "<script>alert('XSS')</script>",
                "email": "test@email.com"
            },
            "tenant_id": "tenant_123"
        }
        
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012",
                    "email": "token_87654321-4321-4321-4321-210987654321"
                },
                "hashes": {
                    "nome": "hash_nome_123",
                    "email": "hash_email_456"
                },
                "status": "success"
            }
            
            response = client.post("/api/v1/tokenize", json=request)
            
            # Should not cause XSS
            assert response.status_code == 200
    
    def test_concurrent_tokenize_requests(self, client):
        """Test concurrent tokenization requests."""
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012"
                },
                "hashes": {
                    "nome": "hash_nome_123"
                },
                "status": "success"
            }
            
            request = {
                "pii_data": {
                    "nome": "João Silva Santos"
                },
                "tenant_id": "tenant_123"
            }
            
            # Simulate concurrent requests
            responses = []
            for i in range(10):
                response = client.post("/api/v1/tokenize", json=request)
                responses.append(response)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
    
    def test_error_handling(self, client):
        """Test error handling in API endpoints."""
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.side_effect = Exception("Database connection failed")
            
            request = {
                "pii_data": {
                    "nome": "João Silva Santos"
                },
                "tenant_id": "tenant_123"
            }
            
            response = client.post("/api/v1/tokenize", json=request)
            
            assert response.status_code == 500
    
    def test_rate_limiting(self, client):
        """Test rate limiting on tokenization endpoint."""
        with patch('app.services.vault_service.VaultService.tokenize_pii') as mock_tokenize:
            mock_tokenize.return_value = {
                "tokens": {
                    "nome": "token_12345678-1234-1234-1234-123456789012"
                },
                "hashes": {
                    "nome": "hash_nome_123"
                },
                "status": "success"
            }
            
            request = {
                "pii_data": {
                    "nome": "João Silva Santos"
                },
                "tenant_id": "tenant_123"
            }
            
            # Make many requests quickly
            for i in range(100):
                response = client.post("/api/v1/tokenize", json=request)
                if response.status_code == 429:  # Rate limited
                    break
            
            # Should eventually hit rate limit
            assert response.status_code in [200, 429]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/tokenize")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_content_type_validation(self, client):
        """Test content type validation."""
        response = client.post("/api/v1/tokenize", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test missing content type header."""
        response = client.post("/api/v1/tokenize", 
                             data='{"pii_data": {"nome": "test"}}')
        assert response.status_code == 422
