import asyncio

import re
import redis
import anyjson as json


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
    def _wrapped_on_message_function(responder_instance, message):
        return on_message_function(responder_instance, json.loads(message))
    return _wrapped_on_message_function


@asyncio.coroutine
def call_blocking(f, *args):
    return (yield from asyncio.get_event_loop().run_in_executor(None, f, *args))
