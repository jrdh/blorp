import asyncio

import anyjson as json
import asyncio_redis
import blorp


class ResponderLoop:

    def __init__(self, router):
        self.router = router
        self.run = True
        self.event_loop = None

    def start(self, event_loop=None):
        self.event_loop = event_loop
        asyncio.async(self.message_loop(), loop=self.event_loop)

    @asyncio.coroutine
    def message_loop(self):
        message_receiver = yield from asyncio_redis.Connection.create()

        message_handlers = {
            'connection': lambda m: self.router.add_responder(m['websocketId']),
            'disconnection': lambda m: self.router.remove_responder(m['websocketId']),
            'message': lambda m: self.router.route(m['websocketId'], m['event'], m['data'])
        }

        while self.run:
            raw_message = yield from message_receiver.blpop([blorp.to_queue])
            message = json.loads(raw_message.value)
            asyncio.async(message_handlers[message['type']](message), loop=self.event_loop)

        message_receiver.close()
