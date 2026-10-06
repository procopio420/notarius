"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Add packages directory to Python path before Django loads
# This ensures packages can be imported by Django apps
BASE_DIR = Path(__file__).resolve().parent.parent
packages_paths = [
    '/packages',  # Docker mount point
    BASE_DIR.parent.parent / 'packages',  # From apps/notarius-api to project root
]

for pkg_path in packages_paths:
    pkg_str = str(pkg_path) if isinstance(pkg_path, Path) else pkg_path
    if os.path.exists(pkg_str):
        if pkg_str not in sys.path:
            sys.path.insert(0, pkg_str)
        break

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
