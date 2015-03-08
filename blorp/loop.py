import asyncio
import uuid

import anyjson as json
import asyncio_redis
from blorp import pool


class WebsocketHandlerLoop:

    def __init__(self, router):
        self.router = router
        self.run = True
        self.event_loop = None
        self.instance_id = None

    def start(self, event_loop=None):
        self.event_loop = event_loop
        pool.init_sync_pool()
        asyncio.async(pool.init_async_pool(), loop=self.event_loop)
        asyncio.async(self.message_loop(), loop=self.event_loop)
        self.register()

    def register(self):
        attempts = 0
        while attempts < 3:
            potential_instance_id = uuid.uuid4()
            if pool.sync.sadd('blorp:instances', potential_instance_id):
                self.instance_id = potential_instance_id
                return
            attempts += 1

    @asyncio.coroutine
    def message_loop(self):
        message_receiver = yield from asyncio_redis.Connection.create()

        message_handlers = {
            'connection': lambda m: self.router.add_websocket_handler(m['websocketId']),
            'disconnection': lambda m: self.router.remove_websocket_handler(m['websocketId']),
            'message': lambda m: self.router.route(m['websocketId'], m['event'], m['data'])
        }

        while self.run:
            raw_message = yield from message_receiver.blpop(['blorp:queues:{0}'.format(self.instance_id)])
            message = json.loads(raw_message.value)
            yield from message_handlers[message['type']](message)

        message_receiver.close()

    def close(self):
        pool.sync.srem('blorp:instances', self.instance_id)
        pool.async.close()
        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
