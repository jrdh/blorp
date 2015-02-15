# blorp
A 'bridge' that allows socket.io websocket connections to be used from (currently) Python via redis and node.js.
Uses redis' pubsub system and Python's asyncio module.

## Todo
- python on_message refactor to allow registration of functions to websocket events


## To think about...
- work out how to do cope with balancing
