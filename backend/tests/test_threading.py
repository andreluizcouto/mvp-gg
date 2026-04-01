# backend/tests/test_threading.py
"""
Integration tests for 3-thread model: EventBus + tkinter mainloop + threading.
Validates cross-thread event delivery, latency, and shutdown coordination.
"""
import os
import sys
import threading
import time
import tkinter as tk

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from event_bus import EventBus, EventType, Event


@pytest.fixture(scope="module")
def _tk_root():
    """Single Tk root shared across all tests (avoids Tcl state corruption on Windows)."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.fixture()
def tk_root(_tk_root):
    """Per-test wrapper that resets the shared root for reuse."""
    return _tk_root


def test_eventbus_polling_with_tk_mainloop(tk_root):
    """EventBus delivers events via after() polling on the tk mainloop."""
    received = []

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, lambda e: received.append(e))
    event_bus.start_polling(tk_root)

    # Emit from main thread after a short delay
    tk_root.after(50, lambda: event_bus.emit(
        Event(EventType.STATE_CHANGE, {"state": "waiting"})
    ))
    # Safety timeout to exit mainloop
    tk_root.after(500, tk_root.quit)

    tk_root.mainloop()

    assert len(received) == 1
    assert received[0].data["state"] == "waiting"


def test_cross_thread_emit_to_tk_mainloop(tk_root):
    """Events emitted from a background thread are delivered on the main thread."""
    received = []
    delivery_thread_ids = []

    main_thread_id = threading.current_thread().ident

    def handler(event):
        received.append(event)
        delivery_thread_ids.append(threading.current_thread().ident)

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, handler)
    event_bus.start_polling(tk_root)

    def background_emit():
        time.sleep(0.05)
        event_bus.emit(Event(EventType.STATE_CHANGE, {
            "state": "recording", "champion": "Jinx"
        }))

    t = threading.Thread(target=background_emit, daemon=True)
    t.start()

    # Safety timeout
    tk_root.after(500, tk_root.quit)
    tk_root.mainloop()

    assert len(received) == 1
    assert received[0].data["state"] == "recording"
    assert received[0].data["champion"] == "Jinx"
    # Handler runs on main thread (via after() polling)
    assert delivery_thread_ids[0] == main_thread_id


def test_eventbus_delivery_latency(tk_root):
    """Cross-thread event delivery completes within 200ms (APP-02 requirement)."""
    timestamps = {}

    def handler(event):
        timestamps["received"] = time.perf_counter()

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, handler)
    event_bus.start_polling(tk_root)

    def background_emit():
        time.sleep(0.05)  # Let mainloop start
        timestamps["emitted"] = time.perf_counter()
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "uploading"}))

    t = threading.Thread(target=background_emit, daemon=True)
    t.start()

    # Safety timeout
    tk_root.after(500, tk_root.quit)
    tk_root.mainloop()

    assert "emitted" in timestamps, "Event was never emitted"
    assert "received" in timestamps, "Event was never received"
    latency = timestamps["received"] - timestamps["emitted"]
    assert latency < 0.200, f"Latency {latency:.3f}s exceeds 200ms requirement"


def test_shutdown_via_stop_event(tk_root):
    """Shutdown via stop_event + after(0, quit) exits mainloop cleanly."""
    stop_event = threading.Event()

    def on_quit():
        stop_event.set()
        tk_root.after(0, tk_root.quit)

    def background_trigger():
        time.sleep(0.1)
        on_quit()

    t = threading.Thread(target=background_trigger, daemon=True)
    t.start()

    start = time.perf_counter()
    tk_root.mainloop()
    elapsed = time.perf_counter() - start

    assert stop_event.is_set(), "stop_event was not set"
    assert elapsed < 2.0, f"Mainloop took {elapsed:.1f}s to exit (should be < 2s)"


def test_multiple_events_from_async_thread(tk_root):
    """Multiple events of different types are delivered in order."""
    received = []

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, lambda e: received.append(e))
    event_bus.subscribe(EventType.ERROR, lambda e: received.append(e))
    event_bus.start_polling(tk_root)

    def background_emit():
        time.sleep(0.05)
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "waiting"}))
        event_bus.emit(Event(EventType.ERROR, {"message": "test error"}))
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "recording"}))

    t = threading.Thread(target=background_emit, daemon=True)
    t.start()

    # Safety timeout
    tk_root.after(500, tk_root.quit)
    tk_root.mainloop()

    assert len(received) == 3, f"Expected 3 events, got {len(received)}"
    assert received[0].type == EventType.STATE_CHANGE
    assert received[0].data["state"] == "waiting"
    assert received[1].type == EventType.ERROR
    assert received[1].data["message"] == "test error"
    assert received[2].type == EventType.STATE_CHANGE
    assert received[2].data["state"] == "recording"
