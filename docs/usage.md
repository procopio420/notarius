# Legal Knowledge Stack Usage Guide

## Overview

This guide demonstrates how to use the Notarius legal knowledge stack for document processing.

## Workflow

The typical workflow is:

1. **Classify Document** → Identify document type and specialty
2. **Extract Form** → Extract structured data from free-text
3. **Validate** → Check against legal rules and requirements
4. **Render Template** → Generate document clauses
5. **Calculate Fees** → Determine applicable fees

## Examples

### Example 1: Escritura de Compra e Venda

#### Input
```
Escritura de compra e venda. Vendedor: Eduardo Rocha, CPF 333.222.111-00. 
Compradora: Marina Costa, CPF 555.444.333-22. Imóvel: matrícula 12345, 
2º RI Curitiba/PR. Preço R$ 450.000, pagamento à vista.
```

#### Step 1: Classify
```bash
POST /api/v1/classify-document
{
  "text": "Escritura de compra e venda...",
  "tenant_id": "tenant-uuid"
}
```

**Response:**
```json
{
  "tipo_documento": "escritura_compra_venda",
  "especialidade": "tabelionato_notas",
  "confianca": 0.95
}
```

#### Step 2: Extract Form
```bash
POST /api/v1/extract-form
{
  "text": "Escritura de compra e venda...",
  "document_type": "escritura_compra_venda",
  "tenant_id": "tenant-uuid"
}
```

**Response:**
```json
{
  "campos": {
    "vendedor": {
      "nome": "Eduardo Rocha",
      "cpf": "333.222.111-00"
    },
    "comprador": {
      "nome": "Marina Costa",
      "cpf": "555.444.333-22"
    },
    "imovel": {
      "matricula": "12345",
      "ri": "2º RI Curitiba/PR"
    },
    "financeiro": {
      "preco": 450000.00,
      "moeda": "BRL",
      "condicao": "avista"
    }
  }
}
```

#### Step 3: Validate
```bash
POST /api/v1/validation/validate-document/
{
  "document_type": "escritura_compra_venda",
  "extracted_data": {...},
  "uf": "PR"
}
```

**Response:**
```json
{
  "exigencias": [
    {
      "item": "Certidão de matrícula (<=30 dias)",
      "citation": "Lei 6.015/73, Art. 123",
      "met": false
    },
    {
      "item": "ITBI quitado",
      "citation": "Lei 6.015/73, Art. 123",
      "met": false
    }
  ],
  "bloqueantes": [],
  "opcionais": [],
  "citacoes": ["Lei 6.015/73", "CC/2002"]
}
```

#### Step 4: Render Template
The template service automatically uses the renderer with PII redaction and state-specific clauses.

#### Step 5: Calculate Fees
```bash
POST /api/v1/fees/calculate-fees/
{
  "document_type": "escritura_compra_venda",
  "uf": "PR",
  "base_value": 450000.00
}
```

**Response:**
```json
{
  "emolumentos": 1500.00,
  "frj": 75.00,
  "fundo_estadual": 225.00,
  "itbi": 4500.00,
  "total": 6300.00
}
```

## Integration Examples

### Full Workflow (Python)
```python
import httpx

async def process_document(text: str, tenant_id: str, uf: str):
    # 1. Classify
    classify_resp = await client.post(
        "http://intent-engine:8000/api/v1/classify-document",
        json={"text": text, "tenant_id": tenant_id}
    )
    doc_type = classify_resp.json()["tipo_documento"]
    
    # 2. Extract
    extract_resp = await client.post(
        "http://intent-engine:8000/api/v1/extract-form",
        json={"text": text, "document_type": doc_type, "tenant_id": tenant_id}
    )
    extracted = extract_resp.json()["campos"]
    
    # 3. Validate
    validate_resp = await client.post(
        "http://notarius-api:8000/api/v1/validation/validate-document/",
        json={"document_type": doc_type, "extracted_data": extracted, "uf": uf}
    )
    validation = validate_resp.json()
    
    return {
        "document_type": doc_type,
        "extracted": extracted,
        "validation": validation
    }
```

## Error Handling

- **422 (Unprocessable Entity)**: Validation errors (missing required fields, invalid format)
- **428 (Precondition Required)**: Missing documents (e.g., certidão not provided)

## Privacy Notes

- All PII is hashed before caching
- Logs are sanitized to remove PII
- Vector store contains only redacted content
- Original PII is only in encrypted vault

