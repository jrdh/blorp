import asyncio
import asyncio_redis
import redis


async = None
sync = None


@asyncio.coroutine
def init_async_pool(host='localhost', port=6379, size=10):
    global async
    async = yield from asyncio_redis.Pool.create(host=host, port=port, poolsize=size)


def init_sync_pool(host='localhost', port=6379):
    global sync
    sync = redis.StrictRedis(host=host, port=port)
