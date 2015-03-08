import asyncio

import asyncio_redis
import anyjson as json


class BaseWebsocketHandler:

    def __init__(self, websocket_id, app):
        self.websocket_id = websocket_id
        self.app = app
        self.message_queue = asyncio.Queue()
        self.go = True

    @asyncio.coroutine
    def on_connection(self):
        while self.go:
            message_handler, data = yield from self.message_queue.get()
            yield from message_handler(self, data)

    @asyncio.coroutine
    def on_disconnection(self):
        self.go = False


class BaseWebsocketHandlerFactory:

    def __init__(self, app):
        self.app = app

    @asyncio.coroutine
    def get_new_websocket_handler(self, websocket_id):
        websocket_handler = self.app.handler_cls(websocket_id, self.app)
        asyncio.async(websocket_handler.on_connection())
        return websocket_handler


class BaseWebsocketHandlerRouter:

    def __init__(self, app):
        self.app = app
        self.websocket_handlers = {}
        self.async_sender = None

    @asyncio.coroutine
    def add_websocket_handler(self, websocket_id):
        yield from self.app.get_session(websocket_id, create=True)
        self.websocket_handlers[websocket_id] = yield from self.app.factory.get_new_websocket_handler(websocket_id)

    @asyncio.coroutine
    def remove_websocket_handler(self, websocket_id):
        if websocket_id in self.websocket_handlers:
            yield from self.websocket_handlers[websocket_id].on_disconnection()
            yield from self.app.delete_session(websocket_id)
            del self.websocket_handlers[websocket_id]

    @asyncio.coroutine
    def route(self, websocket_id, event, data):
        for regex, on_message_function in self.app.message_handlers:
            if regex.match(event) and websocket_id in self.websocket_handlers:
                websocket_handler = self.websocket_handlers[websocket_id]
                # ensure there is a session for this websocket
                yield from self.app.get_session(websocket_id)
                if on_message_function.in_order:
                    # add to message queue for that websocket responder
                    yield from websocket_handler.message_queue.put((on_message_function, data))
                else:
                    # run responder immediately
                    asyncio.async(on_message_function(websocket_handler, data))
                break


class WebsocketReceiver:

    def __init__(self, app):
        self.app = app
        self.run = True

    @asyncio.coroutine
    def message_loop(self):
        message_receiver = yield from asyncio_redis.Connection.create()

        message_handlers = {
            'connection': lambda m: self.app.router.add_websocket_handler(m['websocketId']),
            'disconnection': lambda m: self.app.router.remove_websocket_handler(m['websocketId']),
            'message': lambda m: self.app.router.route(m['websocketId'], m['event'], m['data'])
        }

        while self.run:
            raw_message = yield from message_receiver.blpop([self.app.keys['queues']])
            message = json.loads(raw_message.value)
            yield from message_handlers[message['type']](message)

        message_receiver.close()
