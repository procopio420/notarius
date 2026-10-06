"""
API views for workflow orchestrator.
"""

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from workflow_orchestrator.models.contracts import WorkflowInput, RulePackSummary
from workflow_orchestrator.core.orchestrator import plan_from_input
from workflow_orchestrator.core.rulepack_loader import load_rulepack
from workflow_orchestrator.utils.pii import redact_pii_in_logs

logger = logging.getLogger(__name__)

_metrics_lock = Lock()
_request_counters = defaultdict(int)


def _increment_counter(route: str, outcome: str) -> None:
    """Increment in-memory counter for observability."""
    key = (route, outcome)
    with _metrics_lock:
        _request_counters[key] += 1


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def route_workflow(request):
    """
    POST /workflow/route
    
    Generate workflow plan for a document.
    
    Body: WorkflowInput
    Returns: WorkflowPlan
    """
    start = time.perf_counter()
    endpoint = "/workflow/route"
    try:
        # Parse input (Pydantic validation)
        try:
            input_data = WorkflowInput(**request.data)
        except PydanticValidationError as exc:
            duration = time.perf_counter() - start
            _increment_counter(endpoint, "validation_error")
            error_payload: Dict[str, Any] = {
                "error": "Invalid input",
                "details": exc.errors(),
            }
            logger.warning(f"Invalid workflow input: {redact_pii_in_logs(request.data)}")
            return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate plan
        plan = plan_from_input(input_data)
        
        # Log (with PII redaction)
        log_data = {
            "especialidade": input_data.doc.especialidade,
            "tipo_documento": input_data.doc.tipo_documento,
            "uf": input_data.doc.uf,
            "cache_key": plan.cache_key,
        }
        logger.info(f"Workflow plan generated: {redact_pii_in_logs(log_data)}")
        
        duration = time.perf_counter() - start
        _increment_counter(endpoint, "success")
        
        # Return plan
        return Response(plan.model_dump(), status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating workflow plan: {e}", exc_info=True)
        duration = time.perf_counter() - start
        _increment_counter(endpoint, "error")
        return Response(
            {"error": str(e), "error_type": type(e).__name__},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rulepacks(request):
    """
    GET /workflow/rulepacks?uf=RJ&specialidade=registro_imoveis
    
    Get rulepack summary.
    
    Query params:
        uf: State code (optional)
        specialidade: Specialty (optional)
    
    Returns: RulePackSummary
    """
    start = time.perf_counter()
    endpoint = "/workflow/rulepacks"
    try:
        uf = request.query_params.get('uf')
        especialidade = request.query_params.get('specialidade')
        
        # Load rulepack
        rules = load_rulepack(uf) if uf else load_rulepack(None)
        
        # Filter by especialidade if provided
        if especialidade:
            filtered_rules = {
                k: v for k, v in rules.items()
                if k.startswith(f"{especialidade}.")
            }
        else:
            filtered_rules = rules
        
        # Extract document types
        document_types = list(filtered_rules.keys())
        
        summary = RulePackSummary(
            uf=uf,
            especialidade=especialidade,
            document_types=document_types,
            rules_count=len(filtered_rules)
        )
        
        duration = time.perf_counter() - start
        _increment_counter(endpoint, "success")
        
        return Response(summary.model_dump(), status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error loading rulepack: {e}", exc_info=True)
        duration = time.perf_counter() - start
        _increment_counter(endpoint, "error")
        return Response(
            {"error": str(e), "error_type": type(e).__name__},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

