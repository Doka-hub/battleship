from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# local imports
from .models import CustomUser, Game


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    readonly_fields = ['game_id']
