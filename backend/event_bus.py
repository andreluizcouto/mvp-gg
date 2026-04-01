# backend/event_bus.py
"""
EventBus — thread-safe cross-thread communication via queue.Queue + after() polling.

Any thread can call emit(). The main (tkinter) thread drains the queue via _poll(),
which is re-scheduled every POLL_INTERVAL_MS milliseconds using app.after().
"""
import logging
import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Discriminator for EventBus messages."""
    STATE_CHANGE = auto()    # App state transitions (waiting/recording/uploading/ready)
    CONFIG_CHANGED = auto()  # Config was modified
    GAME_EVENT = auto()      # Live game event (death, kill, objective)
    LOG_MESSAGE = auto()     # Activity log entry
    ERROR = auto()           # Error occurred
    SHUTDOWN = auto()        # Shutdown requested


@dataclass
class Event:
    """Payload carried through the EventBus."""
    type: EventType
    data: Any = None


class EventBus:
    """Thread-safe event bus: any thread can put(), main thread polls via after()."""

    POLL_INTERVAL_MS = 100  # 100ms — well within 200ms requirement

    def __init__(self) -> None:
        self._queue: queue.Queue[Event] = queue.Queue()
        self._handlers: dict[EventType, list[Callable]] = {}
        self._app = None

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Register a handler for an event type. Call from main thread during setup."""
        self._handlers.setdefault(event_type, []).append(handler)

    def emit(self, event: Event) -> None:
        """Put an event on the queue. Thread-safe — callable from ANY thread."""
        self._queue.put(event)

    def start_polling(self, app) -> None:
        """Begin after()-based polling on the main thread."""
        self._app = app
        self._poll()

    def _poll(self) -> None:
        """Drain the queue and dispatch to handlers. Runs on main thread."""
        try:
            while True:
                event = self._queue.get_nowait()
                handlers = self._handlers.get(event.type, [])
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception:
                        logger.exception("EventBus handler error for %s", event.type)
        except queue.Empty:
            pass
        # Re-schedule on the tkinter main loop (only when app is connected)
        if self._app:
            self._app.after(self.POLL_INTERVAL_MS, self._poll)
