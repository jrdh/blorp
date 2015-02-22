import asyncio
import threading


websockets = set()
event_handlers = {}
to_queue = 'blorp:to'
back_queue = 'blorp:back'


from blorp.loop import ResponderLoop
from blorp.responder import ResponderFactory, ResponderRouter


def start(router_cls=ResponderRouter, factory_cls=ResponderFactory, event_loop=None):
    """
    Starts the websocket listening service with the given optional parameters. The event loop is started on the current
    thread.
    :param router_cls: the class to instantiate for the router object (optional)
    :param factory_cls: the class to instantiate for the factory object (optional)
    :param event_loop: the event loop to use (optional)
    """
    factory = factory_cls()
    router = router_cls(factory, event_handlers)
    websocket_loop = ResponderLoop(router)
    if not event_loop:
        event_loop = asyncio.get_event_loop()
    asyncio.set_event_loop(event_loop)
    websocket_loop.start(event_loop=event_loop)
    event_loop.run_forever()


def start_in_new_thread(event_loop=None, **kwargs):
    """
    Starts the websocket listening service with the given optional parameters on a new thread and then returns that
    thread and the event loop used as a tuple.
    :param router_cls: the class to instantiate for the router object (optional)
    :param factory_cls: the class to instantiate for the factory object (optional)
    :param event_loop: the event loop to use (optional)
    """
    if not event_loop:
        # we need to make sure the event loop is created in this thread so that we can pass it back
        event_loop = asyncio.get_event_loop()
    kwargs.update({'event_loop': event_loop})
    thread = threading.Thread(target=start, kwargs=kwargs)
    thread.start()
    return thread, event_loop
