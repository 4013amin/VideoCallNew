# Video/asgi.py
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Video.settings')

django_asgi_app = get_asgi_application()

import videocall.routing # مسیردهی وب‌سوکت‌ها را اینجا import می‌کنیم

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    videocall.routing.websocket_urlpatterns
                )
            )
        ),
    }
)