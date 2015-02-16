import asyncio
import json
import re

import asyncio_redis
import redis

import blorp


blocking_redis = redis.StrictRedis()


def register(event_regex, re_flags=0):
    def wrap(f):
        blorp.event_handlers[re.compile(event_regex, re_flags)] = f

        @asyncio.coroutine
        def wrapped_f(*args):
            f(*args)
        return wrapped_f
    return wrap


def json_message(on_message_function):
    def _wrapped_on_message_function(responder_instance, message, sender):
        return on_message_function(responder_instance, json.loads(message), sender)
    return _wrapped_on_message_function


def channel_for(websocket_id):
    return '{0}{1}'.format(blorp.back_channel_prefix, websocket_id)


def emit(channel, event, message):
    blocking_redis.publish(channel, json.dumps({'event': event, 'data': message}))


def emit_to_all(event, message):
    emit(blorp.all_channel, event, message)


def emit_to(websocket_id, event, message):
    emit(channel_for(websocket_id), event, message)


class AsyncSender:

    def __init__(self):
        self.message_sender = None

    @classmethod
    @asyncio.coroutine
    def create(cls):
        sender = cls()
        sender.message_sender = yield from asyncio_redis.Connection.create()
        return sender

    @asyncio.coroutine
    def emit(self, channel, event, message):
        yield from self.message_sender.publish(channel, json.dumps({'event': event, 'data': message}))

    @asyncio.coroutine
    def emit_to(self, websocket_id, event, message):
        yield from self.emit(channel_for(websocket_id), event, message)

    @asyncio.coroutine
    def emit_to_all(self, event, message):
        yield from self.emit(blorp.all_channel, event, message)

    def close(self):
        self.message_sender.close()
