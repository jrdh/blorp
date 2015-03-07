import asyncio
import asyncio_redis

import anyjson as json


session_id_template = 'blorp:sessions:{0}'
websocket_id_key = 'websocket_id'
default_ttl = 1800
redis = None


@asyncio.coroutine
def init():
    global redis
    redis = yield from asyncio_redis.Connection.create()


@asyncio.coroutine
def save_session(session):
    websocket_id = session[websocket_id_key]
    yield from redis.set(session_id_template.format(websocket_id), json.dumps(session), expire=default_ttl)


@asyncio.coroutine
def create_new_session(websocket_id):
    session = {websocket_id_key: websocket_id}
    yield from save_session(session)
    return session


@asyncio.coroutine
def delete_session(websocket_id):
    yield from redis.delete(session_id_template.format(websocket_id))


@asyncio.coroutine
def touch_session(websocket_id):
    yield from redis.expire(session_id_template.format(websocket_id), default_ttl)


@asyncio.coroutine
def get_session(websocket_id, create=True):
    session = yield from redis.get(session_id_template.format(websocket_id))
    if session:
        yield from touch_session(websocket_id)
        return json.loads(session)
    elif create:
        return (yield from create_new_session(websocket_id))
    return None
