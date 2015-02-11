# blorp
A 'bridge' that allows socket.io websocket connections to be used from (currently) Python via redis and node.js.
Uses redis' pubsub system and Python's asyncio module.

## Todo
- work out how messages on different socket.io channels will be passed to python and back
- support for objects and strings coming from socket.io client
- handle connect and disconnect in python
- work out how to do multiple backends (i.e. many python instances connected to the same node instance)