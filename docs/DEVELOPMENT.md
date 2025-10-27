# Development Guide

This guide covers development setup, coding standards, testing, and contribution guidelines for the Notarius project.

## Development Environment Setup

### Prerequisites

- **Python 3.11+** (tested with 3.13)
- **Node.js 18+** (for frontend development)
- **Git**
- **Docker & Docker Compose** (for full stack development)
- **PostgreSQL 14+** (for production-like development)

### 1. Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd notarius

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Backend Development

```bash
cd apps/notarius-api

# Install Django dependencies
pip install django djangorestframework django-cors-headers django-filter psycopg2-binary python-decouple django-environ markdown PyPDF2 httpx pytest-django model-bakery factory-boy

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:8000
```

### 3. Frontend Development

```bash
cd apps/notarius-web

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

### 4. Full Stack Development

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
notarius/
├── apps/                          # Application services
│   ├── notarius-api/             # Django REST API
│   │   ├── apps/                 # Django apps
│   │   │   ├── base/             # Multi-tenancy foundation
│   │   │   ├── documentos/       # Document management
│   │   │   ├── partes/           # Party management
│   │   │   ├── processos/        # Process workflow
│   │   │   └── ai/               # AI service integration
│   │   ├── config/               # Django settings
│   │   ├── templates/            # HTML templates
│   │   └── tests/                # Test suite
│   ├── notarius-web/             # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/              # Next.js app router
│   │   │   ├── components/       # React components
│   │   │   ├── hooks/            # Custom hooks
│   │   │   ├── lib/              # Utilities
│   │   │   └── types/            # TypeScript types
│   │   └── public/               # Static assets
│   ├── lexnode-api/              # RAG service (FastAPI)
│   ├── pii-vault/                # PII protection (FastAPI)
│   └── intent-engine/            # NLP service (FastAPI)
├── packages/                      # Shared packages
│   ├── core/                     # Domain models
│   ├── pii/                      # PII utilities
│   └── observability/            # Monitoring
├── infra/                        # Infrastructure
│   ├── docker/                   # Docker configurations
│   ├── terraform/                # Infrastructure as Code
│   └── k8s/                      # Kubernetes manifests
├── docs/                         # Documentation
└── scripts/                      # Utility scripts
```

## Coding Standards

### Python (Backend)

**Code Formatting**:
```bash
# Install development tools
pip install black isort mypy ruff

# Format code
black apps/
isort apps/

# Lint code
ruff check apps/
mypy apps/
```

**Standards**:
- **Line Length**: 88 characters (Black default)
- **Import Order**: isort with Black compatibility
- **Type Hints**: Required for all public functions
- **Docstrings**: Google style for all classes and functions
- **Error Handling**: Explicit exception handling

**Example**:
```python
from typing import List, Optional
from django.db import models
from apps.base.models import BaseTenantModel


class Minuta(BaseTenantModel):
    """
    Minuta model for AI-generated document drafts.
    
    This model represents a draft document that can be generated
    by AI and edited by humans before finalization.
    """
    
    corpo_md: str = models.TextField(help_text="Markdown content")
    status: str = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    def can_be_approved(self) -> bool:
        """Check if minuta can be approved."""
        return self.status == "rascunho"
    
    def approve(self, user: User) -> None:
        """Approve the minuta."""
        if not self.can_be_approved():
            raise ValueError("Minuta cannot be approved in current state")
        
        self.status = "aprovado"
        self.approved_by = user
        self.save()
```

### TypeScript (Frontend)

**Code Formatting**:
```bash
# Install development tools
npm install -D eslint prettier @typescript-eslint/parser

# Format code
npm run format

# Lint code
npm run lint
```

**Standards**:
- **Line Length**: 100 characters
- **Indentation**: 2 spaces
- **Quotes**: Single quotes for strings
- **Semicolons**: Required
- **Type Safety**: Strict TypeScript configuration

