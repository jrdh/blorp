import anyjson as json

import blorp


class WebsocketHandler(blorp.BaseWebsocketHandler):

    def __init__(self, websocket_id, app):
        super().__init__(websocket_id, app)

    @blorp.on('json', ordered=False)
    @blorp.json_message
    def on_json(self, message):
        yield from self.app.send_async(self.websocket_id, 'something',
                                       json.dumps({'orig': message, 'new': 'hello {0}!'.format(self.websocket_id)}))

    @blorp.on('string')
    def on_string(self, message):
        session = yield from self.app.get_session(self.websocket_id)
        session['string_message_sent'] = True
        yield from self.app.save_session(self.websocket_id, session)
        yield from self.app.send_async(self.websocket_id, 'something',
                                       "you said {0}, I say 'hello {1}'".format(message, self.websocket_id))

    @blorp.on('.*')
    def on_everything_else(self, message):
        yield from self.app.send_async_to_all('something',
                                              "{0} sent '{1}' to everyone!".format(self.websocket_id, message))


if __name__ == '__main__':
    blorp_app = blorp.BlorpApp('basic', handler_cls=WebsocketHandler)
    blorp_app.start_in_new_thread()

    try:
        while True:
            blorp_app.send_sync_to_all('something', input("Type something to say to the nice websockets: "))
    except KeyboardInterrupt as _:
        blorp_app.stop()
        exit(0)
