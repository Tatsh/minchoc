"""WSGI application."""
# pragma no cover
from __future__ import annotations

from django.core.wsgi import get_wsgi_application

__all__ = ('application',)

application = get_wsgi_application()
