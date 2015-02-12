import asyncio
import json

import asyncio_redis


class WebSocketResponder:

    def __init__(self, socket_id, to_channel, back_channel):
        """
        Called when a new websocket connection is created.
        :param socket_id: the id of the websocket
        :param to_channel: the to channel for this websocket
        :param back_channel: the back channel for this websocket
        :return: a new instance of a responder
        """
        self.socket_id = socket_id
        self.to_channel = to_channel
        self.back_channel = back_channel
        self.message_count = 0

    @asyncio.coroutine
    def on_disconnection(self):
        """
        Called when the websocket connection is lost.
        :return:
        """
        pass

    @asyncio.coroutine
    def on_message(self, message, sender):
        """
        Called when a message is received by the websocket this responder is attached to.
        :param message: the message that was sent to the server through the attached websocket
        :param sender: a redis client instance that allows this function to immediately respond back in various ways
        :return:
        """
        self.message_count += 1
        json_message = json.loads(message)
        json_message['beans'] = True
        yield from sender.publish(self.back_channel, json.dumps(json_message))


class WebSocketResponderFactory:

    def __init__(self, to_channel_prefix, back_channel_prefix):
        self.to_channel_prefix = to_channel_prefix
        self.back_channel_prefix = back_channel_prefix

    def get_new_responder(self, websocket_id):
        """
        Creates and returns a new responder for the given websocket id.
        :param websocket_id: the websocket's id
        :return: a new responder instance configured for communication with the given websocket
        """
        return WebSocketResponder(websocket_id, self.to_channel_prefix + websocket_id,
                                  self.back_channel_prefix + websocket_id)


class WebSocketLoop:

    def __init__(self, factory):
        self.factory = factory
        self.responders = {}
        self.run = True

    def start(self, event_loop=None):
        """
        Starts all the async tasks that manage websocket connections, disconnections and messages.
        :param event_loop: optional event loop to run on
        :return:
        """
        asyncio.async(self.connection_loop(), loop=event_loop)
        asyncio.async(self.disconnection_loop(), loop=event_loop)
        asyncio.async(self.message_loop(), loop=event_loop)

    @asyncio.coroutine
    def connection_loop(self):
        """
        Listens for disconnections pushed to a redis queue from the node.js server.
        :return:
        """
        connection_receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        while self.run:
            message = yield from connection_receiver.blpop(['ws:connections'])
            websocket_id = message.value
            self.responders[websocket_id] = self.factory.get_new_responder(websocket_id)
        connection_receiver.close()

    @asyncio.coroutine
    def disconnection_loop(self):
        """
        Listens for connections pushed to a redis queue from the node.js server.
        :return:
        """
        disconnection_receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        while self.run:
            message = yield from disconnection_receiver.blpop(['ws:disconnections'])
            websocket_id = message.value
            if websocket_id in self.responders:
                yield from self.responders[websocket_id].on_disconnection()
                del self.responders[websocket_id]
        disconnection_receiver.close()

    @asyncio.coroutine
    def message_loop(self):
        """
        Listens for messages to all websockets and passes the messages to the corresponding responder when they arrive.
        :return:
        """
        message_receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
        message_sender = yield from asyncio_redis.Connection.create(host='localhost', port=6379)

        subscriber = yield from message_receiver.start_subscribe()
        yield from subscriber.psubscribe(['{0}*'.format(self.factory.to_channel_prefix)])

        # channels have the form to_prefix:<websocket_id>, for example: ws:to:IUv43I9r_BFELoe4
        to_prefix_length = len(self.factory.to_channel_prefix)

        while self.run:
            message = yield from subscriber.next_published()
            websocket_id = message.channel[to_prefix_length:]
            if websocket_id in self.responders:
                yield from self.responders[websocket_id].on_message(message.value, message_sender)
        message_receiver.close()
        message_sender.close()


if __name__ == '__main__':
    websocket_responder_factory = WebSocketResponderFactory('ws:to:', 'ws:back:')
    websocket_loop = WebSocketLoop(websocket_responder_factory)
    loop = asyncio.get_event_loop()
    websocket_loop.start(event_loop=loop)
    loop.run_forever()
