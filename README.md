# blorp
A 'bridge' that allows socket.io websocket connections to be used from (currently) Python via redis and node.js.
Uses redis and Python's asyncio module.

## Todo
- call blocking functions from registered on_* callbacks
- tidy (~)
- tests
- threadsafety of blorp.websockets set (in fact most of it)

## To think about...
- work out how to do cope with load balancing (this is now way more possible with a queue rather than using redis' pubsub)
