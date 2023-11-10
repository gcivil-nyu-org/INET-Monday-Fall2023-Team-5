import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roleplaydate.settings")

# Initialize Django ASGI application early to ensure the App registry is populated
django_asgi_app = get_asgi_application()

# Now we can import the rest of the channels routing and other necessary imports
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from roleplaydate import routing

# Define a top-level ProtocolTypeRouter that routes to the correct type of connection
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,  # Django's ASGI application to handle traditional HTTP requests
        "websocket": AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns  # Use the routing defined in roleplaydate.routing
            )
        ),
    }
)
