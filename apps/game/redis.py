from typing import Optional, Union, List

from django.utils.timezone import datetime
from django.conf import settings

import json

import redis

# local imports
from .models import Game as GameModel


class RedisClient:
    r_client = redis.Redis(settings.REDIS_URL, settings.REDIS_PORT).client()


class Message(RedisClient):
    def __init__(self,
                 chat_id: str, user_id: int, username: str, content: str,
                 date: Union[datetime, str]
                 ):
        self.id = self.__get_message_id()
        self.chat_id = chat_id
        self.user_id = user_id
        self.username = username
        self.content = content
        self.date = date
        if isinstance(date, datetime):
            self.date = date.strftime('%d.%m.%Y')

    def __get_message_id(self) -> int:
        last_message_id = self.r_client.get('last_message_id') or 0
        new_id = int(last_message_id) + 1
        self.r_client.set('last_message_id', new_id)
        return new_id

    def save(self) -> None:
        messages_info = json.loads(
            self.r_client.hget('messages', self.chat_id) or '[]'
        )

        message_info = {
            'message_id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'content': self.content,
            'date': self.date
        }
        messages_info.append(message_info)
        self.r_client.hset('messages', self.chat_id, json.dumps(messages_info))

    @classmethod
    def get_messages_by_chat_id(cls, chat_id) -> Optional[dict]:
        data: Optional[bytes] = cls.r_client.hget('messages', chat_id)
        if isinstance(data, bytes):
            data: List = json.loads(data)
            print(data)
            data = sorted(data, key=lambda x: x['message_id'])
        return data


