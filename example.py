import blorp
from blorp.utils import emit_to_all


if __name__ == '__main__':
    thread, loop = blorp.start_in_new_thread()

    while True:
        text = input("Type something to say to the nice websockets: ")
        emit_to_all('something', text)
        # for websocket_id in blorp.websockets:
        #     emit_to(websocket_id, 'something', 'sending something to each individually :) {0}'.format(text))
