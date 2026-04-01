# Domain Pitfalls: Adding CustomTkinter GUI to CoachApp

**Domain:** Desktop GUI integration into existing headless Python app (pystray + asyncio + mss)
**Researched:** 2025-07-10
**Overall confidence:** HIGH — based on direct code analysis + well-documented tkinter/threading constraints

---

## Critical Pitfalls

Mistakes that cause crashes, data corruption, or architectural rewrites.

---

### Pitfall 1: Main Thread War — pystray.Icon.run() vs CustomTkinter.mainloop()

**What goes wrong:** Both `pystray.Icon.run()` and CustomTkinter's `CTk.mainloop()` are blocking calls that expect to own the main thread. The current `coach_app.py` gives main thread to pystray (line 207: `tray.run()`). If you naively add `CTk.mainloop()` alongside it, one of them doesn't get the main thread and either crashes or hangs silently.

**Why it happens:** On Windows, tkinter's mainloop runs a Tcl/Tk event loop that processes Win32 messages. It strongly prefers the main thread — while it *can* technically run on a non-main thread on Windows (unlike macOS where it's a hard crash), doing so leads to subtle instabilities: phantom focus events, unresponsive widgets, random freezes under DPI changes. pystray's `_win32` backend also creates a hidden window with its own message pump, but it's lighter-weight and tolerates background threads well.

**Consequences:**
- If CustomTkinter runs on a non-main thread: intermittent freezes, widgets stop responding to clicks, window becomes unresponsive after system sleep/wake.
- If pystray runs on main thread (current behavior): no room for CustomTkinter.
- If both compete: deadlocks in the Win32 message pump.

**Prevention:** Invert the current threading model:
- **Main thread → CustomTkinter** (`CTk.mainloop()`)
- **Background thread → pystray** (`Icon.run()` in a daemon thread)
- **Background daemon thread → asyncio** (keep current `_run_async_loop`)

pystray on Windows uses the `_win32` backend which creates its own hidden `HWND` and message loop via `Shell_NotifyIcon`. This works reliably from a background thread on Windows because it manages its own independent message pump.

```python
# NEW architecture (coach_app.py main())
def main():
    stop_event = threading.Event()
    app = CoachGUI(stop_event)  # CustomTkinter window

    # pystray in background thread (works on Windows _win32 backend)
    tray = TrayIcon(on_quit=lambda: app.request_shutdown())
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # asyncio in background daemon thread (unchanged)
    async_thread = threading.Thread(
        target=_run_async_loop, args=(tray, app, stop_event), daemon=True
    )
    async_thread.start()

    app.mainloop()  # Blocks main thread — this is correct
```

**Detection:** If the GUI window becomes unresponsive to clicks but the process is still running, main thread ownership is wrong. Test: open GUI → switch to another app → switch back. If the GUI fails to regain focus or paint, tkinter isn't on main thread.

**Confidence:** HIGH — tkinter main-thread requirement is extensively documented in CPython source and Tcl/Tk docs. pystray `_win32` backend thread-safety confirmed by pystray source code using `ctypes.windll.shell32` calls that are apartment-threaded COM.

---

### Pitfall 2: Cross-Thread GUI Updates from asyncio — Tkinter Is Not Thread-Safe

**What goes wrong:** The asyncio event loop runs on a daemon thread (line 200-204, coach_app.py). When `coach_loop` changes state (waiting → recording → uploading → ready), it currently calls `tray.set_state()` which is thread-safe (uses `self._lock`). But if you add GUI widget updates the same way — e.g., `self.status_label.configure(text="Recording...")` — from the asyncio thread, tkinter will corrupt its internal state. Crashes range from segfaults to `TclError: out of stack space` to silent widget corruption.

**Why it happens:** Tkinter's Tcl interpreter is single-threaded. All widget operations MUST happen on the thread that created the `Tk()` root window (the main thread). There's no internal locking — calling widget methods from another thread races against the event loop's own operations.

