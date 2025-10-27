# Notarius Architecture

## System Overview

Notarius is a privacy-first, multi-tenant AI system designed for Brazilian notary offices. The architecture ensures complete PII protection while providing powerful AI-assisted document generation capabilities.

## Core Principles

1. **Privacy by Design**: No PII ever leaves the system unencrypted
2. **Multi-tenancy**: Complete isolation between cartórios
3. **Audit Everything**: Full audit trail for compliance
4. **Human-in-the-Loop**: AI assists, humans decide
5. **Legal Grounding**: All content backed by actual Brazilian law

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Notarius System Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Client    │    │   Client    │    │   Client    │        │
│  │ (Browser)   │    │ (Mobile)    │    │  (Admin)    │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                API Gateway (Traefik)                       ││
│  │  - Load Balancing  - SSL Termination  - Rate Limiting     ││
│  └─────────────────────────────────────────────────────────────┘│
│                             │                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Application Layer                       ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ││
│  │  │ Notarius    │  │ LexNode     │  │ PII Vault   │        ││
│  │  │ (Django)    │  │ (FastAPI)   │  │ (FastAPI)   │        ││
│  │  │ Port 8000   │  │ Port 8001   │  │ Port 8002   │        ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘        ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ││
│  │  │ Intent      │  │ Frontend    │  │ Observability│       ││
│  │  │ Engine      │  │ (Next.js)   │  │ (Grafana)   │        ││
│  │  │ (FastAPI)   │  │ Port 3000   │  │ Port 3001   │        ││
│  │  │ Port 8003   │  │             │  │             │        ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
│                             │                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Data Layer                              ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ││
│  │  │ Notarius    │  │ LexNode     │  │ PII Vault   │        ││
│  │  │ Database    │  │ Database    │  │ Database    │        ││
│  │  │ (Postgres)  │  │ (Postgres   │  │ (Postgres   │        ││
│  │  │             │  │ + pgvector) │  │ + KMS)      │        ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘        ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ││
│  │  │ Redis       │  │ S3 Storage  │  │ KMS         │        ││
│  │  │ (Cache)     │  │ (Documents) │  │ (Encryption)│        ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Service Architecture

### 1. Notarius API (Django)

**Purpose**: Core business logic, multi-tenancy, document management

**Responsibilities**:
- User authentication and authorization
- Multi-tenant data isolation
- Document and minuta management
- Integration with AI services
- Audit logging

**Key Components**:
- `apps/base/`: Multi-tenancy foundation
- `apps/documentos/`: Document management
- `apps/partes/`: Party management with PII tokens
- `apps/processos/`: Process workflow
- `apps/ai/`: AI service integration

### 2. PII Vault (FastAPI)

**Purpose**: Secure PII storage and tokenization

**Responsibilities**:
- Encrypt and store PII data
- Generate and manage tokens
- Provide detokenization with audit
- KMS integration for key management

**Key Components**:
- `models.py`: Encrypted token storage
- `routes/vault.py`: Tokenization/detokenization API
- `kms.py`: Key management integration
- `audit.py`: Audit logging

### 3. LexNode (FastAPI)

**Purpose**: Legal knowledge retrieval and grounding

**Responsibilities**:
- Crawl and index Brazilian legal documents
- Provide semantic search over legal corpus
- Generate grounded legal content
- Citation management

**Key Components**:
- `crawler/`: Legal document crawlers
- `indexer/`: Vector and text indexing
- `retrieval/`: Hybrid search (BM25 + vectors)
- `normalizer/`: Legal document parsing

### 4. Intent Engine (FastAPI)

**Purpose**: Natural language understanding and draft generation

**Responsibilities**:
- Parse natural language intents
- Generate document drafts
- Coordinate with LexNode for grounding
- Manage document templates

**Key Components**:
- `parser/`: Intent parsing with TRELLIS framework
- `generator/`: Draft generation pipeline
- `templates/`: Document template management
- `cache/`: Draft caching system

### 5. Frontend (Next.js)

**Purpose**: Human-in-the-loop document editing

**Responsibilities**:
- Rich text editor with AI suggestions
- Citation display and management
- Approval workflow
- Real-time collaboration

**Key Components**:
- `components/editor/`: TipTap-based editor
- `components/citations/`: Legal citation display
- `store/`: State management with Zustand
- `hooks/`: API integration hooks

## Data Flow

### 1. Document Generation Flow

```
User Input → Intent Engine → PII Vault → LexNode → Draft Generation → HITL Editor → Approval → Finalization
```

**Detailed Steps**:

1. **User Input**: "Fazer procuração para João Silva, CPF 123.456.789-00"
2. **Intent Parsing**: Extract act type, parties, powers
3. **PII Tokenization**: Replace PII with encrypted tokens
4. **Legal Retrieval**: Query LexNode for relevant legal content
5. **Draft Generation**: Combine template + legal content + tokens
6. **Human Review**: Editor reviews and modifies draft
7. **Approval**: Human approves final version
8. **Finalization**: Detokenize PII, generate PDF, store