**Example**:
```typescript
import { useState, useEffect } from 'react';
import { Minuta, Citation } from '@/types';

interface EditorProps {
  minuta: Minuta;
  onSave: (content: string) => void;
  onApprove: () => void;
}

export const HITLEditor: React.FC<EditorProps> = ({
  minuta,
  onSave,
  onApprove,
}) => {
  const [content, setContent] = useState<string>(minuta.corpo_md);
  const [citations, setCitations] = useState<Citation[]>([]);

  const handleSave = (): void => {
    onSave(content);
  };

  const handleApprove = (): void => {
    onApprove();
  };

  return (
    <div className="editor-container">
      {/* Editor implementation */}
    </div>
  );
};
```

## Testing

### Backend Testing

**Test Structure**:
```python
# tests/test_models.py
import pytest
from django.test import TestCase
from apps.documentos.models import Minuta
from apps.base.models import Tenant


class MinutaModelTest(TestCase):
    """Test Minuta model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            nome="Test Cartório",
            uf="SP"
        )
    
    def test_minuta_creation(self):
        """Test minuta creation."""
        minuta = Minuta.objects.create(
            tenant=self.tenant,
            corpo_md="# Test Minuta",
            status="rascunho"
        )
        
        self.assertEqual(minuta.tenant, self.tenant)
        self.assertEqual(minuta.status, "rascunho")
    
    def test_minuta_approval(self):
        """Test minuta approval workflow."""
        minuta = Minuta.objects.create(
            tenant=self.tenant,
            corpo_md="# Test Minuta",
            status="rascunho"
        )
        
        self.assertTrue(minuta.can_be_approved())
        
        minuta.approve(self.user)
        self.assertEqual(minuta.status, "aprovado")
```

**Running Tests**:
```bash
# Run all tests
python manage.py test

# Run specific test
python manage.py test tests.test_models.MinutaModelTest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run with verbose output
python manage.py test --verbosity=2
```

### Frontend Testing

**Test Structure**:
```typescript
// __tests__/components/Editor.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { HITLEditor } from '@/components/editor/HITLEditor';
import { Minuta } from '@/types';

const mockMinuta: Minuta = {
  id: '1',
  corpo_md: '# Test Minuta',
  status: 'rascunho',
  // ... other properties
};

describe('HITLEditor', () => {
  it('renders minuta content', () => {
    render(<HITLEditor minuta={mockMinuta} onSave={jest.fn()} onApprove={jest.fn()} />);
    
    expect(screen.getByText('Test Minuta')).toBeInTheDocument();
  });

  it('calls onSave when save button is clicked', () => {
    const mockOnSave = jest.fn();
    render(<HITLEditor minuta={mockMinuta} onSave={mockOnSave} onApprove={jest.fn()} />);
    
    fireEvent.click(screen.getByText('Save'));
    expect(mockOnSave).toHaveBeenCalled();
  });
});
```

**Running Tests**:
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## Database Development

### Migrations

**Creating Migrations**:
```bash
# Create migration for model changes
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations documentos

# Create empty migration
python manage.py makemigrations --empty documentos
```

**Applying Migrations**:
```bash
# Apply all migrations
python manage.py migrate

# Apply specific migration
python manage.py migrate documentos 0001

# Show migration status
python manage.py showmigrations
```

**Migration Best Practices**:
- Always review generated migrations
- Test migrations on sample data
- Use data migrations for complex changes
- Never edit applied migrations

### Database Seeding

**Management Commands**:
```python
# apps/documentos/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from apps.documentos.models import DocumentTemplate


class Command(BaseCommand):
    help = 'Seed database with initial data'
    
    def handle(self, *args, **options):
        # Create default templates
        DocumentTemplate.objects.get_or_create(
            name="Procuração Padrão",
            document_type="procuracao",
            defaults={
                "template_path": "procuracao.html",
                "is_default": True,
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database')
        )
```

**Running Seed Commands**:
```bash
python manage.py seed_data
```

## API Development

### REST API Standards

**URL Patterns**:
```python
# apps/documentos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MinutaViewSet, DocumentoViewSet

router = DefaultRouter()
router.register(r'minutas', MinutaViewSet, basename='minuta')
router.register(r'documentos', DocumentoViewSet, basename='documento')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

**ViewSet Implementation**:
```python
# apps/documentos/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.base.views import BaseTenantViewSet
from .models import Minuta
from .serializers import MinutaSerializer