**Consequences:**
- Random `RuntimeError: main thread is not in main loop` (most common)
- `TclError: out of stack space` under heavy updates
- Silent widget corruption: labels show stale text, progress bars freeze
- Segfaults in the Tcl interpreter (rare but devastating — no error message, just process death)

**Prevention:** Use `root.after()` or a thread-safe queue to marshal updates to the main thread:

```python
class CoachGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self._update_queue = queue.Queue()
        self._poll_updates()  # Start polling

    def _poll_updates(self):
        """Check for pending updates every 100ms — runs on main thread."""
        while not self._update_queue.empty():
            try:
                callback = self._update_queue.get_nowait()
                callback()  # Safe: runs on main thread
            except queue.Empty:
                break
        self.after(100, self._poll_updates)  # Re-schedule

    def update_status(self, state: str, detail: str = ""):
        """Thread-safe: can be called from asyncio thread."""
        self._update_queue.put(lambda: self._do_update_status(state, detail))

    def _do_update_status(self, state: str, detail: str):
        """Actual widget update — only called on main thread."""
        self.status_label.configure(text=f"{state}: {detail}")
```

**Do NOT use:** `threading.Lock` around widget calls — this doesn't help because tkinter's Tcl interpreter has its own internal state machine that isn't protected by your lock. The issue isn't concurrent writes to a variable; it's calling Tcl commands from the wrong thread.

**Detection:** Run with `PYTHONFAULTHANDLER=1` environment variable. Any segfault from Tcl will produce a traceback. Also: if your GUI randomly freezes while the tray icon keeps working, cross-thread widget access is the cause.

**Confidence:** HIGH — this is the single most common tkinter threading bug, documented in CPython docs and every tkinter tutorial.

---

### Pitfall 3: PyInstaller Spec Explicitly Excludes tkinter

**What goes wrong:** The current `coach.spec` (line 35) has `excludes=["tkinter", "matplotlib", "numpy", "scipy"]`. This was intentional — the tray-only app didn't need tkinter, and excluding it saved ~15MB from the bundle. If you add CustomTkinter as a dependency but forget to remove `tkinter` from the excludes list, PyInstaller will happily build — then crash at runtime with `ModuleNotFoundError: No module named '_tkinter'`.

**Why it happens:** CustomTkinter is a pure-Python wrapper around tkinter. It imports `tkinter` internally. PyInstaller's excludes list is processed after dependency analysis, so it actively strips `_tkinter.pyd` and the Tcl/Tk runtime even though CustomTkinter pulled them in.

**Consequences:** The built `.exe` launches, pystray works, asyncio starts — then the moment any code imports `customtkinter`, the app crashes with no visible error (because `console=False` in the spec). Users see the app start and immediately die.

**Prevention:** Three changes to `coach.spec`:

1. **Remove `tkinter` from excludes:**
   ```python
   excludes=["matplotlib", "numpy", "scipy"],  # tkinter REMOVED
   ```

2. **Add CustomTkinter assets to datas:**
   ```python
   import customtkinter
   ctk_path = os.path.dirname(customtkinter.__file__)

   datas=[
       ("config.json", "."),
       (ctk_path, "customtkinter"),  # Themes, JSON, images
   ],
   ```

3. **Add hidden imports:**
   ```python
   hiddenimports=[
       # ... existing ...
       "customtkinter",
       "tkinter",
       "tkinter.filedialog",  # if used
   ],
   ```

**Detection:** Always test the built `.exe` before release, not just `python coach_app.py`. The dev environment has tkinter installed globally; the PyInstaller bundle does not unless explicitly included.

**Confidence:** HIGH — verified by reading the current spec file directly.

---

### Pitfall 4: CustomTkinter Theme/Asset Files Missing in PyInstaller Bundle

