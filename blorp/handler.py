import asyncio

import blorp
from blorp.utils import AsyncSender


class BaseWebsocketHandler:

    def __init__(self, websocket_id):
        self.websocket_id = websocket_id
        self.message_queue = asyncio.Queue()
        self.go = True

    @asyncio.coroutine
    def on_connection(self):
        while self.go:
            message_handler, data, async_sender = yield from self.message_queue.get()
            yield from message_handler(self, data, async_sender)

    @asyncio.coroutine
    def on_disconnection(self):
        self.go = False


class BaseWebsocketHandlerFactory:

    def __init__(self, responder_cls=BaseWebsocketHandler):
        self.responder_cls = responder_cls

    @asyncio.coroutine
    def get_new_websocket_handler(self, websocket_id):
        websocket_handler = self.responder_cls(websocket_id)
        asyncio.async(websocket_handler.on_connection())
        return websocket_handler


class BaseWebsocketHandlerRouter:

    def __init__(self, factory, message_handlers):
        self.factory = factory
        self.message_handlers = message_handlers
        self.websocket_handlers = {}
        self.async_sender = None

    @asyncio.coroutine
    def add_websocket_handler(self, websocket_id):
        blorp.websockets.add(websocket_id)
        self.websocket_handlers[websocket_id] = yield from self.factory.get_new_websocket_handler(websocket_id)

    @asyncio.coroutine
    def remove_websocket_handler(self, websocket_id):
        blorp.websockets.discard(websocket_id)
        if websocket_id in self.websocket_handlers:
            yield from self.websocket_handlers[websocket_id].on_disconnection()
            del self.websocket_handlers[websocket_id]

    @asyncio.coroutine
    def route(self, websocket_id, event, data):
        if not self.async_sender:
            self.async_sender = yield from AsyncSender.create()
        for regex, on_message_function in self.message_handlers:
            if regex.match(event) and websocket_id in self.websocket_handlers:
                websocket_handler = self.websocket_handlers[websocket_id]
                if on_message_function.in_order:
                    # add to message queue for that websocket responder
                    yield from websocket_handler.message_queue.put((on_message_function, data, self.async_sender))
                else:
                    # run responder immediately
                    asyncio.async(on_message_function(websocket_handler, data, self.async_sender))
                break

    def close(self):
        self.async_sender.close()
