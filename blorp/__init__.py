import asyncio
import json
import re


default_namespace = 'default'
_message_responders = {}


def register(event_regex, namespace=default_namespace, re_flags=0):
    def wrap(f):
        if namespace not in _message_responders:
            _message_responders[namespace] = {}
        _message_responders[namespace][re.compile(event_regex, re_flags)] = f

        @asyncio.coroutine
        def wrapped_f(*args):
            f(*args)
        return wrapped_f
    return wrap


def json_message(on_message_function):
    def _wrapped_on_message_function(responder_instance, message, sender):
        return on_message_function(responder_instance, json.loads(message), sender)
    return _wrapped_on_message_function


from blorp.loop import ResponderLoop
from blorp.responder import ResponderFactory, ResponderRouter


def start(router=ResponderRouter, factory=ResponderFactory, namespace=default_namespace, event_loop=None,
          run_forever=True):
    to_channel_prefix = 'ws:to:'
    back_channel_prefix = 'ws:back:'
    factory_instance = factory()
    router_instance = router(factory_instance, _message_responders[namespace], back_channel_prefix)
    websocket_loop = ResponderLoop(router_instance, to_channel_prefix, back_channel_prefix)
    if not event_loop:
        event_loop = asyncio.get_event_loop()
    websocket_loop.start(event_loop=event_loop)
    if run_forever:
        event_loop.run_forever()
