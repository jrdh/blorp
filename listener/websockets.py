import asyncio

import asyncio_redis


class WebSocketResponder:

    def __init__(self, socket_id, to_channel, back_channel):
        self.socket_id = socket_id
        self.to_channel = to_channel
        self.back_channel = back_channel
        self.message_count = 0

    @asyncio.coroutine
    def on_message(self, message, sender):
        self.message_count += 1
        yield from sender.publish(self.back_channel, message)


class WebSocketLoop:

    def __init__(self, to_channel_prefix, back_channel_prefix):
        self.to_channel_prefix = to_channel_prefix
        self.back_channel_prefix = back_channel_prefix
        self.responders = {}

    @asyncio.coroutine
    def loop(self):
        # Create connection
        receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        sender = yield from asyncio_redis.Connection.create(host='localhost', port=6379)

        # Create subscriber.
        subscriber = yield from receiver.start_subscribe()

        # Subscribe to channel.
        yield from subscriber.psubscribe(['{0}*'.format(self.to_channel_prefix)])

        # Inside a while loop, wait for incoming events.
        while True:
            message = yield from subscriber.next_published()
            websocket_id = message.channel[len(self.to_channel_prefix):]
            if websocket_id not in self.responders:
                self.responders[websocket_id] = WebSocketResponder(websocket_id, self.to_channel_prefix + websocket_id,
                                                                   self.back_channel_prefix + websocket_id)
            yield from self.responders[websocket_id].on_message(message.value, sender)

        # When finished, close the connection.
        receiver.close()
        sender.close()


if __name__ == '__main__':
    websocket_loop = WebSocketLoop('ws:to:', 'ws:back:')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_loop.loop())
