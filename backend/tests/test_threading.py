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


def test_eventbus_polling_with_tk_mainloop():
    """EventBus delivers events via after() polling on the tk mainloop."""
    root = tk.Tk()
    root.withdraw()
    received = []

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, lambda e: received.append(e))
    event_bus.start_polling(root)

    # Emit from main thread after a short delay
    root.after(50, lambda: event_bus.emit(
        Event(EventType.STATE_CHANGE, {"state": "waiting"})
    ))
    # Safety timeout to exit mainloop
    root.after(500, root.quit)

    root.mainloop()

    try:
        assert len(received) == 1
        assert received[0].data["state"] == "waiting"
    finally:
        root.destroy()


def test_cross_thread_emit_to_tk_mainloop():
    """Events emitted from a background thread are delivered on the main thread."""
    root = tk.Tk()
    root.withdraw()
    received = []
    delivery_thread_ids = []

    main_thread_id = threading.current_thread().ident

    def handler(event):
        received.append(event)
        delivery_thread_ids.append(threading.current_thread().ident)

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, handler)
    event_bus.start_polling(root)

    def background_emit():
        time.sleep(0.05)
        event_bus.emit(Event(EventType.STATE_CHANGE, {
            "state": "recording", "champion": "Jinx"
        }))

    t = threading.Thread(target=background_emit, daemon=True)
    t.start()

    # Safety timeout
    root.after(500, root.quit)
    root.mainloop()

    try:
        assert len(received) == 1
        assert received[0].data["state"] == "recording"
        assert received[0].data["champion"] == "Jinx"
        # Handler runs on main thread (via after() polling)
        assert delivery_thread_ids[0] == main_thread_id
    finally:
        root.destroy()


def test_eventbus_delivery_latency():
    """Cross-thread event delivery completes within 200ms (APP-02 requirement)."""
    root = tk.Tk()
    root.withdraw()
    timestamps = {}

    def handler(event):
        timestamps["received"] = time.perf_counter()

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, handler)
    event_bus.start_polling(root)

    def background_emit():
        time.sleep(0.05)  # Let mainloop start
        timestamps["emitted"] = time.perf_counter()
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "uploading"}))

    t = threading.Thread(target=background_emit, daemon=True)
    t.start()

    # Safety timeout
    root.after(500, root.quit)
    root.mainloop()

    try:
        assert "emitted" in timestamps, "Event was never emitted"
        assert "received" in timestamps, "Event was never received"
        latency = timestamps["received"] - timestamps["emitted"]
        assert latency < 0.200, f"Latency {latency:.3f}s exceeds 200ms requirement"
    finally:
        root.destroy()


def test_shutdown_via_stop_event():
    """Shutdown via stop_event + after(0, quit) exits mainloop cleanly."""
    root = tk.Tk()
    root.withdraw()
    stop_event = threading.Event()

    def on_quit():
        stop_event.set()
        root.after(0, root.quit)

    def background_trigger():
        time.sleep(0.1)
        on_quit()

    t = threading.Thread(target=background_trigger, daemon=True)
    t.start()

    start = time.perf_counter()
    root.mainloop()
    elapsed = time.perf_counter() - start

    try:
        assert stop_event.is_set(), "stop_event was not set"
        assert elapsed < 2.0, f"Mainloop took {elapsed:.1f}s to exit (should be < 2s)"
    finally:
        root.destroy()


def test_multiple_events_from_async_thread():
    """Multiple events of different types are delivered in order."""
    root = tk.Tk()
    root.withdraw()
    received = []

    event_bus = EventBus()
    event_bus.subscribe(EventType.STATE_CHANGE, lambda e: received.append(e))
    event_bus.subscribe(EventType.ERROR, lambda e: received.append(e))
    event_bus.start_polling(root)

    def background_emit():
        time.sleep(0.05)
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "waiting"}))
        event_bus.emit(Event(EventType.ERROR, {"message": "test error"}))
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "recording"}))

    t = threading.Thread(target=background_emit, daemon=True)
    t.start()

    # Safety timeout
    root.after(500, root.quit)
    root.mainloop()

    try:
        assert len(received) == 3, f"Expected 3 events, got {len(received)}"
        assert received[0].type == EventType.STATE_CHANGE
        assert received[0].data["state"] == "waiting"
        assert received[1].type == EventType.ERROR
        assert received[1].data["message"] == "test error"
        assert received[2].type == EventType.STATE_CHANGE
        assert received[2].data["state"] == "recording"
    finally:
        root.destroy()
