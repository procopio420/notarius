# Notarius API Documentation

## Overview

The Notarius API provides a comprehensive REST interface for managing Brazilian notary office workflows, documents, and AI-assisted processes.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Staging**: `https://staging.notarius.ai/api/`
- **Production**: `https://api.notarius.ai/api/`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response**:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "your-username",
    "email": "user@example.com"
  }
}
```

## Core Resources

### Tenants

Manage cartório (notary office) information.

#### List Tenants

```http
GET /api/tenants/
```

**Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "nome": "Cartório de Teste",
      "uf": "SP",
      "settings": {},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Tenant

```http
POST /api/tenants/
Content-Type: application/json

{
  "nome": "Cartório de Teste",
  "uf": "SP",
  "settings": {
    "custom_field": "value"
  }
}
```

### Processes

Manage legal processes (processos).

#### List Processes

```http
GET /api/processos/
```

**Query Parameters**:
- `tipo_ato`: Filter by act type (procuracao, certidao, testamento, etc.)
- `status`: Filter by status (ativo, finalizado, etc.)
- `search`: Search in process data

**Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "tipo_ato": "procuracao",
      "status": "ativo",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Process

```http
POST /api/processos/
Content-Type: application/json

{
  "tipo_ato": "procuracao",
  "status": "ativo"
}
```

### Parties

Manage parties (partes) with PII tokenization.

#### List Parties

```http
GET /api/partes/
```

**Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "tipo": "pf",
      "tipo_pessoa": "pf",
      "nome_token": "token://party_1_name/uuid",
      "cpf_token": "token://party_1_cpf/uuid",
      "metadata": {},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Party

```http
POST /api/partes/
Content-Type: application/json

{
  "tipo": "pf",
  "tipo_pessoa": "pf",
  "nome_token": "token://party_1_name/uuid",
  "cpf_token": "token://party_1_cpf/uuid",
  "metadata": {
    "custom_field": "value"
  }
}
```

### Documents

Manage final documents.

#### List Documents

```http
GET /api/documentos/
```

**Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "processo": "uuid",
      "s3_key": "documents/final-document.pdf",
      "mime": "application/pdf",
      "pages": 2,
      "status": "pronto",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Minutas

Manage document drafts.

#### List Minutas

```http
GET /api/minutas/
```

**Query Parameters**:
- `processo`: Filter by process ID
- `status`: Filter by status (rascunho, aprovado, rejeitado, finalizado)
- `gerada_por`: Filter by generation method (usuario, ai)

**Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "processo": "uuid",
      "corpo_md": "# Minuta\n\nConteúdo da minuta...",
      "variaveis_json": {
        "PARTY_1_NAME": "token://party_1_name/uuid"
      },
      "status": "rascunho",
      "versao": 1,
      "gerada_por": "ai",
      "citations": [
        {
          "title": "Código de Normas CGJ-SP",
          "anchor": "Art. 678, §3º",
          "snippet": "Poderes gerais para representação judicial...",
          "confidence": 0.92
        }
      ],
      "grounding_confidence": 0.88,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Minuta

```http
POST /api/minutas/
Content-Type: application/json

{
  "processo": "uuid",
  "corpo_md": "# Minuta\n\nConteúdo da minuta...",
  "variaveis_json": {
    "PARTY_1_NAME": "token://party_1_name/uuid"
  },
  "gerada_por": "usuario"
}
```

### Document Templates

Manage customizable document templates.

#### List Templates

```http
GET /api/document-templates/
```

**Query Parameters**:
- `document_type`: Filter by document type
- `is_default`: Filter by default status
- `is_active`: Filter by active status

**Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Procuração Padrão",
      "document_type": "procuracao",
      "template_path": "procuracao.html",
      "is_default": true,
      "is_active": true,
      "version": "1.0",
      "custom_css": "",
      "custom_js": "",
      "custom_fields": {},
      "description": "Template padrão para procurações",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Template by Type

```http
GET /api/document-templates/by_type/?document_type=procuracao
```

## AI Features

### Generate Minuta from Intent

Generate a minuta from natural language input.

```http
POST /api/ai/generate-minuta/
Content-Type: application/json

