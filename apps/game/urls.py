from django.urls import path

# local imports
from .views import (
    CustomLoginView, LogoutView, GuestLoginView,
    EnterGameIDFormView, GameDetailView
)


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('login-as-guest/', GuestLoginView.as_view(), name='login_as_guest'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('game/', EnterGameIDFormView.as_view(), name='enter_game_id'),
    path('game/<str:game_id>/', GameDetailView.as_view(), name='game'),
]


