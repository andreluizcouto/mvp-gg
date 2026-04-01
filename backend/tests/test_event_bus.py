# backend/tests/test_event_bus.py
"""Unit tests for the EventBus cross-thread communication module."""
import os
import sys
import threading

import pytest

# Ensure backend/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from event_bus import EventBus, EventType, Event


# ---------------------------------------------------------------------------
# Test 1: emit + subscribe basic flow
# ---------------------------------------------------------------------------
def test_emit_and_subscribe():
    """Subscribe handler to STATE_CHANGE, emit event, handler receives it."""
    bus = EventBus()
    received = []

    bus.subscribe(EventType.STATE_CHANGE, lambda e: received.append(e))
    event = Event(type=EventType.STATE_CHANGE, data={"state": "waiting"})
    bus.emit(event)
    bus._poll()

    assert len(received) == 1
    assert received[0].type is EventType.STATE_CHANGE
    assert received[0].data == {"state": "waiting"}


# ---------------------------------------------------------------------------
# Test 2: multiple subscribers for the same event type
# ---------------------------------------------------------------------------
def test_multiple_subscribers():
    """Two handlers subscribed to same EventType both receive the event."""
    bus = EventBus()
    results_a = []
    results_b = []

    bus.subscribe(EventType.CONFIG_CHANGED, lambda e: results_a.append(e))
    bus.subscribe(EventType.CONFIG_CHANGED, lambda e: results_b.append(e))

    event = Event(type=EventType.CONFIG_CHANGED, data="new_value")
    bus.emit(event)
    bus._poll()

    assert len(results_a) == 1
    assert len(results_b) == 1
    assert results_a[0] is results_b[0] is event


# ---------------------------------------------------------------------------
# Test 3: emitting with no subscribers does not raise
# ---------------------------------------------------------------------------
def test_unhandled_event_type():
    """Emitting an event with no subscribers does not raise."""
    bus = EventBus()
    event = Event(type=EventType.GAME_EVENT, data={"kill": True})
    bus.emit(event)
    bus._poll()  # should silently drain without error


# ---------------------------------------------------------------------------
# Test 4: cross-thread emit
# ---------------------------------------------------------------------------
def test_cross_thread_emit():
    """Emit from a background thread, _poll() on main thread delivers it."""
    bus = EventBus()
    received = []

    bus.subscribe(EventType.LOG_MESSAGE, lambda e: received.append(e))

    event = Event(type=EventType.LOG_MESSAGE, data="hello from bg")
    t = threading.Thread(target=lambda: bus.emit(event))
    t.start()
    t.join()

    bus._poll()

    assert len(received) == 1
    assert received[0].data == "hello from bg"


# ---------------------------------------------------------------------------
# Test 5: handler exception isolation
# ---------------------------------------------------------------------------
def test_handler_exception_isolation():
    """A handler that raises does not prevent other handlers from running."""
    bus = EventBus()
    results = []

    def bad_handler(e):
        raise RuntimeError("boom")

    def good_handler(e):
        results.append(e)

    bus.subscribe(EventType.ERROR, bad_handler)
    bus.subscribe(EventType.ERROR, good_handler)

    event = Event(type=EventType.ERROR, data="test_error")
    bus.emit(event)
    bus._poll()

    # good_handler must still receive the event despite bad_handler raising
    assert len(results) == 1
    assert results[0].data == "test_error"


# ---------------------------------------------------------------------------
# Test 6: _poll drains multiple events in a single call
# ---------------------------------------------------------------------------
def test_poll_drains_multiple():
    """Single _poll() call dispatches all queued events."""
    bus = EventBus()
    received = []

    bus.subscribe(EventType.STATE_CHANGE, lambda e: received.append(e))

    for i in range(3):
        bus.emit(Event(type=EventType.STATE_CHANGE, data=i))

    bus._poll()

    assert len(received) == 3
    assert [e.data for e in received] == [0, 1, 2]