{
  "command": "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP",
  "processo_id": "uuid"
}
```

**Response**:
```json
{
  "minuta_id": "uuid",
  "status": "rascunho",
  "preview": "# PROCURAÇÃO\n\nOutorgante: {{PARTY_1_NAME}}...",
  "confidence": 0.88,
  "citations": [
    {
      "title": "Código de Normas CGJ-SP",
      "anchor": "Art. 678, §3º",
      "snippet": "Poderes gerais para representação judicial...",
      "confidence": 0.92
    }
  ]
}
```

### Approve Minuta

Approve a minuta for finalization.

```http
POST /api/ai/approve-minuta/{minuta_id}/
```

**Response**:
```json
{
  "minuta_id": "uuid",
  "status": "aprovado",
  "approved_at": "2024-01-01T00:00:00Z",
  "approved_by": "uuid"
}
```

### Finalize Minuta

Finalize an approved minuta and generate the final document.

```http
POST /api/ai/finalize-minuta/{minuta_id}/
```

**Response**:
```json
{
  "minuta_id": "uuid",
  "status": "finalizado",
  "finalized_at": "2024-01-01T00:00:00Z",
  "document_id": "uuid",
  "s3_key": "documents/final-document.pdf"
}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format.

### Error Response Format

```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Specific field error"]
  },
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Example Error Response

```json
{
  "error": "Validation failed",
  "details": {
    "tipo_ato": ["This field is required."],
    "status": ["Invalid choice."]
  },
  "code": "VALIDATION_ERROR"
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination using cursor-based pagination:

### Request

```http
GET /api/minutas/?page=2&page_size=20
```

### Response

```json
{
  "count": 100,
  "next": "http://api.notarius.ai/api/minutas/?page=3&page_size=20",
  "previous": "http://api.notarius.ai/api/minutas/?page=1&page_size=20",
  "results": [...]
}
```

## Filtering and Searching

Most list endpoints support filtering and searching:

### Filtering

```http
GET /api/minutas/?status=aprovado&gerada_por=ai
```

### Searching

```http
GET /api/processos/?search=procuração
```

### Ordering

```http
GET /api/minutas/?ordering=-created_at
```

## Webhooks

The API supports webhooks for real-time notifications:

### Register Webhook

```http
POST /api/webhooks/
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["minuta.approved", "document.finalized"],
  "secret": "your-webhook-secret"
}
```

### Webhook Payload

```json
{
  "event": "minuta.approved",
  "data": {
    "minuta_id": "uuid",
    "status": "aprovado",
    "approved_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## SDKs and Libraries

### Python

```python
import requests

class NotariusClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def generate_minuta(self, command, processo_id):
        response = requests.post(
            f'{self.base_url}/api/ai/generate-minuta/',
            json={
                'command': command,
                'processo_id': processo_id
            },
            headers=self.headers
        )
        return response.json()

# Usage
client = NotariusClient('http://localhost:8000', 'your-token')
result = client.generate_minuta(
    'Fazer procuração para João Silva',
    'processo-uuid'
)
```

### JavaScript

```javascript
class NotariusClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async generateMinuta(command, processoId) {
    const response = await fetch(`${this.baseUrl}/api/ai/generate-minuta/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        command,
        processo_id: processoId
      })
    });
    return response.json();
  }
}

// Usage
const client = new NotariusClient('http://localhost:8000', 'your-token');
const result = await client.generateMinuta(
  'Fazer procuração para João Silva',
  'processo-uuid'
);
```

## Testing

### Postman Collection

Import the Notarius API Postman collection for easy testing:

[Download Collection](https://api.notarius.ai/docs/postman-collection.json)

### cURL Examples

#### Generate Minuta

```bash
curl -X POST http://localhost:8000/api/ai/generate-minuta/ \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Fazer procuração para João Silva, CPF 123.456.789-00",
    "processo_id": "uuid"
  }'
```

#### List Minutas

```bash
curl -X GET http://localhost:8000/api/minutas/ \
  -H "Authorization: Bearer your-token"
```

## Changelog

### v1.0.0 (2024-01-01)
- Initial API release
- Core CRUD operations for all resources
- AI minuta generation
- Document template management
- PII tokenization support

### v1.1.0 (2024-02-01)
- Webhook support
- Advanced filtering and searching
- Rate limiting
- Improved error handling

---

For more information, visit our [documentation site](https://docs.notarius.ai) or contact support at api-support@notarius.ai.
