"""
Prometheus metrics endpoint for LexNode API service.
"""

import sys

# Ensure root directory is in path to enable packages import
if '/' not in sys.path:
    sys.path.insert(0, '/')

from fastapi import APIRouter
from fastapi.responses import Response
from packages.observability.metrics import get_metrics_collector

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    collector = get_metrics_collector("lexnode-api")
    metrics_data = collector.get_metrics()
    return Response(
        content=metrics_data,
        media_type=collector.get_content_type()
    )


