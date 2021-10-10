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
                'user_id': str(self.user.id),
                'data': messages_data
            }
        )

        # game
        game = await async_get_game_by_id(self.game_id)
        if not game.is_start():
            game.start()

        enemy_user_id = game.get_another_player(self.user.id)

        boat_places = game.get_player_boat_places(self.user.id)
        my_attacked_fields = game.get_player_attacked_fields(self.user.id)
        enemy_attacked_fields = game.get_player_attacked_fields(enemy_user_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_start',
                'user_id': str(self.user.id),

                'data': {
                    'boat_places': boat_places,
                    'my_attacked_fields': my_attacked_fields,
                    'enemy_attacked_fields': enemy_attacked_fields,
                    'turn': game.turn
                }
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
            user_id = str(self.user.id)
            username = self.user.username

            message = Message(self.room_group_name, self.user.id,
                              self.user.username, message, date)
            message.save()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user_id': user_id,
                    'message': message.content,
                    'username': username,
                    'date': date,
                }
            )
        elif type_ == 'gameAttack':
            data = text_data_json['data']
            field_id = data['fieldID']
            user_id = str(data['userID'])

            game = await async_get_game_by_id(self.game_id)
            enemy_user_id = str(game.get_another_player(user_id))

            # если не ход противника
            if str(game.turn) == user_id:
                response = game.attack(user_id, field_id)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_attack',
                        'user_id': user_id,
                        'data': response
                    }
                )

                response['from_enemy'] = True
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_attack',
                        'user_id': enemy_user_id,
                        'data': response
                    }
                )
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_error',
                        'user_id': user_id,
                        'error_text': 'Не ваш ход!'
                    }
                )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        date = event['date']
        user_id = event['user_id']

        await self.send(json.dumps({
            'type': 'message',
            'status': 'OK',

            'content': message,

            'user_id': user_id,
            'username': username,
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

    async def game_end(self, event):
        data = event['data']
        user_id = event['user_id']

        await self.send(json.dumps(
            {
                'type': 'game_end',
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

    async def game_enemy_attack(self, event):
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
