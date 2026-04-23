import inspect
from collections import defaultdict
from typing import Any, Callable


EventHandler = Callable[[dict], Any]


class EventBus:
    """Minimal async-capable event bus for downstream handler attachment."""

    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._subscribers[event_name].append(handler)

    async def emit(self, event_name: str, payload: dict) -> None:
        for handler in self._subscribers.get(event_name, []):
            result = handler(payload)
            if inspect.isawaitable(result):
                await result
