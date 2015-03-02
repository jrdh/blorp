import asyncio
import re

import asyncio_redis
import redis
import anyjson as json

from blorp import back_queue


blocking_redis = redis.StrictRedis()
_handler_counter = 0


def on(event_regex, re_flags=0, ordered=True, order=None):
    global _handler_counter
    _handler_counter += 1

    def wrap(f):
        @asyncio.coroutine
        def wrapped_f(*args):
            f(*args)
        wrapped_f.message_handler = True
        wrapped_f.event_regex = re.compile(event_regex, re_flags)
        f.in_order = ordered
        wrapped_f.original = f
        f.order = order if order else _handler_counter
        return wrapped_f
    return wrap


def json_message(on_message_function):
    def _wrapped_on_message_function(responder_instance, message, sender):
        return on_message_function(responder_instance, json.loads(message), sender)
    return _wrapped_on_message_function


def create_message(to, event, data):
    return json.dumps({'id': to, 'event': event, 'data': data})


def emit(to, event, data):
    blocking_redis.rpush(back_queue, create_message(to, event, data))


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
        yield from self.message_sender.rpush(back_queue, [create_message(to, event, data)])

    @asyncio.coroutine
    def emit_to_all(self, event, data):
        # None to implies send to all websocket clients
        yield from self.emit(None, event, data)

    def close(self):
        self.message_sender.close()


@asyncio.coroutine
def call_blocking(f, *args):
    return (yield from asyncio.get_event_loop().run_in_executor(None, f, *args))
