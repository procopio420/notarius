#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path

# Add packages directory to Python path before Django loads
# This ensures packages can be imported by Django apps
BASE_DIR = Path(__file__).resolve().parent
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


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
