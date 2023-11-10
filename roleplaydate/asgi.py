import os
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import roleplaydate.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roleplaydate.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(roleplaydate.routing.websocket_urlpatterns)
        ),
    }
)
