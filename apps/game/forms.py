from django.contrib.auth.forms import AuthenticationForm
from django import forms

# local imports
from .models import Game


class EnterGameIDForm(forms.Form):
    game_id = forms.CharField(max_length=255)

    class Meta:
        widgets = {
            'game_id': forms.TextInput(attrs={
                'class': 'input'
            })
        }

    def is_valid(self):
        game_id = self.data.get('game_id')

        try:
            Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            self.add_error('game_id', 'Игра не найдена!')

        return self.is_bound and not self.errors
