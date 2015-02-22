import asyncio
import re

import asyncio_redis
import redis
import anyjson as json

import blorp


blocking_redis = redis.StrictRedis()


def on(event_regex, re_flags=0, ordered=True):
    def wrap(f):
        f.in_order = ordered
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


def create_message(to, event, data):
    return json.dumps({'id': to, 'event': event, 'data': data})


def emit(to, event, data):
    blocking_redis.rpush(blorp.back_queue, create_message(to, event, data))


def emit_to_all(event, data):
    emit(None, event, data)


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
    def emit(self, to, event, data):
        yield from self.message_sender.rpush(blorp.back_queue, [create_message(to, event, data)])

    @asyncio.coroutine
    def emit_to_all(self, event, data):
        # None to implies send to all websocket clients
        yield from self.emit(None, event, data)

    def close(self):
        self.message_sender.close()


@asyncio.coroutine
def call_blocking(f, *args):
    return_value = yield from asyncio.get_event_loop().run_in_executor(None, f, *args)
    return return_value
