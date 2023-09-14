# pragma no cover
from django.core.wsgi import get_wsgi_application

__all__ = ('application',)

application = get_wsgi_application()