### 2. PII Protection Flow

```
Raw PII → PII Vault → Encrypted Token → AI Services → Detokenization → Final Document
```

**Security Guarantees**:
- No raw PII in AI service payloads
- All PII operations audited
- KMS-encrypted storage
- Tenant isolation

## Database Design

### 1. Notarius Database (PostgreSQL)

**Core Tables**:
- `tenants`: Cartório information
- `processos`: Legal processes
- `partes`: Parties with PII tokens
- `minutas`: Document drafts
- `documentos`: Final documents
- `document_templates`: Customizable templates

**Key Features**:
- Multi-tenant isolation
- PII tokenization
- Audit trails
- Soft deletes

### 2. LexNode Database (PostgreSQL + pgvector)

**Core Tables**:
- `legal_documents`: Crawled legal documents
- `legal_chunks`: Vectorized content chunks
- `citations`: Legal citations and references

**Key Features**:
- Vector similarity search
- Full-text search (BM25)
- Legal document metadata
- Citation tracking

### 3. PII Vault Database (PostgreSQL + KMS)

**Core Tables**:
- `encrypted_tokens`: Encrypted PII storage
- `vault_audit_log`: Audit trail

**Key Features**:
- KMS-encrypted storage
- Token lifecycle management
- Complete audit trail
- RBAC integration

## Security Architecture

### 1. Encryption

- **At Rest**: KMS-encrypted database fields
- **In Transit**: TLS 1.3 for all communications
- **Key Management**: AWS KMS or GCP KMS
- **Token Encryption**: AES-256-GCM

### 2. Authentication & Authorization

- **JWT Tokens**: Stateless authentication
- **RBAC**: Role-based access control
- **Tenant Isolation**: Complete data separation
- **API Keys**: Service-to-service authentication

### 3. Audit & Compliance

- **Audit Logging**: All PII operations logged
- **Correlation IDs**: Request tracing across services
- **Data Retention**: Configurable retention policies
- **LGPD Compliance**: Brazilian data protection law

## Monitoring & Observability

### 1. Metrics

- **Application Metrics**: Request rates, latencies, errors
- **Business Metrics**: Document generation rates, approval times
- **Security Metrics**: PII operations, audit events
- **Infrastructure Metrics**: CPU, memory, disk usage

### 2. Logging

- **Structured Logging**: JSON format with correlation IDs
- **PII Redaction**: Automatic PII removal from logs
- **Log Aggregation**: Centralized log collection
- **Retention**: Configurable log retention

### 3. Tracing

- **Distributed Tracing**: OpenTelemetry integration
- **Service Maps**: Visual service dependencies
- **Performance Analysis**: Request flow analysis
- **Error Tracking**: Exception and error monitoring

## Deployment Architecture

### 1. Development

- **Docker Compose**: Local development environment
- **SQLite**: Simple database for development
- **Mock Services**: Simplified AI services for testing

### 2. Staging

- **Kubernetes**: Container orchestration
- **PostgreSQL**: Production database
- **Redis**: Caching and session storage
- **S3**: Document storage

### 3. Production

- **AWS/GCP**: Cloud infrastructure
- **ECS/GKE**: Container orchestration
- **RDS**: Managed PostgreSQL
- **ElastiCache**: Managed Redis
- **S3/GCS**: Object storage
- **KMS**: Key management
- **CloudWatch/GCP Monitoring**: Observability

## Scalability Considerations

### 1. Horizontal Scaling

- **Stateless Services**: All services are stateless
- **Load Balancing**: Multiple service instances
- **Database Sharding**: Tenant-based sharding
- **Cache Distribution**: Redis clustering

### 2. Performance Optimization

- **Caching**: Multi-level caching strategy
- **Database Optimization**: Indexes and query optimization
- **CDN**: Static asset delivery
- **Connection Pooling**: Database connection management

### 3. Data Partitioning

- **Tenant Isolation**: Separate data per tenant
- **Time-based Partitioning**: Historical data management
- **Archive Strategy**: Long-term data retention

## Future Enhancements

### 1. Advanced AI Features

- **Multi-modal AI**: Image and document processing
- **Advanced NLP**: Better intent understanding
- **Legal Reasoning**: Automated legal analysis
- **Predictive Analytics**: Document outcome prediction

### 2. Integration Ecosystem

- **e-Notariado**: Brazilian notary system integration
- **CRC**: Real estate registry integration
- **Selo Digital**: Digital signature integration
- **Third-party APIs**: External service integration

### 3. Mobile & Accessibility

- **Mobile App**: Native mobile application
- **Offline Support**: Offline document editing
- **Accessibility**: WCAG compliance
- **Multi-language**: Internationalization support

---

This architecture provides a solid foundation for a privacy-first, scalable, and maintainable AI system for Brazilian notary offices.
