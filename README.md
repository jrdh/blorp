# Blorp
A 'bridge' that allows socket.io websocket connections to be used from other programming languages via redis and node.js.

## Co-implementations (clients-ish)
[blorp-python](https://github.com/jrdh/blorp-python)


## Todo
- implement instance switching (i.e. when a client instance shuts down, move the messages to another one if there is one)
- implement dynamic namespaces (using redis keyspace notifcations?)
- tidy (~)
- tests
- investigate using hashes in redis
- Javascript client library (i.e. for the browser)


## To think about...
- work out how to do cope with load balancing (almost there...)

