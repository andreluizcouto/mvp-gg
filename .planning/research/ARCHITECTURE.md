# Architecture Patterns: MVPApp Desktop GUI Integration

**Domain:** Desktop companion app — GUI overlay onto existing headless tray + asyncio architecture
**Researched:** 2025-07-14
**Confidence:** HIGH (based on direct code analysis + established Python threading patterns)

## Executive Summary

The MVPApp currently runs on two threads: pystray blocks the main thread, and asyncio runs on a daemon thread. Adding CustomTkinter requires resolving a three-way threading conflict — tkinter, pystray, and asyncio all want long-running event loops. The recommended architecture puts CustomTkinter on the main thread (where GUI frameworks are most reliable), moves pystray to a daemon thread (fully supported on Windows via the win32 backend), keeps asyncio on its existing daemon thread, and bridges them with a thread-safe `queue.Queue` polled by tkinter's `after()` scheduler.

## Current Architecture (Before GUI)

```
┌─────────────────────────────────────────────────┐
│                  coach_app.py                    │
│                                                  │
│  Main Thread              Daemon Thread          │
│  ┌──────────┐            ┌──────────────────┐   │
│  │ pystray  │            │ asyncio.run()    │   │
│  │ Icon.run │  ←─state─  │ ┌──────────────┐ │   │
│  │ (blocks) │            │ │ coach_loop() │ │   │
│  └──────────┘            │ │ LiveCoach    │ │   │
│                          │ │ _upload()    │ │   │
│                          │ └──────────────┘ │   │
│                          └──────────────────┘   │
│                                                  │
│  Shared: TrayIcon.set_state() via threading.Lock │
│  Config: app_config.get_config() (file I/O)      │
└─────────────────────────────────────────────────┘
```

**Key constraints discovered in code:**
- `coach_app.py:207` — `tray.run()` blocks main thread
- `coach_app.py:200-205` — asyncio runs on `daemon=True` thread
- `tray_icon.py:56-66` — `set_state()` called from asyncio thread, uses `threading.Lock`
- `live_coach.py:82` — `events_queue: asyncio.Queue` exists but is **never consumed**
- `live_coach.py:440-442` — `_emit()` appends to `event_history` AND puts onto `events_queue`
- `coach.spec:35` — **tkinter is explicitly excluded** from PyInstaller build (`excludes=["tkinter", ...]`)
- `app_config.py` — No thread locks, just file I/O (safe for single-writer pattern)

## Recommended Architecture (With GUI)

```
┌──────────────────────────────────────────────────────────────┐
│                      coach_app.py (restructured)             │
│                                                              │
│  Main Thread          Daemon Thread 1     Daemon Thread 2    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ CustomTkinter│    │ pystray      │    │ asyncio.run()│   │
│  │ CTk.mainloop │    │ Icon.run()   │    │ coach_loop() │   │
│  │              │    │              │    │ LiveCoach    │   │
│  │ ┌──────────┐│    │              │    │ event_bridge │   │
│  │ │ after()  ││    │              │    │              │   │
│  │ │ poll 100 ││    │              │    │              │   │
│  │ │ ms queue ││    │              │    │              │   │
│  │ └────▲─────┘│    └──────┬───────┘    └──────┬───────┘   │
│  └──────┼──────┘           │                    │            │
│         │                  │                    │            │
│         │    ┌─────────────┴────────────────────┘            │
│         │    │                                               │
│         │    ▼                                               │
│     ┌───┴────────────┐                                      │
│     │ queue.Queue    │  Thread-safe stdlib queue             │
│     │ (event_bus)    │  Events + status + show/hide signals  │
│     └────────────────┘                                      │
│                                                              │
│     ┌────────────────┐                                      │
│     │ app_config.json│  Settings persistence (file I/O)     │
│     └────────────────┘                                      │
└──────────────────────────────────────────────────────────────┘
```

### Why This Threading Model

| Thread | Runs | Rationale |
|--------|------|-----------|
| **Main** | CustomTkinter `mainloop()` | GUI frameworks are most reliable on the main thread. tkinter has known issues when run on non-main threads (event handling, window manager integration, DPI awareness). This is the standard recommendation for all tkinter-based apps. |
| **Daemon 1** | pystray `Icon.run()` | pystray on Windows uses the `win32` backend (`pystray._win32`). It creates its own message pump via `win32gui` and works correctly from any thread. Already a proven pattern in the Python ecosystem. Moving it off the main thread is a safe, one-line change. |
| **Daemon 2** | `asyncio.run(coach_loop())` | Unchanged from current architecture. The asyncio loop handles Riot API polling, event detection, upload, and status polling. No reason to modify this. |

