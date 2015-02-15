import asyncio

import asyncio_redis


class ResponderLoop:

    def __init__(self, router, to_channel_prefix, back_channel_prefix):
        self.router = router
        self.to_channel_prefix = to_channel_prefix
        self.back_channel_prefix = back_channel_prefix
        self.run = True

    def start(self, event_loop=None):
        asyncio.async(self.connection_loop(), loop=event_loop)
        asyncio.async(self.disconnection_loop(), loop=event_loop)
        asyncio.async(self.message_loop(), loop=event_loop)

    @asyncio.coroutine
    def connection_loop(self):
        connection_receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        while self.run:
            message = yield from connection_receiver.blpop(['ws:connections'])
            yield from self.router.add_responder(message.value)
        connection_receiver.close()

    @asyncio.coroutine
    def disconnection_loop(self):
        disconnection_receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        while self.run:
            message = yield from disconnection_receiver.blpop(['ws:disconnections'])
            yield from self.router.remove_responder(message.value)
        disconnection_receiver.close()

    @asyncio.coroutine
    def message_loop(self):
        message_receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        message_sender = yield from asyncio_redis.Connection.create(host='localhost', port=6379)

        subscriber = yield from message_receiver.start_subscribe()
        yield from subscriber.psubscribe(['{0}*'.format(self.to_channel_prefix)])

        # channels have the form to_prefix:<websocket_id>, for example: ws:to:IUv43I9r_BFELoe4
        to_prefix_length = len(self.to_channel_prefix)

        while self.run:
            message = yield from subscriber.next_published()
            descriptor = message.channel[to_prefix_length:].split(':')
            websocket_id = descriptor[0]
            event = descriptor[1]
            yield from self.router.route(websocket_id, event, message.value, message_sender)

        message_receiver.close()
        message_sender.close()
