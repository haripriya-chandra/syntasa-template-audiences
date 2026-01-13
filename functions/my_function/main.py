"""
Main entry point for the function.

This file bootstraps the Django application that lives inside
functions/my_function/django_app.
"""

import os
import sys
from pathlib import Path


def bootstrap_django() -> None:
    """
    Prepare Python path and environment so Django can run
    inside the reference repo structure.
    """
    base_dir = Path(__file__).resolve().parent
    django_dir = base_dir / "django_app"

    # Add django_app to PYTHONPATH
    sys.path.insert(0, str(django_dir))

    # Load Django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main() -> None:
    """
    Main entry point invoked by:
    - CI
    - Docker
    - Local execution
    """
    bootstrap_django()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise RuntimeError("Django is not installed or could not be loaded") from exc

    # Default to Django management commands
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
