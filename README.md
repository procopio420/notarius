# Notarius - Privacy-First AI Notary System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)

> **Transform natural language into legally grounded documents with zero PII leaving your system**

Notarius is a production-grade, privacy-preserving AI system designed for Brazilian notary offices (cartórios). It transforms natural language intents into legally grounded documents, reviewed by humans, with complete PII protection and audit trails.

## 🎯 Key Features

### 🔒 **Privacy-First Architecture**
- **Zero PII in AI Services**: All sensitive data is tokenized before leaving your system
- **KMS-Encrypted Vault**: Military-grade encryption for PII storage
- **Audit Everything**: Complete audit trail for all PII operations
- **Tenant Isolation**: Complete data separation between cartórios

### 🤖 **AI-Powered Workflow**
- **Natural Language Processing**: "Fazer procuração para João Silva, CPF 123.456.789-00"
- **Legal Grounding**: Citations to actual Brazilian law (CNJ, CGJ-SP, etc.)
- **Human-in-the-Loop**: Rich editor with AI suggestions and human approval
- **Template System**: Customizable document templates per tenant

### 📋 **Document Management**
- **Multi-tenant**: Each cartório has isolated data and customizations
- **Version Control**: Track changes and approvals
- **PDF Generation**: Professional document output
- **Integration Ready**: e-Notariado, CRC, Selo Digital

## 🏗️ Architecture

### System Overview

Notarius is built as a microservices architecture with clear separation of concerns, ensuring privacy, scalability, and maintainability. The system is designed around a privacy-first approach where PII never leaves the secure vault environment.

### Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Notarius Docker Stack                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                           Frontend Layer                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐              ┌─────────────────────┐            │
│  │  Notarius Web      │◄─────────────┤     Traefik         │            │
│  │  (Next.js 15)      │              │  (API Gateway)      │            │
│  │  Port: 3000        │              │  Port: 80/443       │            │
│  │  - HITL Editor     │              │  - Load Balancing   │            │
│  │  - Dashboard       │              │  - SSL Termination  │            │
│  │  - Real-time UI    │              │  - Rate Limiting    │            │
│  └────────────────────┘              └─────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Notarius API    │  │  LexNode API    │  │ Intent Engine   │         │
│  │   (Django 5.2)  │  │   (FastAPI)     │  │   (FastAPI)     │         │
│  │   Port: 8000    │  │   Port: 8001    │  │   Port: 8003    │         │
│  │  - Multi-tenant │  │  - RAG Engine   │  │  - NLP Parser   │         │
│  │  - Auth & RBAC  │  │  - Legal KB     │  │  - Intent Class │         │
│  │  - Document Mgmt│  │  - Vector Search│  │  - AI Pipeline  │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│           │                    │                     │                   │
│           └────────────────────┼─────────────────────┘                   │
│                                │                                         │
│                      ┌─────────────────┐                                 │
│                      │   PII Vault     │                                 │
│                      │   (FastAPI)     │                                 │
│                      │   Port: 8002    │                                 │
│                      │  - Encryption   │                                 │
│                      │  - Tokenization │                                 │
│                      │  - Audit Logs   │                                 │
│                      └─────────────────┘                                 │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                           Data Layer                                     │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ PostgreSQL       │  │ PostgreSQL       │  │ PostgreSQL       │      │
│  │ (Notarius)       │  │ (LexNode)        │  │ (PII Vault)      │      │
│  │ Port: 5432       │  │ Port: 5433       │  │ Port: 5434       │      │
│  │ + pgvector       │  │ + pgvector       │  │ + encryption     │      │
│  │ - App Data       │  │ - Legal Docs     │  │ - Encrypted PII  │      │
│  │ - User Mgmt      │  │ - Embeddings     │  │ - Audit Trails   │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐                            │
│  │     Redis        │  │     MinIO        │                            │
│  │  (Cache/Queue)   │  │  (S3 Storage)    │                            │
│  │  Port: 6379      │  │  Port: 9000/9001 │                            │
│  │ - Session Cache  │  │ - Document Files │                            │
│  │ - Task Queue     │  │ - PDF Storage    │                            │
│  │ - Rate Limiting  │  │ - Media Assets   │                            │
│  └──────────────────┘  └──────────────────┘                            │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                        Observability Layer                               │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │    Grafana      │  │   Prometheus    │  │     Jaeger      │         │
│  │  (Dashboards)   │  │   (Metrics)     │  │   (Tracing)     │         │
│  │  Port: 3001     │  │  Port: 9090     │  │  Port: 16686    │         │
│  │ - System Health │  │ - Service Metrics│  │ - Request Tracing│        │
│  │ - Performance   │  │ - Custom Metrics │  │ - Error Tracking │        │
│  │ - Business KPIs │  │ - Alerting      │  │ - Latency Analysis│        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Intent Engine  │───▶│   PII Vault     │
│ (Natural Lang)  │    │  (NLP Parser)   │    │ (Tokenization)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  HITL Editor    │◄───│  Notarius API   │◄───│  LexNode RAG    │
│ (Human Review)  │    │ (Orchestration) │    │ (Legal Grounding)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │    Document Output      │
                    │  (PDF + Audit Trail)   │
                    └─────────────────────────┘
