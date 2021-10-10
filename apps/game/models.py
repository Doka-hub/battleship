from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from django.utils.translation import gettext_lazy as _

from uuid import uuid4

from random import choice

import string


class CustomUser(AbstractUser):
    is_guest = models.BooleanField(default=False, verbose_name='Гость')

    @classmethod
    def get_new_guest_username(cls, count: int = 1):
        guests_count = cls.objects.filter(is_guest=True).count() + count
        guest_username = f'guest_{guests_count}'
        if cls.objects.filter(username=guest_username):
            return cls.get_new_guest_username(count + 1)
        return guest_username

    @classmethod
    def get_random_password(cls, length: int = 12):
        letters = string.ascii_letters + string.digits
        password = ''.join(choice(letters) for _ in range(length))
        return password

    @classmethod
    def guest_create(cls):
        password = cls.get_random_password()
        username = cls.get_new_guest_username()
        print(username)
        user = cls.objects.create_user(username, password=password)
        return user

    def __str__(self):
        return self.username or ''

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )


def get_random_game_name():
    return choice(Game.GAME_NAME_VARIANTS)[0]


class Game(models.Model):

    WINNER_CHOICE = (
        (1, 1),
        (2, 2)
    )

    GAME_NAME_VARIANTS = (
        ('Пираты', 'Пираты'),
        ('Морские черти', 'Морские черти'),
        ('Остров Х', 'Остров Х'),
    )

    game_id = models.CharField(max_length=255, default=uuid4,
                               verbose_name='ID игры')
    game_name = models.CharField(max_length=255,
                                 default=get_random_game_name,
                                 verbose_name='Название игры')

    player1 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                related_name='player1',
                                null=True, verbose_name='Игрок 1')
    player2 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                related_name='player2',
                                null=True, verbose_name='Игрок 2')

    winner = models.IntegerField(choices=WINNER_CHOICE, blank=True, null=True,
                                 verbose_name='Победитель')

    is_end = models.BooleanField(default=False, verbose_name='Игра закончена')

    def __str__(self):
        return self.game_name


@receiver(pre_save, sender=CustomUser)
def set_guest_username(sender, instance: CustomUser, **kwargs):
    if not instance.username and instance.is_guest:
        instance.username = CustomUser.get_new_guest_username()
