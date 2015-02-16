# blorp
A 'bridge' that allows socket.io websocket connections to be used from (currently) Python via redis and node.js.
Uses redis' pubsub system and Python's asyncio module.

## Todo
- call blocking functions from registered on_* callbacks
- tidy (~)
- tests
- threadsafety of blorp.websockets set (in fact of most of it)

## To think about...
- work out how to do cope with load balancing
