"""App configuration."""
from __future__ import annotations

from django.apps import AppConfig


class MainConfig(AppConfig):
    """Configuration for the minchoc app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'minchoc'