**Why NOT other approaches:**

| Alternative | Why Rejected |
|-------------|-------------|
| Keep pystray on main, tkinter on daemon thread | tkinter on non-main thread is fragile on Windows. Event handling, window focus, and DPI awareness can break. Not worth the risk for zero benefit. |
| Replace pystray with tkinter system tray | tkinter has no native system tray support. Would need `win32api` directly or `pywinstyles`. Adds complexity and risk, loses pystray's proven abstraction. |
| Single thread with interleaved event loops | Brittle. Both `mainloop()` and `Icon.run()` expect exclusive control. Manual `root.update()` polling patterns cause lag, missed events, and subtle GUI bugs. |
| Use `Icon.run_detached()` | pystray 0.19.5+ may expose `run_detached()` which spawns its own background thread. If available, this is a valid shortcut. However, manual `threading.Thread(target=icon.run, daemon=True)` is safer (works on all 0.19.x versions, gives explicit control over `daemon=True`). Recommend: **verify `run_detached()` exists at implementation time**; fall back to manual threading if not. |

### Component Boundaries

| Component | File | Status | Responsibility | Thread | Communicates With |
|-----------|------|--------|---------------|--------|-------------------|
| **EventBus** | `event_bus.py` | **NEW** | Thread-safe `queue.Queue` wrapper. Typed messages for events, status changes, show/hide commands | Shared (any thread writes, main thread reads) | All components |
| **GuiWindow** | `gui_window.py` | **NEW** | CustomTkinter window — status, settings, activity log, how-it-works | Main | EventBus (reads), AppConfig (reads/writes) |
| **TrayIcon** | `tray_icon.py` | **MODIFIED** | System tray icon + menu. Adds "Open" item, sends show/hide via EventBus | Daemon 1 | EventBus (writes) |
| **coach_app** | `coach_app.py` | **MODIFIED** | Entry point. Creates 3 threads, wires components, manages shutdown | Main (setup), then GUI mainloop | All components |
| **LiveCoachSession** | `live_coach.py` | **UNCHANGED** | Event detection, minimap capture. Already emits to `events_queue` | Daemon 2 (asyncio) | EventBus (via bridge task in coach_app) |
| **AppConfig** | `app_config.py` | **UNCHANGED** | JSON config persistence | N/A (file I/O) | GuiWindow (caller), MinimapCapture (caller) |
| **MinimapCapture** | `minimap_capture.py` | **UNCHANGED** | Screen capture | Daemon 2 (asyncio) | AppConfig (reads fresh each call) |
| **LiveGameClient** | `live_game_client.py` | **UNCHANGED** | Riot localhost API client | Daemon 2 (asyncio) | LiveCoachSession |

## Data Flow Patterns

### Pattern 1: Activity Log (asyncio → tkinter)

**What:** Game events (deaths, kills, objectives) flow from the asyncio polling loop to the GUI's activity log display.

**How:** An asyncio task bridges from `asyncio.Queue` to `queue.Queue`. Tkinter polls the queue every 100ms using `after()`.

```
LiveCoachSession._emit(event)
    │
    ▼
asyncio.Queue (events_queue)      ← existing, currently unconsumed
    │
    ▼
event_bridge_task (asyncio.Task)   ← NEW: reads asyncio.Queue, writes stdlib queue
    │
    ▼
queue.Queue (event_bus)            ← NEW: thread-safe bridge
    │
    ▼
GuiWindow.after(100, _poll_bus)    ← NEW: tkinter scheduler polls queue
    │
    ▼
Activity log widget updated
```

**Reference implementation:**

```python
# event_bus.py — Thread-safe message bus
import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

class MessageType(Enum):
    GAME_EVENT = auto()      # LiveEvent from asyncio
    STATUS_CHANGE = auto()   # State change (waiting/recording/uploading/ready)
    SHOW_WINDOW = auto()     # Tray requested window show
    HIDE_WINDOW = auto()     # Window minimized to tray
    SHUTDOWN = auto()        # App shutdown signal

@dataclass
class BusMessage:
    type: MessageType
    data: Any = None

class EventBus:
    """Thread-safe message bus using stdlib queue.Queue."""
    def __init__(self):
        self._queue: queue.Queue[BusMessage] = queue.Queue()

    def put(self, msg: BusMessage) -> None:
        """Put message — safe from any thread."""
        self._queue.put_nowait(msg)

    def get_all(self) -> list[BusMessage]:
        """Drain all pending messages — call from consumer thread only."""
        messages = []
        while True:
            try:
                messages.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return messages
```

