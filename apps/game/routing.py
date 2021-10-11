from django.urls import path

# local imports
from .consumers import Consumer


websocket_urlpatterns = [
    path('ws/game/<str:game_id>/', Consumer.as_asgi()),
]