**What goes wrong:** CustomTkinter ships with JSON theme files (`blue.json`, `dark-blue.json`, etc.), font files, and image assets inside its package directory. PyInstaller's default analysis doesn't collect these non-Python files. The app builds and launches, but CustomTkinter falls back to ugly default tkinter appearance, or crashes with `FileNotFoundError` when trying to load themes.

**Why it happens:** PyInstaller follows Python imports, not file-system reads. CustomTkinter loads its themes via `open(os.path.join(package_dir, "assets", ...))` — these are runtime file reads, not imports. PyInstaller can't detect them.

**Consequences:**
- `FileNotFoundError` when CustomTkinter tries to load theme JSON
- Widgets render with default tkinter gray-box appearance (ugly, defeats the purpose of using CTk)
- Dark mode doesn't work
- Custom fonts missing

**Prevention:** Bundle the entire `customtkinter` package directory as data:

```python
import customtkinter
import os
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ...
    datas=[
        ("config.json", "."),
        (ctk_path, "customtkinter"),  # ALL assets
    ],
    ...
)
```

At runtime, CustomTkinter finds its assets via `__file__` resolution. In a PyInstaller bundle, `customtkinter.__file__` resolves inside `_MEIPASS` (one-file) or the dist directory (one-dir). The `datas` entry above places the files where CustomTkinter expects them.

**Verify after build:** Check that `dist/CoachApp/customtkinter/assets/themes/` contains JSON theme files.

**Detection:** If the GUI window appears but looks like plain gray tkinter widgets instead of modern CustomTkinter styling, assets are missing.

**Confidence:** HIGH — CustomTkinter's own docs note this requirement for PyInstaller bundling.

---

### Pitfall 5: config.json Race Condition — Three Writers, No Locking

