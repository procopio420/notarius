# Workflow Orchestrator

## Overview

The Workflow Orchestrator module automatically determines the complete workflow for any document: who needs to sign, what type of signature, where to route it, how to protocol it, prerequisites, and legal requirements - all while protecting PII (Personally Identifiable Information).

## Architecture

```
WorkflowInput → Orchestrator → Rulepack Loader → WorkflowPlan
```

### Decision Flow

```
1. Receive WorkflowInput (document type, specialty, UF, partes, preferences)
2. Normalize document type and specialty slugs
3. Load rulepack (global + UF-specific merge)
4. Determine routing destination (roteamento)
5. Determine signature requirements (assinatura)
6. Build checklist from rulepack + anexos
7. Extract legal citations (citacoes)
8. Extract fee hints (fees_hint)
9. Generate PII-safe cache key
10. Return WorkflowPlan
```

## API Endpoints

### POST /api/v1/workflow/route

Generate workflow plan for a document.

**Request Body:**
```json
{
  "doc": {
    "tipo_documento": "escritura_compra_venda",
    "especialidade": "tabelionato_notas",
    "uf": "SP",
    "municipio": "São Paulo",
    "partes": [
      {
        "nome": "Eduardo Rocha",
        "cpf_cnpj": "333.222.111-00",
        "papel": "vendedor"
      },
      {
        "nome": "Marina Costa",
        "cpf_cnpj": "555.444.333-22",
        "papel": "comprador"
      }
    ]
  },
  "preferencia_online": true,
  "assinatura_disponivel": ["icp_brasil", "e-notariado", "manual"],
  "canais_disponiveis": ["online", "presencial"],
  "anexos": ["itbi"]
}
```

**Response:**
```json
{
  "roteamento": {
    "autoridade": "Tabelionato de Notas",
    "plataforma": "e-notariado",
    "modo": "hibrido"
  },
  "assinatura": {
    "quem_assina": ["vendedor", "comprador", "tabeliao"],
    "tipo": "e-notariado",
    "videoconferencia": true
  },
  "protocolo": {
    "canal_principal": "hibrido",
    "plataforma": "e-notariado",
    "instrucoes": "Enviar para Tabelionato de Notas via e-notariado"
  },
  "checklist": [
    "Certidão matrícula <=30d",
    "ITBI",
    "Documentos de identidade",
    "Estado civil/procur. se aplicável"
  ],
  "citacoes": [
    "CC/2002",
    "Lei 6.015/73",
    "Prov. CNJ 100"
  ],
  "bloqueantes": [],
  "alerta": [],
  "fees_hint": [
    "Emolumentos Notas",
    "ITBI"
  ],
  "cache_key": "abc123..."
}
```

### GET /api/v1/workflow/rulepacks

Get rulepack summary.

**Query Parameters:**
- `uf` (optional): State code (SP, RJ, etc.)
- `specialidade` (optional): Specialty filter

**Response:**
```json
{
  "uf": "RJ",
  "especialidade": "registro_imoveis",
  "document_types": [
    "registro_imoveis.averbacao_construcao"
  ],
  "rules_count": 1
}
```

## Routing Logic

### By Specialty

| Specialty | Authority | Platform | Mode |
|-----------|-----------|----------|------|
| tabelionato_notas | Tabelionato de Notas | e-notariado | hibrido |
| rcpn | Registro Civil de Pessoas Naturais | None | presencial |
| registro_imoveis | Registro de Imóveis competente | registrodeimoveis.org.br | online |
| rtd | Registro de Títulos e Documentos | rtdbrasil.org.br | online |
| rcpj | Registro Civil de Pessoas Jurídicas | rtdbrasil.org.br | online |
| protesto | Tabelionato de Protesto | protesto.com.br | online |

## Signature Type Selection

1. **tabelionato_notas**: Prefer "e-notariado" → "icp_brasil" → "manual"
2. **Other specialties**: Prefer "icp_brasil" → "e-notariado" → "manual"

## Rulepack Format

Rulepacks are YAML files located in `rulepacks/` directory.

### Structure

```yaml
especialidade.tipo_documento:
  quem_assina:
    - role1
    - role2
  checklist:
    - Item 1
    - Item 2
  citacoes:
    - Citation 1
    - Citation 2
  fees_hint:
    - Fee 1
    - Fee 2
  bloqueantes: []
  alerta: []
```

### UF-Specific Overrides

UF-specific rulepacks can override or extend global rules:

```yaml
# RJ.yaml
registro_imoveis.averbacao_construcao:
  checklist_add:
    - Additional item
  citacoes_add:
    - Additional citation
```

The `_add` suffix appends to the base list instead of replacing it.

## PII Safety

- **No PII in logs**: All PII is redacted before logging
- **Hashed cache keys**: Cache keys use SHA256 hash of PII (with salt)
- **No PII in metrics**: Metrics only include aggregated data

### Cache Key Generation

Cache keys are generated from:
- Document type and specialty
- UF and municipality
- Hashed PII from partes (CPF/CNPJ)
- Partes roles
- Anexos (sorted)

Same input = same cache key (deterministic).

## Integration Stubs

The module includes integration stubs for:

- **e-notariado**: `ENotariadoClient`
- **RI Central**: `RICentralClient`
- **RTD/RCPJ Central**: `RTDPJCentralClient`
- **Protesto Central**: `ProtestoCentralClient`

All stubs return mock GUIDs and status information. Real integrations can be implemented later.

## Feature Flags

Environment variables control feature availability:

- `ENABLE_ENOTARIADO`: Enable e-notariado integration (default: True)
- `ENABLE_RI_CENTRAL`: Enable RI central integration (default: True)
- `ENABLE_RTDPJ_CENTRAL`: Enable RTD/RCPJ central integration (default: True)
- `ENABLE_PROTESTO_CENTRAL`: Enable Protesto central integration (default: True)

## Testing

Run tests with:

```bash
pytest tests/workflow/
```

All fixtures from `fixtures.jsonl` are automatically tested.

## Examples

### Escritura de Compra e Venda

```python
from workflow_orchestrator.models.contracts import WorkflowInput
from workflow_orchestrator.core.orchestrator import plan_from_input

input_data = WorkflowInput(
    doc={
        "tipo_documento": "escritura_compra_venda",
        "especialidade": "tabelionato_notas",
        "uf": "SP",
        "municipio": "São Paulo",
        "partes": [
            {"cpf_cnpj": "333.222.111-00", "papel": "vendedor"},
            {"cpf_cnpj": "555.444.333-22", "papel": "comprador"}
        ]
    },
    anexos=["itbi"]
)

plan = plan_from_input(input_data)
```

### Procuração

```python
input_data = WorkflowInput(
    doc={
        "tipo_documento": "procuracao_ad_judicia",
        "especialidade": "tabelionato_notas",
        "uf": "RJ",
        "partes": [
            {"cpf_cnpj": "987.111.222-33", "papel": "outorgante"}
        ]
    }
)

plan = plan_from_input(input_data)
```

## Future Enhancements

- Real integration implementations (replace stubs)
- Cost simulator by UF and document type
- UI pre-flight checker
- Advanced rulepack features (conditions, dependencies)

