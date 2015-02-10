import asyncio
import asyncio_redis


@asyncio.coroutine
def example():
    # Create connection
    connection = yield from asyncio_redis.Connection.create(host='localhost', port=6379)

    # Inside a while loop, wait for incoming events.
    while True:
        reply = yield from connection.blpop(['ws.*'])
        print('Received: ', repr(reply.value), 'on list', reply.list_name)

    # When finished, close the connection.
    connection.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
