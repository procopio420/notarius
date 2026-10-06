"""
Prometheus metrics endpoint for Django Notarius API service.
"""

import sys
import os
from pathlib import Path
from django.http import HttpResponse


def metrics_view(request):
    """Prometheus metrics endpoint."""
    # Lazy import to avoid build-time errors when packages isn't available
    # Ensure packages directory is in Python path
    if '/packages' not in sys.path and os.path.exists('/packages'):
        sys.path.insert(0, '/')
    elif not any('packages' in p for p in sys.path):
        # Try to find packages directory relative to this file
        current_file = Path(__file__).resolve()
        # Go up: base -> apps -> notarius-api -> project root
        project_root = current_file.parent.parent.parent
        if (project_root / 'packages').exists():
            sys.path.insert(0, str(project_root))
    
    # Import here (lazy) so it only happens at runtime, not during build
    from packages.observability.metrics import get_metrics_collector
    
    collector = get_metrics_collector("notarius-api")
    metrics_data = collector.get_metrics()
    return HttpResponse(
        metrics_data,
        content_type=collector.get_content_type()
    )

