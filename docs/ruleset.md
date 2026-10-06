# Legal Ruleset Documentation

## Rule Sources and Precedence Model

The Notarius legal knowledge system applies rules from multiple sources with a clear precedence hierarchy.

## Precedence Hierarchy

Rules are applied in the following order of precedence (highest to lowest):

1. **Federal Legislation (Precedence: `federal`)**
   - CNJ (Conselho Nacional de Justiça) Provimentos
   - Federal Laws (Lei 6.015/73, Lei 8.935/94)
   - Civil Code (Código Civil)

2. **State-Level Rules (Precedence: `state`)**
   - CGJ (Corregedoria Geral de Justiça) normas by UF
   - State-specific regulations

3. **Internal Notes (Precedence: `internal`)**
   - Cartório-specific procedures
   - Internal guidelines

## Rule Application

When querying rules for a document type and UF:

1. All federal rules apply (precedence = "federal")
2. State-specific rules apply only if UF matches
3. Internal rules apply per tenant/cartório

## Citation Format Standards

Citations follow this format:
- `Lei 6.015/73, Art. 123`
- `CNJ Provimento 123/2024`
- `CGJ/SP Norma 456/2023`
- `CC/2002, Art. 678`

## Checklist Items

Each checklist item must include at least one citation from legal_knowledge. Checklist items are extracted from rule content and metadata.

## Example

For `escritura_compra_venda` in `SP`:
- Federal rules: CC/2002, Lei 6.015/73 (always apply)
- State rules: CGJ/SP normas (apply because UF=SP)
- Internal rules: Cartório-specific (apply if tenant has them)

