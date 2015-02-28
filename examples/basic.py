import anyjson as json

import blorp
from blorp.utils import emit_to_all, on, json_message
from blorp.handler import BaseWebsocketHandler


class WebsocketHandler(BaseWebsocketHandler):

    def __init__(self, websocket_id):
        super().__init__(websocket_id)

    @on('json', ordered=False)
    @json_message
    def on_json(self, message, sender):
        yield from sender.emit(self.websocket_id, 'something',
                               json.dumps({'orig': message, 'new': 'hello {0}!'.format(self.websocket_id)}))

    @on('string')
    def on_string(self, message, sender):
        yield from sender.emit(self.websocket_id, 'something',
                               "you said {0}, I say 'hello {1}'".format(message, self.websocket_id))

    @on('.*')
    def on_everything_else(self, message, sender):
        yield from sender.emit_to_all('something', "{0} sent '{1}' to everyone!".format(self.websocket_id, message))


if __name__ == '__main__':
    thread, loop = blorp.start_in_new_thread(responder_cls=WebsocketHandler)

    try:
        while True:
            emit_to_all('something', input("Type something to say to the nice websockets: "))
    except KeyboardInterrupt as _:
        exit(0)