```

### Service Details

| **Service** | **Technology** | **Port** | **Purpose** | **Key Features** |
|-------------|----------------|----------|-------------|------------------|
| **Notarius Web** | Next.js 15 + React 19 | 3000 | HITL Editor Frontend | Rich text editor, real-time collaboration, document management |
| **Notarius API** | Django 5.2 + DRF | 8000 | Main REST API | Multi-tenant, authentication, document orchestration |
| **LexNode RAG** | FastAPI + LangChain | 8001 | Legal Knowledge Base | Vector search, legal document retrieval, citation generation |
| **PII Vault** | FastAPI + Cryptography | 8002 | Encryption Service | PII tokenization, KMS encryption, audit logging |
| **Intent Engine** | FastAPI + OpenAI | 8003 | AI Parser | Natural language processing, intent classification |

### Data Services

| **Service** | **Technology** | **Port** | **Purpose** | **Key Features** |
|-------------|----------------|----------|-------------|------------------|
| **PostgreSQL (Notarius)** | PostgreSQL 16 | 5432 | Application Data | Multi-tenant schema, user management, document metadata |
| **PostgreSQL (LexNode)** | PostgreSQL 16 + pgvector | 5433 | Legal Documents | Vector embeddings, legal document storage, similarity search |
| **PostgreSQL (Vault)** | PostgreSQL 16 | 5434 | Encrypted PII | Encrypted PII storage, audit trails, compliance logging |
| **Redis** | Redis 7 | 6379 | Cache & Queues | Session storage, task queues, rate limiting |
| **MinIO** | MinIO | 9000/9001 | S3 Storage | Document files, PDF storage, media assets |

### Observability Stack

| **Service** | **Technology** | **Port** | **Purpose** | **Key Features** |
|-------------|----------------|----------|-------------|------------------|
| **Grafana** | Grafana | 3001 | Dashboards | System monitoring, business KPIs, alerting |
| **Prometheus** | Prometheus | 9090 | Metrics | Service metrics, custom metrics, alerting rules |
| **Jaeger** | Jaeger | 16686 | Tracing | Distributed tracing, performance analysis, error tracking |

### Privacy-First Design Principles

1. **Zero PII in AI Services**: All sensitive data is tokenized before processing
2. **Encrypted Vault**: Military-grade encryption for PII storage
3. **Audit Everything**: Complete audit trail for all PII operations
4. **Tenant Isolation**: Complete data separation between cartórios
5. **Compliance Ready**: LGPD compliant with full audit capabilities

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1. One-Command Setup
```bash
git clone <repository-url>
cd notarius
make setup
```

That's it! All 14 services will start automatically with health checks. The system includes a complete microservices architecture with frontend, APIs, databases, and observability stack as shown in the [Architecture](#️-architecture) section above.

**Or manually:**
```bash
docker-compose up -d
```

### 2. Access the Application

**Core Services (14/14 Running):**

**User Interfaces:**
- 🎨 **Frontend**: http://localhost:3000 - HITL Editor, Document Management
- 👨‍💼 **Django Admin**: http://localhost:8000/admin - Backend Administration
- 📊 **Grafana**: http://localhost:3001 - Monitoring Dashboards (admin/admin)

**APIs:**
- 📡 **Django API**: http://localhost:8000 - Main REST API
- 📚 **LexNode RAG**: http://localhost:8001 - Legal Knowledge Base
- 🔐 **PII Vault**: http://localhost:8002 - Encryption Service
- 🤖 **Intent Engine**: http://localhost:8003 - AI Parser

**Development Tools:**
- 📧 **MailHog**: http://localhost:8025 - Email Testing (catch all outgoing emails)
- 💾 **MinIO Console**: http://localhost:9001 - S3 Storage (minioadmin/minioadmin)

**Monitoring:**
- 📈 **Prometheus**: http://localhost:9090 - Metrics Collection
- 🔍 **Jaeger**: http://localhost:16686 - Distributed Tracing

> **Architecture Note**: The system follows a privacy-first microservices architecture where PII is tokenized and encrypted before processing. See the [Architecture](#️-architecture) section for detailed service interactions and data flow.

### 3. Common Commands
```bash
make start          # Start all services
make stop           # Stop all services
make logs           # View logs
make test           # Run tests
make shell          # Open shell in API container
make health         # Check service health
```

📖 **Docker Quick Reference**: [DOCKER_QUICKREF.md](DOCKER_QUICKREF.md) - All commands  
📖 **Docker Architecture**: [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md) - Visual diagrams  
📖 **Full Docker Guide**: [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) - Comprehensive guide  
📖 **Manual Setup**: [QUICKSTART.md](QUICKSTART.md) - Non-Docker setup

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [STATUS.md](STATUS.md) | **Current system status and overview** |
| [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) | **Docker setup guide (START HERE)** |
| [docs/ANSIBLE_SETUP.md](docs/ANSIBLE_SETUP.md) | Ansible infrastructure management |
| [QUICKSTART.md](QUICKSTART.md) | Manual setup (without Docker) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and architecture |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development guidelines |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [docs/API.md](docs/API.md) | API documentation |
| [docs/TESTING.md](docs/TESTING.md) | Testing strategy and guide |
| [docs/COMPREHENSIVE_TESTING.md](docs/COMPREHENSIVE_TESTING.md) | Comprehensive testing documentation |

## 🧪 Testing

```bash
# Using Make (Docker)
make test              # Run quick tests
make test-full         # Run full test suite
make test-integration  # Integration tests
make test-e2e          # End-to-end tests
make test-security     # Security tests

