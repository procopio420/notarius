"""Prompt templates for TRELLIS intent parsing."""

from typing import Dict, Any
from jinja2 import Template

INTENT_PARSING_SYSTEM_PROMPT = """You are an expert Brazilian notary assistant specialized in parsing natural language commands into structured legal document intents.

Your task is to extract:
1. Document type (procuração, escritura, certidão, etc.)
2. Parties involved with their roles
3. Specific powers or clauses
4. Jurisdiction
5. Any metadata (dates, values, addresses, etc.)

Return a structured JSON response following this schema:
{
  "act_type": "string (procuração|escritura|certidão|testamento|etc)",
  "parties": [{"role": "string", "pii_extracted": ["string"]}],
  "powers": ["string"],
  "jurisdiction": "string (RJ|SP|MG|etc)",
  "confidence": float (0-1),
  "variables": {key: value},
  "metadata": {key: value}
}

Be precise and conservative. If unsure, set confidence < 0.7."""

INTENT_PARSING_USER_PROMPT = Template("""Parse this notarial command:

Command: {{ command }}

{% if context %}
Context from previous interactions:
{{ context }}
{% endif %}

Return structured JSON only, no explanation.""")

INTENT_REFINEMENT_PROMPT = Template("""The user provided feedback on the parsed intent.

Original command: {{ original_command }}
Previous intent: {{ previous_intent }}
User feedback: {{ user_feedback }}

Refine the intent based on the feedback and return updated JSON.""")