**What goes wrong:** `config.json` is currently read and written without any synchronization. The current code has two access points:
1. **Tray icon callbacks** (pystray's callback thread): `_toggle_left` and `_toggle_large` in `tray_icon.py` lines 117-123 do `get_config()` → modify → `save_config()` — a read-modify-write without any lock.
2. **Asyncio thread**: `_capture_and_save()` in `live_coach.py` line 429-430 calls `get_config()` to read capture settings.

Adding a GUI settings panel creates a **third** writer on the main thread. Three threads doing unsynchronized read-modify-write on the same JSON file leads to:
- Lost writes (Thread A reads, Thread B reads, Thread A writes, Thread B writes — Thread A's changes are lost)
- Corrupted JSON (partial write from Thread A, Thread B reads truncated file)
- `json.JSONDecodeError` crashes during capture (asyncio thread reads corrupt JSON)

**Why it happens:** `app_config.py` has zero thread-safety mechanisms. `save_config` opens the file, writes, and closes. If two threads call `save_config` simultaneously, one write can truncate the file while the other is reading.

**Consequences:**
- Minimap captures use wrong settings after user changes config in GUI
- Config file becomes empty or contains partial JSON → `get_config` returns defaults silently (current code catches `JSONDecodeError`)
- User's setting changes appear to not save (overwritten by stale read from another thread)

**Prevention:** Add a module-level lock in `app_config.py`:

```python
import threading

_config_lock = threading.Lock()

def get_config(config_dir: str | None = None) -> dict:
    with _config_lock:
        # ... existing read logic ...

def save_config(cfg: dict, config_dir: str | None = None) -> None:
    with _config_lock:
        # ... existing write logic ...
```

Additionally, use atomic writes (write to temp file, then `os.replace`) to prevent partial-read corruption:

```python
def save_config(cfg: dict, config_dir: str | None = None) -> None:
    with _config_lock:
        config_dir = config_dir or _default_dir()
        path = os.path.join(config_dir, "config.json")
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp_path, path)  # Atomic on Windows (NTFS)
```

**Detection:** Change a setting in the GUI while a game is being recorded. If the capture continues using old settings, or if config.json becomes `{}` or empty, race condition is active.

**Confidence:** HIGH — confirmed by reading `app_config.py` directly; zero synchronization present.

---

### Pitfall 6: GUI Window Captured in Minimap Screenshots

**What goes wrong:** `minimap_capture.py` uses `mss` to grab a screen region at the bottom-right (or bottom-left) corner of the primary monitor — exactly where the League minimap sits. If the CustomTkinter GUI window is visible and overlaps that region, `mss` captures the GUI overlay instead of (or composited on top of) the minimap. This corrupts the minimap images sent for AI analysis.

**Why it happens:** `mss` captures whatever is rendered on the screen, including any window overlays. It doesn't have a concept of "capture only this specific application's window." The current headless app had no visible windows, so this was never a problem.

**Consequences:**
- Minimap images contain GUI elements → AI analysis receives garbage input
- The fundamental value proposition of the app (accurate minimap capture for coaching) is broken
- Extremely difficult to debug — the upload succeeds, but analysis quality degrades silently

**Prevention:** Multiple layers of defense:

1. **Auto-hide during recording:** When state transitions to `"recording"`, hide the GUI window:
   ```python
   def _do_update_status(self, state, detail):
       if state == "recording":
           self.withdraw()  # Hide window completely
       # ... update status ...
   ```

2. **Position the GUI away from minimap region:** On launch, position the window at top-center or top-left of the screen — never bottom-right or bottom-left where the minimap lives.

3. **Use `overrideredirect` carefully:** If making a borderless window, ensure it's not set to always-on-top, which would guarantee overlap.

4. **Document to users:** "CoachApp minimizes automatically during games to avoid interfering with captures."

**Detection:** During testing, open the GUI → start a League game → check the captured minimap PNGs in `%TEMP%/lol_coach_prints/`. If any contain GUI elements, the overlap is happening.

**Confidence:** HIGH — confirmed by reading `minimap_capture.py`; it's a raw screen grab with `mss.mss().grab(region)`.

---

## Moderate Pitfalls

Mistakes that cause bugs, poor UX, or significant rework but not architectural failure.

---

### Pitfall 7: Window Close (X Button) Kills the App Instead of Minimizing to Tray

**What goes wrong:** By default, clicking the X button on a tkinter window calls `destroy()`, which terminates `mainloop()`. Since mainloop is on the main thread and the entire app lifecycle depends on it, this kills the app — including the asyncio loop and the tray icon. Users expect a tray app to minimize to tray on close, not exit.

**Prevention:** Override `WM_DELETE_WINDOW`:

```python
class CoachGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Minimize to tray instead of quitting."""
        self.withdraw()  # Hides window, keeps mainloop running
```

Provide "Quit" only through the tray icon menu or an explicit GUI button. The tray quit action should call `self.destroy()` to actually end mainloop.

**Detection:** Click X on the GUI window. If the tray icon disappears and the process dies, this pitfall is active.

**Confidence:** HIGH — standard tkinter behavior, well-documented.

---

### Pitfall 8: Shutdown Coordination — Three Components, One Exit

**What goes wrong:** The app now has three concurrent components that must shut down cleanly:
1. CustomTkinter mainloop (main thread)
2. pystray Icon.run() (background thread)
3. asyncio coach_loop (daemon thread)

If "Quit" from the tray icon calls `stop_event.set()` but doesn't call `app.destroy()`, the asyncio loop stops but the main thread's mainloop runs forever (the window is hidden, the process won't exit). If the GUI calls `self.destroy()` but doesn't set `stop_event`, the main thread exits but the asyncio daemon thread might still be mid-upload and gets killed abruptly.

**Prevention:** Single shutdown coordinator:

```python
def request_shutdown(self):
    """Called from ANY thread — safely shuts down everything."""
    self.stop_event.set()           # Signal asyncio loop
    self.tray.stop()                # Stop pystray
    self.after(0, self.destroy)     # Destroy GUI on main thread
```

The `self.after(0, self.destroy)` is critical — if called from the tray thread, `destroy()` must be marshaled to the main thread via `after()`.

**Detection:** Quit from tray → check Task Manager. If `CoachApp.exe` is still running, shutdown coordination is broken.

**Confidence:** HIGH — direct consequence of the three-thread architecture.

---

### Pitfall 9: DPI Scaling Mismatch Between GUI and Screen Capture

**What goes wrong:** Windows DPI scaling (100%, 125%, 150%, etc.) affects how applications report and interpret coordinates. CustomTkinter is DPI-aware by default — it calls `ctypes.windll.shcore.SetProcessDpiAwareness(2)` internally. But `mss` also handles DPI awareness in its own way. If the DPI awareness mode is set by CustomTkinter before `mss` captures, or if it changes the process-wide DPI mode, the screen coordinates in `minimap_capture.py` may be interpreted differently.

**Why it happens:** DPI awareness is a process-global setting on Windows. Once set, all screen coordinate APIs in the process use the same mode. If CustomTkinter sets Per-Monitor DPI awareness (level 2), `mss` will receive physical pixels — which is correct for screen capture. But if there's a mismatch (e.g., CustomTkinter set it to System DPI aware but mss expects unaware), capture coordinates are wrong.

**Consequences:**
- Minimap capture region is offset — captures the wrong area of the screen
- Works on 100% scaling, breaks on 125% or 150% (most laptops)
- Extremely confusing to debug: "works on my desktop, fails on my laptop"

**Prevention:**
1. Explicitly set DPI awareness early in `coach_app.py`, before importing CustomTkinter or mss:
   ```python
   import ctypes
   try:
       ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor V2
   except Exception:
       pass  # Windows 7 fallback
   ```
2. Test on 125% and 150% DPI scaling specifically.
3. `mss` at v9+ handles DPI correctly when the process is Per-Monitor aware — verify this works with your `mss` version.

**Detection:** Set Windows display scaling to 150% → run the app → check if captured minimap images show the correct region.

**Confidence:** MEDIUM — DPI behavior depends on exact mss version and Windows version. The risk is real but the existing app may already handle it (mss sets its own DPI awareness). Adding CustomTkinter could change the initialization order.

---

### Pitfall 10: pystray `set_state()` + GUI `update_status()` — Dual Update Paths

**What goes wrong:** The asyncio loop currently calls `tray.set_state()` to update the tray icon. With a GUI, it also needs to call `gui.update_status()`. If these are separate calls, you get divergent state: the tray shows "Recording" but the GUI shows "Waiting" (or vice versa) due to timing differences or one call failing silently.

**Prevention:** Create a unified state manager that both the tray and GUI subscribe to:

```python
class AppState:
    def __init__(self):
        self._state = "waiting"
        self._detail = ""
        self._listeners = []  # list of callables

    def set_state(self, state: str, detail: str = ""):
        self._state = state
        self._detail = detail
        for listener in self._listeners:
            listener(state, detail)

    def add_listener(self, fn):
        self._listeners.append(fn)
```

Then the tray and GUI both register as listeners. The asyncio loop only calls `app_state.set_state()` once.

**Detection:** Watch the tray tooltip and the GUI status label during a game. If they ever show different states, dual-path updates are the cause.

**Confidence:** HIGH — architectural concern, obvious from code structure.

---

### Pitfall 11: CustomTkinter `after()` Polling Stops When Window Is Withdrawn

**What goes wrong:** When the GUI window is hidden with `self.withdraw()` (e.g., during a game to avoid screenshot interference), the `after()` callbacks may behave unexpectedly. On some platforms, `after()` timers slow down dramatically or stop firing when the window is not visible, because the Tcl event loop deprioritizes hidden windows.

**Prevention:**
- Test that `after()` callbacks still fire reliably when the window is `withdraw()`n on Windows.
- If they don't fire reliably, use a secondary mechanism: have the asyncio thread set state on a thread-safe variable, and when the window is `deiconify()`d (shown again), do a one-time sync to catch up on missed updates.
- Alternative: keep the window alive but minimized to taskbar (`self.iconify()`) instead of fully withdrawn — `iconify()` keeps the event loop active on Windows.

**Detection:** Hide the GUI → trigger state changes from asyncio → show the GUI → check if the status is current or stale.

**Confidence:** MEDIUM — behavior varies by platform. On Windows, `after()` typically works fine even when withdrawn, but worth testing explicitly.

---

### Pitfall 12: Activity Log Memory Growth

**What goes wrong:** The planned activity log shows events, uploads, errors in the GUI. If events are appended indefinitely to a list or text widget, memory grows unbounded during long gaming sessions (5+ hours).

**Prevention:**
- Cap the activity log at a fixed size (e.g., 500 entries).
- Use a ring buffer or deque with `maxlen`.
- When inserting into a CTkTextbox, delete oldest lines when count exceeds max.

```python
from collections import deque

class ActivityLog:
    def __init__(self, maxlen=500):
        self._entries = deque(maxlen=maxlen)

    def append(self, message: str):
        self._entries.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
```

**Detection:** Run the app for several hours. Check memory usage in Task Manager. If it grows steadily, the log isn't capped.

**Confidence:** HIGH — standard unbounded collection pitfall.

---

## Minor Pitfalls

Issues that cause confusion, wasted time, or minor UX problems.

---

### Pitfall 13: CustomTkinter Version Pinning

**What goes wrong:** CustomTkinter is actively developed and has had breaking API changes between versions (e.g., `CTkOptionMenu` API changed in 5.x, theme JSON format changed). Not pinning the version leads to builds breaking when a new version is released.

**Prevention:** Pin in `requirements.txt`: `customtkinter==5.2.2` (or latest stable at time of implementation). Test before bumping.

**Confidence:** HIGH

---

### Pitfall 14: Tray Icon Double-Click to Show Window — Platform Expectation

**What goes wrong:** Windows users expect to double-click a tray icon to open the main window. pystray supports this via `default` menu item, but if not configured, double-clicking does nothing. Users think the app is broken.

**Prevention:**
```python
pystray.MenuItem("Abrir CoachApp", self._show_window, default=True, visible=False)
```
The `default=True` makes it fire on double-click. `visible=False` keeps it from cluttering the context menu.

**Confidence:** HIGH

---

### Pitfall 15: Build Size Increase — Tkinter + Tcl/Tk Runtime

**What goes wrong:** Adding tkinter to the PyInstaller bundle adds the Tcl/Tk runtime (~15-20MB). The current bundle was optimized to exclude it (spec line 35). The ZIP file size will roughly double.

**Prevention:** Accept the size increase — it's unavoidable if using tkinter/CustomTkinter. Mention in release notes. Consider UPX compression (already enabled in spec). Do NOT try to optimize by excluding Tcl/Tk DLLs — this causes runtime crashes.

**Confidence:** HIGH

---

### Pitfall 16: Focus Stealing — GUI Window Appearing Over League Client

**What goes wrong:** If the GUI window is shown (deiconified) while League of Legends is in the foreground, it can steal focus from the game. This is extremely disruptive to the player — they could die in-game because the CoachApp window popped up.

**Prevention:**
- Never auto-show the GUI window during `"recording"` state.
- When showing the window from tray icon click, use `self.deiconify()` without `self.focus_force()` or `self.lift()` — let Windows handle focus naturally.
- Better: just don't show the window during game. Auto-withdraw on recording, only show between games.

**Detection:** Play a League game → trigger window show from tray → check if League loses focus.

**Confidence:** HIGH — Windows focus management is well-understood.

---

### Pitfall 17: `sys.frozen` Path Resolution for CustomTkinter in PyInstaller

**What goes wrong:** CustomTkinter resolves its asset paths relative to `customtkinter.__file__`. In a PyInstaller one-dir bundle, this works correctly if the `datas` entry places the `customtkinter` folder in the right location. But if using one-file mode (future consideration), `__file__` points inside the temp `_MEIPASS` directory, and the path structure might not match.

**Prevention:** Stick with one-dir mode (current spec already uses `COLLECT`). Verify after build:
```
dist/CoachApp/
  CoachApp.exe
  customtkinter/
    assets/
      themes/
        blue.json
        dark-blue.json
        ...
      ...
    __init__.py
    ...
```

If the `customtkinter/` directory exists alongside `CoachApp.exe`, asset resolution will work.

**Confidence:** HIGH — current spec uses one-dir, which is simpler.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Severity | Mitigation |
|-------------|---------------|----------|------------|
| Threading architecture refactor | #1 Main thread war, #2 Cross-thread updates | **CRITICAL** | Must be solved first — everything else depends on correct thread ownership |
| PyInstaller bundling | #3 tkinter excluded, #4 Assets missing | **CRITICAL** | Update spec immediately when adding CTk dependency; test built .exe, not dev |
| Config/Settings panel | #5 Race condition | **CRITICAL** | Add locking to `app_config.py` before adding GUI config writers |
| Window management | #7 Close=quit, #8 Shutdown coordination | **MODERATE** | Implement WM_DELETE_WINDOW override and unified shutdown early |
| Screen capture integration | #6 GUI over minimap, #16 Focus stealing | **CRITICAL** | Auto-withdraw window during recording state |
| Activity log | #12 Memory growth | **MODERATE** | Use deque with maxlen from day one |
| DPI testing | #9 DPI mismatch | **MODERATE** | Test on 125%+ scaling before release |
| State management | #10 Dual update paths | **MODERATE** | Build unified AppState before connecting GUI and tray |
| Build/release | #15 Size increase, #13 Version pinning | **MINOR** | Pin CTk version, document size increase |

## Recommended Implementation Order (Risk-First)

Based on pitfall severity, address in this order:

1. **Thread architecture** (Pitfalls #1, #2) — must be correct before any GUI code works
2. **PyInstaller spec update** (Pitfalls #3, #4) — must build before anything can be tested
3. **Config thread-safety** (Pitfall #5) — must be safe before adding GUI config panel
4. **Window lifecycle** (Pitfalls #7, #8, #6) — close-to-tray, shutdown, and auto-hide during capture
5. **State management** (Pitfall #10) — unified state before connecting both UI surfaces
6. **Polish** (Pitfalls #9, #12, #14, #16) — DPI, memory, tray double-click, focus

## Sources

- Direct code analysis: `coach_app.py`, `tray_icon.py`, `coach.spec`, `app_config.py`, `minimap_capture.py`, `live_coach.py`
- CPython documentation: tkinter threading model (single Tcl interpreter, main thread requirement)
- pystray source code: `_win32.py` backend uses `ctypes.windll.shell32.Shell_NotifyIconW` with independent message pump
- CustomTkinter GitHub: PyInstaller bundling notes, DPI awareness implementation
- Python `threading` module: daemon thread semantics, `threading.Lock` for file I/O
- Windows Win32 documentation: DPI awareness levels, `SetProcessDpiAwareness` API
- mss library: screen capture at physical pixel coordinates

**Confidence levels:**
- Thread architecture pitfalls (#1, #2): **HIGH** — fundamental, well-documented constraints
- PyInstaller pitfalls (#3, #4): **HIGH** — confirmed by reading current spec
- Config race condition (#5): **HIGH** — confirmed by reading app_config.py (zero locking)
- Screen capture (#6): **HIGH** — confirmed by reading minimap_capture.py (raw screen grab)
- DPI (#9): **MEDIUM** — depends on mss version + Windows version interaction
- after() behavior when withdrawn (#11): **MEDIUM** — works on Windows generally, but edge cases exist