```python
# Bridge task — runs inside the asyncio event loop (in coach_app.py)
async def event_bridge(session: LiveCoachSession, bus: EventBus):
    """Reads from asyncio.Queue, writes to thread-safe EventBus."""
    while True:
        event = await session.events_queue.get()
        bus.put(BusMessage(
            type=MessageType.GAME_EVENT,
            data=event.to_dict()  # serialize to plain dict for cross-thread safety
        ))
```

```python
# GuiWindow — polls on main thread
class GuiWindow(customtkinter.CTk):
    def __init__(self, bus: EventBus):
        super().__init__()
        self._bus = bus
        self._poll_bus()  # start polling

    def _poll_bus(self):
        """Drain event bus and process messages. Runs every 100ms on main thread."""
        for msg in self._bus.get_all():
            if msg.type == MessageType.GAME_EVENT:
                self._append_to_activity_log(msg.data)
            elif msg.type == MessageType.STATUS_CHANGE:
                self._update_status(msg.data)
            elif msg.type == MessageType.SHOW_WINDOW:
                self.deiconify()
                self.lift()
                self.focus_force()
            elif msg.type == MessageType.SHUTDOWN:
                self.destroy()
                return
        self.after(100, self._poll_bus)  # re-schedule
```

**Why 100ms poll interval:** Fast enough to feel real-time for activity log updates (game events happen at most every few seconds). Low enough CPU overhead that it's negligible. tkinter's `after()` is the standard, safe way to schedule work on the main thread from external sources.

### Pattern 2: Status Updates (asyncio → tray + GUI)

**What:** The coach loop changes state (waiting → recording → uploading → ready). Both tray icon AND GUI need to update.

**Current:** `coach_loop()` calls `tray.set_state("recording")` directly — cross-thread call protected by `threading.Lock`.

**Recommended change:** Keep the direct `tray.set_state()` call (it works, is lock-protected, and tray updates should be immediate). ADD a bus message so the GUI also updates.

```python
# In coach_loop() — after existing tray.set_state() call
tray.set_state("recording", detail=champion)
bus.put(BusMessage(type=MessageType.STATUS_CHANGE, data={"state": "recording", "detail": champion}))
```

This is additive — does not break existing tray behavior. Tray updates immediately (same thread safety as before). GUI updates within 100ms via bus poll.

### Pattern 3: Show/Hide Window (tray ↔ tkinter)

**What:** User clicks tray icon "Open" menu item → window appears. User clicks window close (X) → window hides, app stays in tray.

**Tray → Window (show):**
```python
# In TrayIcon — menu callback runs on pystray's thread
def _show_window(self, icon, item):
    self._bus.put(BusMessage(type=MessageType.SHOW_WINDOW))
```
GuiWindow's `_poll_bus()` picks this up within 100ms and calls `self.deiconify()` on the main thread. **Never call tkinter methods directly from the pystray thread.**

**Window → Tray (hide on close):**
```python
# In GuiWindow.__init__
self.protocol("WM_DELETE_WINDOW", self._on_close)

def _on_close(self):
    """Hide instead of destroy — app lives on in tray."""
    self.withdraw()
```

This runs on the main thread already — no cross-thread concern.

**pystray double-click to open:**
```python
# In TrayIcon._build_menu() — make "Open" the default (double-click) action
pystray.MenuItem("Open MVPApp", self._show_window, default=True),
```

### Pattern 4: Settings Changes (GUI → config → capture)

**What:** User toggles minimap position or size in the GUI. Change must affect the next minimap capture.

**Current flow (already works via tray menu):**
```
User toggles setting in tray menu
    → save_config(cfg)                     # writes config.json
    → (next event) _capture_and_save()
        → get_config()                     # reads config.json fresh each time
        → capture_minimap(..., cfg values)
```

**New flow (same pattern, different trigger):**
```
User toggles setting in GUI
    → save_config(cfg)                     # writes config.json — same function
    → (next event) _capture_and_save()     # reads fresh config — no change needed
        → get_config()
        → capture_minimap(..., cfg values)
```

**No cross-thread notification needed.** The capture code in `live_coach.py:428-437` already reads config fresh on every event via `get_config()`. Settings changes take effect on the next capture automatically. This is a clean design that requires **zero modification** to `minimap_capture.py` or the config-reading path in `live_coach.py`.

## Restructured Entry Point