# Or use the test runner directly
python tests/run_all_tests.py --all
python tests/run_all_tests.py --quick
```

## 🏢 Use Cases

### For Cartórios (Notary Offices)
- **Procurações**: Generate power of attorney documents from natural language
- **Certidões**: Create certificates with legal citations
- **Testamentos**: Draft wills with proper legal structure
- **Escrituras**: Generate property deeds and contracts

### For Legal Professionals
- **Document Drafting**: AI-assisted document creation
- **Legal Research**: Integrated legal knowledge base
- **Compliance**: Automated legal requirement checking
- **Audit Trail**: Complete document history and approvals

## 🔧 Development

### Project Structure
```
notarius/
├── apps/
│   ├── notarius-api/     # Django REST API
│   ├── notarius-web/     # Next.js Frontend
│   ├── lexnode-api/      # RAG Service (FastAPI)
│   ├── pii-vault/        # PII Protection (FastAPI)
│   └── intent-engine/    # NLP Service (FastAPI)
├── packages/
│   ├── core/             # Shared domain models
│   ├── pii/              # PII handling utilities
│   └── observability/    # Monitoring and logging
├── infra/                # Infrastructure as Code
└── docs/                 # Documentation
```

### Key Technologies
- **Backend**: Django 5.2, Django REST Framework
- **Frontend**: Next.js 14, TypeScript, TipTap Editor
- **AI Services**: FastAPI, OpenAI, LangChain
- **Database**: PostgreSQL, pgvector (for embeddings)
- **Infrastructure**: Docker, Terraform, AWS/GCP
- **Monitoring**: OpenTelemetry, Grafana, Prometheus

## 🛡️ Security & Privacy

### PII Protection
- **Tokenization**: All PII replaced with encrypted tokens
- **KMS Encryption**: AWS KMS or GCP KMS for key management
- **Audit Logging**: Every PII operation is logged
- **RBAC**: Role-based access control
- **Data Isolation**: Complete tenant separation

### Compliance
- **LGPD Compliant**: Brazilian data protection law
- **Audit Ready**: Complete audit trails
- **Encryption at Rest**: All sensitive data encrypted
- **Encryption in Transit**: TLS 1.3 for all communications

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- **Python**: Black, isort, mypy, ruff
- **TypeScript**: ESLint, Prettier
- **Testing**: pytest, Jest
- **Documentation**: Markdown, OpenAPI

## 📈 Roadmap

### Phase 1: Core System ✅
- [x] Multi-tenant Django API
- [x] Basic document management
- [x] PII tokenization foundation
- [x] Admin interface

### Phase 2: AI Services 🚧
- [ ] PII Vault service
- [ ] LexNode RAG service
- [ ] Intent Engine
- [ ] HITL Editor

### Phase 3: Production ✅
- [x] Docker Compose setup
- [x] Ansible infrastructure management
- [x] Multi-environment deployment (local/staging/production)
- [x] Monitoring and alerting (Grafana, Prometheus, Jaeger)
- [x] Comprehensive test suite
- [ ] Terraform infrastructure
- [ ] CI/CD pipeline

### Phase 4: Advanced Features 📋
- [ ] Real-time collaboration
- [ ] Advanced AI features
- [ ] Brazilian legal integrations
- [ ] Mobile app

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Brazilian legal community for domain expertise
- Open source contributors
- AI/ML research community
- Privacy and security advocates

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/notarius/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/notarius/discussions)
- **Email**: support@notarius.ai

---

**Built with ❤️ for the Brazilian legal community**

*Transforming notary offices with AI while protecting privacy and ensuring legal compliance.*