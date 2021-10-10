import json

from channels.generic.websocket import AsyncWebsocketConsumer

from asgiref.sync import sync_to_async

from django.utils.timezone import datetime

# local imports
from .redis import Message, Game


def get_game_by_id(game_id: str) -> Game:
    game = Game(game_id)
    return game


async_get_game_by_id = sync_to_async(get_game_by_id, thread_sensitive=True)

# TODO: оповещать игроков об их ходе
# TODO: сделать верстку игры


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'chat_{self.game_id}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.room_group_name,
                                           self.channel_name)
        # chat
        messages_data = Message.get_messages_by_chat_id(self.room_group_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_history',
                'user_id': self.user.id,
                'data': messages_data
            }
        )

        # game
        game = await async_get_game_by_id(self.game_id)
        if not game.is_start():
            game.start()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_start',
                'user_id': self.user.id,
                'data': json.dumps(game.get_game_data())
            }
        )

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name,
                                               self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        type_ = text_data_json['type']

        if type_ == 'message':
            message = text_data_json['message']
            date = datetime.now().strftime('%d.%m.%Y %X')

            message = Message(self.room_group_name, self.user.id,
                              self.user.username, message, date)
            message.save()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user_id': self.user.id,
                    'message': message.content,
                    'date': date,
                }
            )
        elif type_ == 'gameAttack':
            data = text_data_json['data']
            field_id = data['fieldID']
            user_id = data['userID']

            game = await async_get_game_by_id(self.game_id)
            game_data = game.get_game_data()
            if game_data['turn'] == user_id:
                data = game.attack(user_id, field_id)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_attack',
                        'user_id': self.user.id,
                        'data': data
                    }
                )
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_error',
                        'user_id': self.user.id,
                        'error_text': 'Не ваш ход!'
                    }
                )

    async def chat_message(self, event):
        message = event['message']
        date = event['date']
        user_id = event['user_id']

        await self.send(json.dumps({
            'type': 'message',
            'status': 'OK',

            'content': message,

            'user_id': user_id,
            'username': self.user.username,
            'date': date
        }))

    async def chat_history(self, event):
        data = event['data']
        user_id = event['user_id']

        await self.send(json.dumps({
            'type': 'history',
            'status': 'OK',

            'user_id': user_id,

            'data': data
        }))

    async def game_start(self, event):
        data = event['data']
        user_id = event['user_id']

        await self.send(json.dumps(
            {
                'type': 'game_start',
                'status': 'OK',
                'user_id': user_id,

                'data': data
            }
        ))

    async def game_attack(self, event):
        data = event['data']
        user_id = event['user_id']

        await self.send(
            json.dumps(
                {
                    'type': 'game',
                    'status': 'OK',

                    'user_id': user_id,

                    'data': data
                }
            )
        )

    async def game_error(self, event):
        error_text = event['error_text']
        user_id = event['user_id']

        await self.send(
            json.dumps(
                {
                    'type': 'game',
                    'status': 'ERROR',

                    'user_id': user_id,

                    'data': {'error_text': error_text}
                }
            )
        )
