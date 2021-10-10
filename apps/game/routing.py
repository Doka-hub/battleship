from django.urls import path

# local imports
from .consumers import ChatConsumer


websocket_urlpatterns = [
    path('ws/game/<str:game_id>/', ChatConsumer.as_asgi()),
]