class MinutaViewSet(BaseTenantViewSet):
    """ViewSet for minuta management."""
    
    queryset = Minuta.objects.all()
    serializer_class = MinutaSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a minuta."""
        minuta = self.get_object()
        
        if not minuta.can_be_approved():
            return Response(
                {'error': 'Minuta cannot be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        minuta.approve(request.user)
        return Response({'status': 'approved'})
```

**Serializer Implementation**:
```python
# apps/documentos/serializers.py
from rest_framework import serializers
from .models import Minuta


class MinutaSerializer(serializers.ModelSerializer):
    """Serializer for Minuta model."""
    
    class Meta:
        model = Minuta
        fields = [
            'id', 'corpo_md', 'status', 'versao',
            'gerada_por', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_status(self, value):
        """Validate status transitions."""
        if self.instance and not self.instance.can_transition_to(value):
            raise serializers.ValidationError(
                f"Cannot transition from {self.instance.status} to {value}"
            )
        return value
```

## Debugging

### Backend Debugging

**Django Debug Toolbar**:
```bash
pip install django-debug-toolbar

# Add to settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**Logging Configuration**:
```python
# config/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Frontend Debugging

**React Developer Tools**:
- Install browser extension
- Use React DevTools for component inspection
- Use Redux DevTools for state management

**Debug Configuration**:
```typescript
// next.config.js
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    // Enable debugging features
  },
};
```

## Performance Optimization

### Backend Optimization

**Database Optimization**:
```python
# Use select_related for foreign keys
minutas = Minuta.objects.select_related('tenant', 'processo').all()

# Use prefetch_related for many-to-many
processos = Processo.objects.prefetch_related('partes').all()

# Use only() to limit fields
minutas = Minuta.objects.only('id', 'status', 'created_at')
```

**Caching**:
```python
from django.core.cache import cache

def get_minuta(minuta_id):
    cache_key = f'minuta_{minuta_id}'
    minuta = cache.get(cache_key)
    
    if not minuta:
        minuta = Minuta.objects.get(id=minuta_id)
        cache.set(cache_key, minuta, 300)  # 5 minutes
    
    return minuta
```

### Frontend Optimization

**Code Splitting**:
```typescript
// Lazy load components
const Editor = lazy(() => import('@/components/editor/HITLEditor'));

// Use dynamic imports
const handleExport = async () => {
  const { exportToPDF } = await import('@/utils/export');
  exportToPDF(content);
};
```

**Memoization**:
```typescript
import { memo, useMemo } from 'react';

const CitationList = memo(({ citations }: { citations: Citation[] }) => {
  const sortedCitations = useMemo(
    () => citations.sort((a, b) => a.confidence - b.confidence),
    [citations]
  );

  return (
    <div>
      {sortedCitations.map(citation => (
        <CitationItem key={citation.id} citation={citation} />
      ))}
    </div>
  );
});
```

## Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f notarius-api

# Stop services
docker-compose down
```

### Staging Deployment

```bash
# Build and push images
docker build -t notarius-api:latest .
docker push notarius-api:latest

# Deploy to staging
kubectl apply -f k8s/staging/
```

### Production Deployment

```bash
# Use Terraform for infrastructure
cd infra/terraform
terraform init
terraform plan
terraform apply

# Deploy applications
./scripts/deploy.sh production
```

## Contributing

### Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Pull Request Guidelines

- **Clear Description**: Explain what the PR does and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update documentation if needed
- **Screenshots**: Include screenshots for UI changes
- **Breaking Changes**: Clearly mark any breaking changes

### Code Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Peer Review**: At least one team member reviews the code
3. **Testing**: Manual testing of new features
4. **Approval**: Maintainer approval required for merge

## Troubleshooting

### Common Issues

**Database Connection Issues**:
```bash
# Check database status
python manage.py dbshell

# Reset database
rm db.sqlite3
python manage.py migrate
```

**Import Errors**:
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt
```

**Frontend Build Issues**:
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

### Getting Help

- **Documentation**: Check the docs/ directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Slack**: Join our development Slack channel

---

Happy coding! 🚀
