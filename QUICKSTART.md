# Notarius - Quick Start Guide

Welcome to Notarius, a privacy-first AI-powered Brazilian notary office workflow system. This guide will help you get the system running locally in minutes.

## 🐳 Docker Setup (Recommended - 2 minutes)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Make (optional, but recommended)

### One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd notarius

# Complete setup (builds images, starts services, runs migrations)
make setup
```

**That's it!** All services are now running. Access:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/ (admin/admin)
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **MailHog**: http://localhost:8025
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)

### Common Docker Commands

```bash
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View logs
make test           # Run tests
make shell          # Open shell in API container
make health         # Check service health
make status         # Show service status and URLs
```

### Without Make

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec notarius-api python manage.py migrate

# Create superuser
docker-compose exec notarius-api python manage.py createsuperuser

# Stop services
docker-compose down
```

📖 **For detailed Docker documentation, see [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)**

---

## 📦 Manual Setup (Without Docker)

> **Note**: Docker setup is recommended. Use manual setup only if you can't use Docker.

### Prerequisites

- Python 3.11+ (tested with Python 3.13)
- Git
- A modern web browser

## Quick Setup (5 minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd notarius

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install django djangorestframework django-cors-headers django-filter psycopg2-binary python-decouple django-environ markdown PyPDF2 httpx pytest-django model-bakery factory-boy
```

### 2. Database Setup

```bash
cd apps/notarius-api

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: admin123
```

### 3. Start the Server

```bash
# Start Django development server
python manage.py runserver 0.0.0.0:8000
```

### 4. Access the System

- **Admin Interface**: http://localhost:8000/admin/
  - Username: `admin`
  - Password: `admin123`

- **API Root**: http://localhost:8000/api/
  - Returns 403 (authentication required) - this is expected

- **API Documentation**: http://localhost:8000/api/ (when authenticated)

## What's Working

✅ **Core Django Application**
- Multi-tenant architecture
- User authentication and authorization
- Admin interface
- REST API endpoints

✅ **Document Management**
- Minuta (draft document) creation and management
- Document templates with tenant customization
- PDF generation (basic)

✅ **PII Protection Foundation**
- Token-based PII storage
- Audit logging
- Tenant isolation

✅ **Basic Models**
- Tenants (cartórios)
- Processes (processos)
- Parties (partes) with PII tokens
- Documents and minutas

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Current user info

### Core Resources
- `GET /api/tenants/` - List tenants
- `GET /api/processos/` - List processes
- `GET /api/partes/` - List parties
- `GET /api/documentos/` - List documents
- `GET /api/minutas/` - List minutas
- `GET /api/document-templates/` - List document templates

### AI Features (Basic Implementation)
- `POST /api/ai/generate-minuta/` - Generate minuta from natural language
- `POST /api/ai/approve-minuta/{id}/` - Approve a minuta
- `POST /api/ai/finalize-minuta/{id}/` - Finalize a minuta

## Testing

```bash
# Run basic tests
python manage.py test test_basic --verbosity=2

# Run with pytest (if you want more detailed output)
pytest test_basic.py -v
```

## Sample Data

The system starts with an empty database. You can:

1. **Create a Tenant** (via admin or API):
   ```json
   {
     "nome": "Cartório de Teste",
     "uf": "SP"
   }
   ```

2. **Create a Process**:
   ```json
   {
     "tipo_ato": "procuracao",
     "status": "ativo"
   }
   ```

3. **Generate a Minuta**:
   ```json
   {
     "command": "Fazer procuração para João Silva, CPF 123.456.789-00",
     "processo_id": "your-processo-id"
   }
   ```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API    │    │   Database      │
│   (Next.js)     │◄──►│   (Notarius)    │◄──►│   (SQLite)      │
│   Port 3000     │    │   Port 8000     │    │   (dev)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Services   │
                       │   (Future)      │
                       │   - PII Vault   │
                       │   - LexNode     │
                       │   - Intent      │
                       └─────────────────┘
```

## What's Coming Next

🚧 **In Development**:
- Full AI services (PII Vault, LexNode, Intent Engine)
- Advanced PDF templates
- Real-time collaboration
- Advanced PII protection

🚧 **Planned**:
- Docker Compose setup
- Production deployment
- Advanced AI features
- Integration with Brazilian legal systems

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**:
   ```bash
   python manage.py runserver 0.0.0.0:8001
   ```

2. **Database errors**:
   ```bash
   rm db.sqlite3
   python manage.py migrate
   ```

3. **Import errors**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Permission errors**:
   ```bash
   chmod +x scripts/*.sh
   ```

### Getting Help

- Check the logs in the terminal where you started the server
- Verify all dependencies are installed: `pip list`
- Ensure you're in the correct directory: `pwd`
- Check if the virtual environment is activated: `which python`

## Next Steps

1. **Explore the Admin Interface**: Create tenants, processes, and test the basic workflow
2. **Test the API**: Use tools like Postman or curl to test the REST endpoints
3. **Read the Architecture Docs**: Check `docs/ARCHITECTURE.md` for detailed system design
4. **Contribute**: See `CONTRIBUTING.md` for development guidelines

---

**Ready to build the future of Brazilian notary offices? Let's go! 🇧🇷**