```python
# coach_app.py — new main() structure
def main() -> None:
    stop_event = threading.Event()
    bus = EventBus()

    def on_quit():
        logger.info("Shutting down MVPApp...")
        stop_event.set()
        bus.put(BusMessage(type=MessageType.SHUTDOWN))

    # Create components (all on main thread before starting anything)
    tray = TrayIcon(on_quit=on_quit, bus=bus)
    window = GuiWindow(bus=bus)

    # Daemon thread 1: pystray
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # Daemon thread 2: asyncio (coach loop + event bridge)
    async_thread = threading.Thread(
        target=_run_async_loop,
        args=(tray, bus, stop_event),
        daemon=True,
    )
    async_thread.start()

    # Main thread: CustomTkinter (blocks until window.destroy())
    window.mainloop()

    # Cleanup after mainloop returns
    on_quit()  # ensure stop_event is set even if window closed unexpectedly
    tray.stop()
    async_thread.join(timeout=5.0)
    logger.info("MVPApp shut down.")
```

**Key change from current code:** `tray.run()` moves from main thread to daemon thread. `window.mainloop()` takes the main thread. The asyncio thread is unchanged but now also runs the `event_bridge` task.

```python
# Updated _run_async_loop
async def _async_main(tray, bus, stop_event):
    session_holder = [None]  # mutable holder for bridge access

    async def coach_loop_with_bus():
        # Same as existing coach_loop but also puts status messages on bus
        ...

    async def bridge_loop():
        while not stop_event.is_set():
            if session_holder[0] and session_holder[0].events_queue:
                try:
                    event = await asyncio.wait_for(
                        session_holder[0].events_queue.get(), timeout=1.0
                    )
                    bus.put(BusMessage(type=MessageType.GAME_EVENT, data=event.to_dict()))
                except asyncio.TimeoutError:
                    continue
            else:
                await asyncio.sleep(1.0)

    await asyncio.gather(coach_loop_with_bus(), bridge_loop())
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Calling tkinter from pystray thread
**What:** Directly calling `window.deiconify()`, `window.title()`, or any widget method from a pystray menu callback.
**Why bad:** tkinter is not thread-safe. This causes random crashes, frozen windows, or silent corruption — often only under specific timing, making it impossible to debug.
**Instead:** Put a message on the EventBus. Let tkinter's `after()` poll pick it up and execute on the main thread.

### Anti-Pattern 2: Using `root.update()` loop instead of `mainloop()`
**What:** Running `while True: root.update(); root.update_idletasks()` to manually pump tkinter events.
**Why bad:** Fragile, burns CPU, misses events, breaks window manager integration (minimize, focus, DPI).
**Instead:** Use `mainloop()` for the main loop and `after()` for all scheduled work. This is what tkinter is designed for.

### Anti-Pattern 3: Sharing mutable LiveEvent objects across threads
**What:** Passing the `LiveEvent` dataclass object directly through `queue.Queue` to the tkinter thread.
**Why bad:** The `LiveEvent` has mutable fields (`assisters` list, optional `minimap_path`). If the asyncio side modifies it after queuing (unlikely but possible in edge cases with `create_task`), the GUI sees inconsistent data.
**Instead:** Serialize to dict via `event.to_dict()` before putting on the bus. Plain dicts of strings are inherently safe across threads.

### Anti-Pattern 4: Storing unlimited activity log entries
**What:** Appending every event forever to the activity log widget.
**Why bad:** Over a long session with many games, memory grows unbounded. The `CTkTextbox` widget will also slow down rendering with thousands of lines.
**Instead:** Cap the activity log at ~500 entries. Drop oldest when the limit is hit. This is a local-only, ephemeral display.

### Anti-Pattern 5: Creating tkinter window before starting mainloop
**What:** Calling `GuiWindow()` constructor and immediately interacting with widgets before `mainloop()` is running.
**Why bad:** Some widget operations (like geometry calculations, DPI-aware sizing) need the event loop running.
**Instead:** Create the window, start background threads, then immediately call `window.mainloop()`. Use `after(0, ...)` for any post-init setup that needs the event loop.

## Shutdown Sequence

Shutdown must be clean to avoid orphan threads or frozen windows.

```
User clicks "Sair"/"Quit" in tray menu
    │
    ▼
on_quit() called [from pystray thread]
    ├── stop_event.set()              → asyncio loop exits coach_loop()
    ├── bus.put(SHUTDOWN)             → tkinter _poll_bus sees SHUTDOWN → window.destroy()
    └── tray.stop()                   → pystray message loop exits
         │
         ▼
    window.mainloop() returns         → main thread unblocks
    on_quit() called again (idempotent) → stop_event already set
    async_thread.join(timeout=5)      → wait for asyncio cleanup
    Process exits (daemon threads killed automatically)
