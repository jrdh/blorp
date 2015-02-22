import asyncio

import blorp
from blorp.utils import on, json_message, AsyncSender


class Responder:

    def __init__(self, websocket_id):
        self.websocket_id = websocket_id
        self.response_queue = asyncio.Queue()
        self.go = False

    @asyncio.coroutine
    def on_connection(self):
        self.go = True
        while self.go:
            on_message_function, data, async_sender = yield from self.response_queue.get()
            yield from on_message_function(self, data, async_sender)

    @asyncio.coroutine
    def on_disconnection(self):
        self.go = False

    @on('json')
    @json_message
    def on_json(self, message, sender):
        yield from sender.emit(self.websocket_id, 'something', "why hello there from json")

    @on('string')
    def on_string(self, message, sender):
        yield from sender.emit(self.websocket_id, 'something', "why hello there from string")

    @on('toAll')
    def on_string(self, message, sender):
        yield from sender.emit_to_all('something', "{0} sent '{1}' to everyone!".format(self.websocket_id, message))


class ResponderFactory:

    @asyncio.coroutine
    def get_new_responder(self, websocket_id):
        responder = Responder(websocket_id)
        asyncio.async(responder.on_connection())
        return responder


class ResponderRouter:

    def __init__(self, factory, event_dict):
        self.factory = factory
        self.event_dict = event_dict
        self.responders = {}
        self.async_sender = None

    @asyncio.coroutine
    def add_responder(self, websocket_id):
        blorp.websockets.add(websocket_id)
        self.responders[websocket_id] = yield from self.factory.get_new_responder(websocket_id)

    @asyncio.coroutine
    def remove_responder(self, websocket_id):
        blorp.websockets.discard(websocket_id)
        if websocket_id in self.responders:
            yield from self.responders[websocket_id].on_disconnection()
            del self.responders[websocket_id]

    @asyncio.coroutine
    def route(self, websocket_id, event, data):
        if not self.async_sender:
            self.async_sender = yield from AsyncSender.create()
        for regex, on_message_function in self.event_dict.items():
            if regex.match(event) and websocket_id in self.responders:
                responder = self.responders[websocket_id]
                yield from responder.response_queue.put((on_message_function, data, self.async_sender))

    def close(self):
        self.async_sender.close()
