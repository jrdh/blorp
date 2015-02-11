import asyncio
import json

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
        print('({0})[{1}]: {2}'.format(self.socket_id, self.message_count, message))
        json_message = json.loads(message)
        json_message['arms'] = 3289
        yield from sender.publish(self.back_channel, json.dumps(json_message))


class WebSocketResponderFactory:

    def __init__(self, to_channel_prefix, back_channel_prefix):
        self.to_channel_prefix = to_channel_prefix
        self.back_channel_prefix = back_channel_prefix

    def get_new_responder(self, websocket_id):
        return WebSocketResponder(websocket_id, self.to_channel_prefix + websocket_id,
                                  self.back_channel_prefix + websocket_id)


class WebSocketLoop:

    def __init__(self, factory):
        self.factory = factory
        self.responders = {}

    @asyncio.coroutine
    def loop(self):
        # Create connection
        receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        sender = yield from asyncio_redis.Connection.create(host='localhost', port=6379)

        # Create subscriber.
        subscriber = yield from receiver.start_subscribe()

        # Subscribe to channel.
        yield from subscriber.psubscribe(['{0}*'.format(self.factory.to_channel_prefix)])

        to_prefix_length = len(self.factory.to_channel_prefix)

        # Inside a while loop, wait for incoming events.
        while True:
            message = yield from subscriber.next_published()
            websocket_id = message.channel[to_prefix_length:]
            if websocket_id not in self.responders:
                self.responders[websocket_id] = self.factory.get_new_responder(websocket_id)
            yield from self.responders[websocket_id].on_message(message.value, sender)

        # When finished, close the connection.
        receiver.close()
        sender.close()


if __name__ == '__main__':
    websocket_responder_factory = WebSocketResponderFactory('ws:to:', 'ws:back:')
    websocket_loop = WebSocketLoop(websocket_responder_factory)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_loop.loop())
