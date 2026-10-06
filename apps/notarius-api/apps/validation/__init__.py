"""
Validation engine for legal document requirements.
"""

import sys
import os
from pathlib import Path

# Ensure packages directory is in Python path before any imports
# This runs when Django loads the validation app
# During Docker build, packages might not be available - that's OK
try:
    if '/packages' not in sys.path and os.path.exists('/packages'):
        sys.path.insert(0, '/packages')
    elif not any('packages' in p for p in sys.path):
        # Try to find packages directory relative to this file
        current_file = Path(__file__).resolve()
        # Go up: validation -> apps -> notarius-api -> project root
        project_root = current_file.parent.parent.parent
        packages_path = project_root / 'packages'
        if packages_path.exists():
            sys.path.insert(0, str(packages_path))
except Exception:
    # During build, this might fail - that's OK, imports will handle it
    pass

default_app_config = 'apps.validation.apps.ValidationConfig'

