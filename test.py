# from random import choice
#
#
# a = (
#     (1, 1),
#     (2, 2,)
# )
#
# print(choice(a))

# import redis
# import json
#
# r = redis.Redis()
# client = r.client()
#
# # client.hset('messages', 0.5, json.dumps({1: 123}))
# # print(client.hget('messages', 0.52))
# # print(type(b'None')
# print(
#     client.set('last_message_id', 0 + 1)
# )
from django.utils.timezone import datetime


a = datetime.now().strftime('%d.%m.%Y %X')
print(
    a
)
