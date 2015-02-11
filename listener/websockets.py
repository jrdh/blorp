import asyncio
import asyncio_redis


@asyncio.coroutine
def example():
    # Create connection
    receiver = yield from asyncio_redis.Connection.create(host='localhost', port=6379)
    sender = yield from asyncio_redis.Connection.create(host='localhost', port=6379)

    # Create subscriber.
    subscriber = yield from receiver.start_subscribe()

    # Subscribe to channel.
    yield from subscriber.psubscribe(['ws:to:*'])

    # Inside a while loop, wait for incoming events.
    while True:
        reply = yield from subscriber.next_published()
        print('Received: ', repr(reply.value), 'on channel', reply.channel, 'back channel',
              reply.channel.replace('ws:to:', 'ws:back:'))
        yield from sender.publish(reply.channel.replace('ws:to:', 'ws:back:'), 'Hello there!')

    # When finished, close the connection.
    receiver.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
