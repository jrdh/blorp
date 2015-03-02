import asyncio
import threading
import inspect

websockets = set()
to_queue = 'blorp:to'
back_queue = 'blorp:back'

from blorp.loop import WebsocketHandlerLoop
from blorp.handler import BaseWebsocketHandler, BaseWebsocketHandlerFactory, BaseWebsocketHandlerRouter


def start(responder_cls=BaseWebsocketHandler, factory_cls=BaseWebsocketHandlerFactory,
          router_cls=BaseWebsocketHandlerRouter, event_loop=None):
    """
    Starts the websocket listening service with the given optional parameters. The event loop is started on the current
    thread.
    :param responder_cls: the class to find the event handler functions on (optional)
    :param factory_cls: the class to instantiate for the factory object (optional)
    :param router_cls: the class to instantiate for the router object (optional)
    :param event_loop: the event loop to use (optional)
    """
    predicate = lambda m: inspect.isfunction(m) and hasattr(m, 'message_handler') and m.message_handler
    message_handlers = [(func.event_regex, func.original) for _, func in inspect.getmembers(responder_cls, predicate)]
    message_handlers.sort(key=lambda t: t[1].order)
    factory = factory_cls(responder_cls=responder_cls)
    router = router_cls(factory, message_handlers)
    websocket_loop = WebsocketHandlerLoop(router)
    if not event_loop:
        event_loop = asyncio.get_event_loop()
    asyncio.set_event_loop(event_loop)
    websocket_loop.start(event_loop=event_loop)
    event_loop.run_forever()


def start_in_new_thread(event_loop=None, **kwargs):
    """
    Starts the websocket listening service with the given optional parameters on a new thread and then returns that
    thread and the event loop used as a tuple.
    :param responder_cls: the class to find the event handler functions on (optional)
    :param factory_cls: the class to instantiate for the factory object (optional)
    :param router_cls: the class to instantiate for the router object (optional)
    :param event_loop: the event loop to use (optional)
    """
    if not event_loop:
        # we need to make sure the event loop is created in this thread so that we can pass it back
        event_loop = asyncio.get_event_loop()
    kwargs.update({'event_loop': event_loop})
    thread = threading.Thread(target=start, kwargs=kwargs)
    thread.start()
    return thread, event_loop
