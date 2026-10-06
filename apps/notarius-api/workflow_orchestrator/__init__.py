"""
Workflow Orchestrator Module

Determines document workflow: signing requirements, routing, protocol methods,
checklists, and legal citations based on document type, specialty, UF, and metadata.
All operations are PII-safe (no PII in logs, metrics, or cache).
"""

__version__ = "1.0.0"

