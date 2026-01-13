"""
Entry point for the my_function package.

This package wraps a Django application and exposes
a standard entry point compatible with the reference repo.
"""

from .main import main
from . import audiences_app

__all__ = ["main"]