class Game(RedisClient):
    BOATS = {
        1: {'blocks': 1, 'defeat': False},
        3: {'blocks': 1, 'defeat': False},
        4: {'blocks': 1, 'defeat': False},
        2: {'blocks': 1, 'defeat': False},
        5: {'blocks': 1, 'defeat': False},
        6: {'blocks': 3, 'defeat': False},
        7: {'blocks': 3, 'defeat': False}
    }
    FIELDS = {
        '1A': {'attacked': False, 'boat': None}, '1B': {'attacked': False, 'boat': None}, '1C': {'attacked': False, 'boat': None}, '1D': {'attacked': False, 'boat': None}, '1E': {'attacked': False, 'boat': None}, '1F': {'attacked': False, 'boat': None}, '1G': {'attacked': False, 'boat': None}, '1H': {'attacked': False, 'boat': None}, '1K': {'attacked': False, 'boat': None}, '1L': {'attacked': False, 'boat': None},
        '2A': {'attacked': False, 'boat': None}, '2B': {'attacked': False, 'boat': None}, '2C': {'attacked': False, 'boat': None}, '2D': {'attacked': False, 'boat': None}, '2E': {'attacked': False, 'boat': None}, '2F': {'attacked': False, 'boat': None}, '2G': {'attacked': False, 'boat': None}, '2H': {'attacked': False, 'boat': None}, '2K': {'attacked': False, 'boat': None}, '2L': {'attacked': False, 'boat': None},
        '3A': {'attacked': False, 'boat': None}, '3B': {'attacked': False, 'boat': None}, '3C': {'attacked': False, 'boat': None}, '3D': {'attacked': False, 'boat': None}, '3E': {'attacked': False, 'boat': None}, '3F': {'attacked': False, 'boat': None}, '3G': {'attacked': False, 'boat': None}, '3H': {'attacked': False, 'boat': None}, '3K': {'attacked': False, 'boat': None}, '3L': {'attacked': False, 'boat': None},
    }

    def __init__(self, game_id: str):
        self.game_id = game_id
        game_data = self.__get_game_data()

        if game_data:
            self.turn = game_data['turn']
            self.winner = game_data['winner']
            self.is_end = game_data['is_end']

            self.player1_id = game_data['player1_id']
            self.player2_id = game_data['player2_id']

            self.player1_fields = game_data[str(self.player1_id)]['fields']
            self.player1_boats = game_data[str(self.player1_id)]['boats']

            self.player2_fields = game_data[str(self.player2_id)]['fields']
            self.player2_boats = game_data[str(self.player2_id)]['boats']
        else:
            self.game = GameModel.objects.get(game_id=game_id)

            self.player1_id = str(self.game.player1.id)
            self.player2_id = str(self.game.player2.id)

            self.turn = str(self.player1_id)
            self.winner = str(self.game.winner)
            self.is_end = self.game.is_end

            self.player1_fields = self.FIELDS
            self.player1_boats = self.BOATS

            self.player2_fields = self.FIELDS
            self.player2_boats = self.BOATS

    def __boats_load(self):
        # тут можно написать логику рандомного расположения кораблей
        # я ограничусь статическими значениями

        # player 1
        self.player1_fields['1A']['boat'] = 1
        self.player1_fields['1C']['boat'] = 2
        self.player1_fields['1E']['boat'] = 3
        self.player1_fields['1G']['boat'] = 4
        self.player1_fields['1K']['boat'] = 5

        self.player1_fields['3A']['boat'] = 6
        self.player1_fields['3B']['boat'] = 6
        self.player1_fields['3C']['boat'] = 6

        self.player1_fields['3E']['boat'] = 7
        self.player1_fields['3F']['boat'] = 7
        self.player1_fields['3G']['boat'] = 7

        # player 2
        self.player2_fields['1A']['boat'] = 1
        self.player2_fields['1C']['boat'] = 2
        self.player2_fields['1E']['boat'] = 3
        self.player2_fields['1G']['boat'] = 4
        self.player2_fields['1K']['boat'] = 5

        self.player2_fields['3A']['boat'] = 6
        self.player2_fields['3B']['boat'] = 6
        self.player2_fields['3C']['boat'] = 6

        self.player2_fields['3E']['boat'] = 7
        self.player2_fields['3F']['boat'] = 7
        self.player2_fields['3G']['boat'] = 7

    def __is_end(self, attacker_id: str):
        fields, boats = self.get_fields_and_boats_by_id(attacker_id)
        end = True

        # если есть хоть один живой корабль, то игра не закончена
        for boat in boats:
            if not boats[boat]['defeat']:
                end = False
        return end

    def __get_game_data(self):
        data = self.r_client.hget('games', self.game_id) or '{}'
        data = json.loads(data)
        return data

    def __set_game_data(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        self.r_client.hset('games', self.game_id, data)

    def __update_game_data(self, data_):
        data = self.__get_game_data()
        data.update(**data_)
        self.__set_game_data(data)

    def is_start(self):
        return bool(self.__get_game_data())

    def __get_player_fields_by_id(self, player_id: str):
        player_fields = self.player1_fields \
            if str(player_id) == str(self.player1_id) else self.player2_fields
        return player_fields

    def get_player_attacked_fields(self, player_id: str):
        player_fields = self.__get_player_fields_by_id(player_id)

        player_attacked_fields = {
            field: 'hit' if player_fields[field]['boat'] else 'miss'
            for field in player_fields
            if player_fields[field]['attacked']
        }
        return player_attacked_fields

    def get_player_boat_places(self, player_id: str):
        player_fields = self.__get_player_fields_by_id(player_id)

        player_boat_places = [
            field for field in player_fields if player_fields[field]['boat']
        ]
        return player_boat_places

    def get_fields_and_boats_by_id(self, attacker_id: str):
        if attacker_id == self.player1_id:
            fields = self.player2_fields
            boats = self.player2_boats
        elif attacker_id == self.player2_id:
            fields = self.player1_fields
            boats = self.player1_boats
        return [fields, boats]

    def get_another_player(self, attacker_id: str):
        return (
            self.player1_id if str(attacker_id) == self.player2_id else
            self.player2_id
        )

    def start(self):
        self.__boats_load()

        self.__update_game_data({
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,

            str(self.player1_id): {
                'boats': self.player1_boats,
                'fields': self.player1_fields
            },
            str(self.player2_id): {
                'boats': self.player2_boats,
                'fields': self.player2_fields
            },

            'turn': self.turn,
            'winner': self.winner,
            'is_end': self.is_end
        })

    def end(self, winner_id: str):
        self.winner = winner_id
        self.is_end = True

        self.__update_game_data(
            {
                'winner': self.winner,
                'is_end': self.is_end
            }
        )

    def attack(self, attacker_id: str, attacked_field: str):
        if isinstance(attacker_id, int):
            attacker_id = str(attacker_id)

        response = {
            'field': attacked_field,
            'hit': False
        }

        fields, boats = self.get_fields_and_boats_by_id(attacker_id)

        field = fields.get(attacked_field)
        boat = field['boat']

        if field['attacked']:  # если уже атаковано
            response['attacked'] = True
            return response

        field['attacked'] = True

        if boat:
            response['hit'] = True

            boat = str(boat)
            boats[boat]['blocks'] -= 1

            if boats[boat]['blocks'] == 0:
                boats[boat]['defeat'] = True
        else:
            self.turn = self.get_another_player(attacker_id)

        self.__update_game_data(
            {
                str(self.player1_id): {
                    'boats': self.player1_boats,
                    'fields': self.player1_fields
                },
                str(self.player2_id): {
                    'boats': self.player2_boats,
                    'fields': self.player2_fields
                },

                'turn': self.turn
            }
        )

        is_end = self.__is_end(attacker_id)
        if is_end:
            self.end(attacker_id)
        response['is_end'] = self.is_end
        return response

