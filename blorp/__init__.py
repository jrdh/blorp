import asyncio
import threading


websockets = set()
event_handlers = {}
to_channel_prefix = 'blorp:to:'
back_channel_prefix = 'blorp:back:'
all_channel = 'blorp:all'


from blorp.loop import ResponderLoop
from blorp.responder import ResponderFactory, ResponderRouter


def start(router_cls=ResponderRouter, factory_cls=ResponderFactory, event_loop=None):
    factory = factory_cls()
    router = router_cls(factory, event_handlers)
    websocket_loop = ResponderLoop(router)
    if not event_loop:
        event_loop = asyncio.get_event_loop()
    asyncio.set_event_loop(event_loop)
    websocket_loop.start(event_loop=event_loop)
    event_loop.run_forever()


def start_in_new_thread(event_loop=None, **kwargs):
    if not event_loop:
        event_loop = asyncio.get_event_loop()
    kwargs.update({'event_loop': event_loop})
    t = threading.Thread(target=start, kwargs=kwargs)
    t.start()
    return t, event_loop
