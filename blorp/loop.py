import asyncio
import json

import asyncio_redis
import blorp


class ResponderLoop:

    def __init__(self, router):
        self.router = router
        self.run = True

    def start(self, event_loop=None):
        asyncio.async(self.connection_loop(), loop=event_loop)
        asyncio.async(self.message_loop(), loop=event_loop)

    @asyncio.coroutine
    def connection_loop(self):
        connection_receiver = yield from asyncio_redis.Connection.create()
        while self.run:
            message = yield from connection_receiver.blpop(['blorp:connections'])
            json_message = json.loads(message.value)
            if 'connect' in json_message and json_message['connect']:
                yield from self.router.add_responder(json_message['id'])
            elif 'disconnect' in json_message and json_message['disconnect']:
                yield from self.router.remove_responder(json_message['id'])
        connection_receiver.close()

    @asyncio.coroutine
    def message_loop(self):
        message_receiver = yield from asyncio_redis.Connection.create()

        subscriber = yield from message_receiver.start_subscribe()
        yield from subscriber.psubscribe(['{0}*'.format(blorp.to_channel_prefix)])

        to_prefix_length = len(blorp.to_channel_prefix)

        while self.run:
            message = yield from subscriber.next_published()
            descriptor = message.channel[to_prefix_length:].split(':')
            websocket_id = descriptor[0]
            event = descriptor[1]
            yield from self.router.route(websocket_id, event, message.value)

        message_receiver.close()
