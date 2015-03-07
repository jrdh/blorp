import asyncio
import asyncio_redis
import redis


async_pool = None
sync_pool = None


@asyncio.coroutine
def init_async_pool(host='localhost', port=6379, size=10):
    global async_pool
    async_pool = yield from asyncio_redis.Pool.create(host=host, port=port, poolsize=size)


def init_sync_pool(host='localhost', port=6379):
    global sync_pool
    sync_pool = redis.StrictRedis(host=host, port=port)
