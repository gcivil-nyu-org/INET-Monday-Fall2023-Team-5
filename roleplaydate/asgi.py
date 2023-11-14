import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roleplaydate.settings")

# Initialize Django ASGI application early to ensure the App registry is populated
django_asgi_app = get_asgi_application()

# Now we can import the rest of the channels routing and other necessary imports
# Imports MUST occur here due to the order of operations for ASGI startup
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa
from channels.auth import AuthMiddlewareStack  # noqa
from roleplaydate import routing  # noqa

# Define a top-level ProtocolTypeRouter that routes to the correct type of connection
application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                # Use the routing defined in roleplaydate.routing
                routing.websocket_urlpatterns
            )
        ),
    }
)
