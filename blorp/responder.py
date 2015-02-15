import asyncio
from functools import partial
import json

from blorp import register, json_message


class Responder:

    def __init__(self, websocket_id, response_channel):
        self.websocket_id = websocket_id
        self.response_channel = response_channel

    @asyncio.coroutine
    def on_disconnection(self):
        pass

    @register('json')
    @json_message
    def on_json(self, message, sender):
        yield from sender.emit(self.response_channel, 'something', "why hello there from json")

    @register('string')
    def on_string(self, message, sender):
        yield from sender.emit(self.response_channel, 'something', "why hello there from string")


class ResponderFactory:

    def __init__(self):
        pass

    def get_new_responder(self, websocket_id, response_channel):
        return Responder(websocket_id, response_channel)


class ResponderRouter:

    def __init__(self, factory, event_dict, back_channel_prefix):
        self.factory = factory
        self.event_dict = event_dict
        self.back_channel_prefix = back_channel_prefix
        self.responders = {}

    @asyncio.coroutine
    def add_responder(self, websocket_id):
        self.responders[websocket_id] = self.factory.get_new_responder(websocket_id,
                                                                       self.back_channel_prefix + websocket_id)

    @asyncio.coroutine
    def remove_responder(self, websocket_id):
        if websocket_id in self.responders:
            yield from self.responders[websocket_id].on_disconnection()
            del self.responders[websocket_id]

    @asyncio.coroutine
    def route(self, websocket_id, event, data, sender):
        for regex, on_message_function in self.event_dict.items():
            if regex.match(event) and websocket_id in self.responders:
                yield from on_message_function(self.responders[websocket_id], data, sender)