```

**Alternative shutdown path — user closes window while wanting to fully quit:**
Could add a "Quit" button in the GUI that calls `on_quit()` → same flow. The default window close (X) should HIDE, not quit. Only explicit "Quit" from tray or GUI kills the app.

**Key detail:** `daemon=True` on both background threads ensures the process exits even if a thread hangs. The `join(timeout=5)` gives asyncio a grace period but doesn't block forever.

## Build Configuration Changes (coach.spec)

The current `coach.spec` **explicitly excludes tkinter** (line 35). This must change:

```python
# BEFORE (current):
excludes=["tkinter", "matplotlib", "numpy", "scipy"],

# AFTER (required):
excludes=["matplotlib", "numpy", "scipy"],  # REMOVE "tkinter"
```

Additional changes:
```python
datas=[
    ("config.json", "."),
    # CustomTkinter ships JSON theme files + assets that must be bundled
    # Use the actual install path at build time:
    (customtkinter_path, "customtkinter/"),
],
hiddenimports=[
    # ... existing entries ...
    "customtkinter",
    "customtkinter._widgets",
    "tkinter",
    "tkinter.ttk",
    "event_bus",
    "gui_window",
],
```

**CustomTkinter asset bundling** is the most commonly reported PyInstaller issue with CustomTkinter. The library needs its `assets/` and `json/` theme directories at runtime. The standard solution is to include the entire `customtkinter` package directory in `datas`.

## Build Order (Dependency-Respecting)

```
Step 1: event_bus.py (NEW)
   └── No dependencies. Foundation for all cross-thread communication.
   └── Can be unit tested in isolation.

Step 2: gui_window.py — basic window shell (NEW)
   └── Depends on: event_bus.py, customtkinter (pip install)
   └── Build: window frame, hide-on-close, bus polling skeleton.
   └── No activity log yet, no settings — just the window that shows/hides.

Step 3: coach_app.py — threading refactor (MODIFY)
   └── Depends on: event_bus.py, gui_window.py (basic)
   └── Build: 3-thread model, wire bus, verify startup/shutdown.
   └── This is the highest-risk step — test carefully.

Step 4: tray_icon.py — integration (MODIFY)
   └── Depends on: event_bus.py, coach_app.py refactor
   └── Build: "Open MVPApp" menu item (default=True), show/hide via bus.
   └── Keep existing settings items in tray menu for quick access.

Step 5: gui_window.py — "How it works" + status display (EXTEND)
   └── Depends on: Steps 2-3 working
   └── Build: Static explanation frame, status bar consuming STATUS_CHANGE messages.

Step 6: gui_window.py — settings panel (EXTEND)
   └── Depends on: Step 5, app_config.py (unchanged)
   └── Build: Minimap position toggle, size toggle with "Recommended for AI" label.

Step 7: gui_window.py — activity log + event bridge (EXTEND)
   └── Depends on: event_bus.py, Steps 2-3, LiveCoachSession.events_queue
   └── Build: CTkTextbox log, event_bridge async task, color coding per event type.
   └── This is the showcase feature.

Step 8: coach.spec — build config (MODIFY)
   └── Depends on: all above working
   └── Build: Remove tkinter exclusion, add customtkinter hiddenimports + datas.
   └── Test PyInstaller build on clean machine.
```

## Sources

- **Direct code analysis** (HIGH confidence): `coach_app.py`, `tray_icon.py`, `live_coach.py`, `minimap_capture.py`, `app_config.py`, `live_game_client.py`, `coach.spec`, `build.bat`
- **Python `threading` module** (HIGH confidence): `queue.Queue` thread safety is guaranteed by the CPython implementation and documented in stdlib docs
- **tkinter documentation** (HIGH confidence): `after()` scheduling, main thread requirement, `WM_DELETE_WINDOW` protocol, `withdraw()`/`deiconify()` for show/hide
- **pystray API** (HIGH confidence): `Icon.run()` blocking behavior, win32 backend threading compatibility, `MenuItem(default=True)` for double-click
- **CustomTkinter** (HIGH confidence): Subclass of `tkinter.Tk` (`CTk`), inherits all tkinter threading constraints, ships with JSON theme assets that need PyInstaller bundling
- **PyInstaller** (HIGH confidence): `excludes`, `hiddenimports`, `datas` configuration for CustomTkinter bundling — well-documented issue in CustomTkinter community

---
*Research completed: 2025-07-14 — v1.1 MVPApp Desktop GUI milestone*
