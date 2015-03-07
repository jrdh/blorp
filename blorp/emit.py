import asyncio

import anyjson as json
from blorp import pool
from blorp import back_queue


def create_message(to, event, data):
    return json.dumps({'id': to, 'event': event, 'data': data})


def sync(to, event, data):
    pool.sync_pool.rpush(back_queue, create_message(to, event, data))


def sync_to_all(event, data):
    sync(None, event, data)


@asyncio.coroutine
def async(to, event, data):
    yield from pool.async_pool.rpush(back_queue, [create_message(to, event, data)])


@asyncio.coroutine
def async_to_all(event, data):
    # None to implies send to all websocket clients
    yield from async(None, event, data)
