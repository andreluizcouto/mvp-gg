# Technology Stack — MVPApp Desktop GUI (v1.1)

**Project:** mvp.gg MVPApp
**Milestone:** v1.1 Desktop GUI
**Researched:** 2025-07-17
**Overall Confidence:** HIGH — all findings verified against installed packages and live code inspection

## Context

This stack document covers **additions and changes only** for the new desktop GUI milestone. The existing validated stack (Python 3.11, FastAPI, httpx, Pillow, mss, pystray, PyInstaller) is not re-evaluated here.

## New Dependencies

### GUI Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| customtkinter | 5.2.2 | Modern tkinter wrapper — all GUI windows and widgets | Python-native, dark mode, modern look. ~1.5 MB total. No C compilation, no Electron overhead. Wraps stdlib tkinter with themed widgets (CTkButton, CTkTextbox, CTkSwitch, CTkSegmentedButton, CTkTabview, etc.). Verified: all widgets needed for settings panel and activity log exist. |
| darkdetect | 0.8.0 | Auto-detect OS dark/light mode (CustomTkinter dependency) | Pure Python, ~9 KB. Required by customtkinter for `set_appearance_mode("system")`. No native binaries — trivial for PyInstaller. |

### Already Satisfied (no install needed)

| Technology | Status | Notes |
|------------|--------|-------|
| packaging | Already installed | Required by customtkinter, already in environment |
| tkinter | Bundled with Python 3.11 | Verified: `tkinter.TkVersion = 8.6`. Currently **excluded** in coach.spec — must be un-excluded |
| Pillow | Already installed (≥10.0.0) | Used by both pystray (icon generation) and customtkinter internally |

### No New Dependencies Needed

The GUI does **not** require:
- No web engine (no Electron, no CEF, no webview)
- No Qt bindings (no PyQt, no PySide)
- No additional image libraries beyond Pillow
- No database for the activity log (RAM-only ring buffer)

## Installation

```bash
# Single new package (darkdetect pulled automatically)
pip install customtkinter==5.2.2

# Updated requirements.txt addition:
# customtkinter==5.2.2
```

## Critical Integration: Threading Model

### Current Architecture (v1.0)
```
Main Thread:     pystray.Icon.run()          ← blocks forever (Win32 message loop)
Daemon Thread:   asyncio.run(coach_loop())   ← event loop for game monitoring
```

### New Architecture (v1.1)
```
Main Thread:     CTk.mainloop()              ← tkinter event loop (MUST be main thread)
Background:      pystray.Icon.run_detached() ← Win32 message loop in its own thread
Daemon Thread:   asyncio.run(coach_loop())   ← unchanged
```

### Why This Works (Verified)

**`pystray.Icon.run_detached()`** is a first-class API (verified in pystray 0.19.5 source) that:
1. Calls `_run_detached()` which spawns `threading.Thread(target=lambda: self._run()).start()`
2. Runs the Win32 message pump in a background thread
3. Was explicitly designed for "integrating pystray with other libraries requiring a mainloop"
4. **Verified working**: tested proof-of-concept showing main thread stays free after `run_detached()`

**tkinter requires main thread** — this is a hard constraint of the Tk library on all platforms. `CTk.mainloop()` must run on the main thread.

### Thread Communication Pattern

```python
# From asyncio/daemon thread → tkinter main thread:
root.after(0, callback)          # schedule callback on Tk event loop (thread-safe)
root.after(ms, periodic_func)    # periodic polling/updates

# From tkinter main thread → asyncio thread:
asyncio.run_coroutine_threadsafe(coro, loop)  # schedule coroutine on asyncio loop

# From any thread → pystray:
icon.icon = new_image            # pystray handles thread-safety internally (verified in v1.0)
icon.update_menu()               # already used cross-thread in current code
```

### Entry Point Changes (coach_app.py)

The `main()` function changes from:

```python
# v1.0: pystray blocks main thread
def main():
    tray = TrayIcon(on_quit=on_quit)
    t = threading.Thread(target=_run_async_loop, args=(tray, stop_event), daemon=True)
    t.start()
    tray.run()            # ← blocks main thread
```

To:

```python
# v1.1: CTk on main thread, pystray detached
def main():
    app = CoachGUI()      # CTk window
    tray = TrayIcon(on_quit=on_quit, on_show=app.show, on_hide=app.hide)
    tray.run_detached()   # ← background thread
    t = threading.Thread(target=_run_async_loop, args=(tray, app, stop_event), daemon=True)
    t.start()
    app.mainloop()        # ← blocks main thread (tkinter)
```

## PyInstaller Impact (CRITICAL)

### Problem: tkinter Is Currently Excluded

The existing `coach.spec` line 35 **explicitly excludes tkinter**:
```python
excludes=["tkinter", "matplotlib", "numpy", "scipy"],
```

This was correct for v1.0 (tray-only, no GUI). For v1.1, this exclusion **must be removed** or the app will crash on import.

### Required Changes to coach.spec

#### 1. Remove tkinter from excludes
```python
# Before
excludes=["tkinter", "matplotlib", "numpy", "scipy"],
# After
excludes=["matplotlib", "numpy", "scipy"],
```

#### 2. Add CustomTkinter assets to datas

CustomTkinter resolves assets (themes, fonts, icon) via `os.path.dirname(os.path.abspath(__file__))` chains from its module files. PyInstaller must bundle the entire `customtkinter` package directory as data:

```python
import customtkinter
import os

customtkinter_path = os.path.dirname(customtkinter.__file__)

datas=[
    ("config.json", "."),
    (customtkinter_path, "customtkinter/"),   # ~360 KB of assets (fonts, themes, icon)
],
```

**What's in the assets** (verified):
- `assets/fonts/Roboto/Roboto-Regular.ttf` (169 KB) — default font
- `assets/fonts/Roboto/Roboto-Medium.ttf` (160 KB) — bold variant
- `assets/fonts/CustomTkinter_shapes_font.otf` (3.4 KB) — widget rendering shapes
- `assets/themes/blue.json`, `dark-blue.json`, `green.json` — color themes
- `assets/icons/CustomTkinter_icon_Windows.ico` — default window icon

Without these, CustomTkinter raises `FileNotFoundError` on theme load with a message pointing to their PyInstaller wiki.

#### 3. Add hiddenimports
```python
hiddenimports=[
    # ... existing entries ...
    "customtkinter",
    "darkdetect",
    "darkdetect._windows_detect",
],
```

#### 4. Bundle size impact

| Component | Size | Notes |
|-----------|------|-------|
| CustomTkinter Python code | ~490 KB | Compiled to .pyc by PyInstaller |
| CustomTkinter assets | ~360 KB | Fonts + themes + icon |
| darkdetect | ~9 KB | Pure Python |
| tkinter stdlib (un-excluded) | ~4-6 MB | tcl/tk runtime + DLLs |
| **Total addition** | **~5-7 MB** | On top of existing one-dir bundle |

The tkinter/tcl runtime is the largest addition. This is unavoidable for any tkinter-based GUI but is a one-time cost.

## Widget Mapping to Features

| Feature | Widget | Key Methods |
|---------|--------|-------------|
| Activity log (read-only) | `CTkTextbox(state="disabled")` | `insert()`, `see("end")` for auto-scroll |
| Minimap position toggle | `CTkSegmentedButton(values=["Left", "Right"])` | `set()`, `get()`, `command=callback` |
| Minimap size setting | `CTkSegmentedButton` or `CTkSwitch` | Toggle between recommended/custom |
| App status indicator | `CTkLabel` | Dynamic text + color via `configure()` |
| Tab navigation | `CTkTabview` | `add()` tabs for Status / Settings / Log |
| Section frames | `CTkFrame` | Layout containers with padding |
| Toggle switches | `CTkSwitch` | On/off for boolean settings |

All widgets verified as available in CustomTkinter 5.2.2.

## Window Management for Tray Integration

```python
# Hide window (minimize to tray) — intercept the close button
app.protocol("WM_DELETE_WINDOW", app.withdraw)

# Show window from tray menu click
app.deiconify()
app.lift()        # bring to front
app.focus_force() # take focus

# Check if window is visible
app.winfo_viewable()  # returns 0 or 1
```

## config.json Evolution

Current `app_config.py` defaults:
```python
_DEFAULTS = {
    "minimap_left":  False,
    "minimap_large": False,
}
```

GUI adds the ability to display and edit these values visually. No new config keys are strictly required for v1.1 MVP — the existing `minimap_left` and `minimap_large` booleans map directly to GUI controls.

**Optional expansion** (if the settings panel grows):
```python
_DEFAULTS = {
    "minimap_left":  False,
    "minimap_large": False,
    "start_minimized": False,    # optional: start hidden in tray
}
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| GUI framework | CustomTkinter | PyQt6 / PySide6 | 50+ MB Qt runtime, GPL/commercial licensing complexity, overkill for settings + log |
| GUI framework | CustomTkinter | Dear PyGui | Less mature, different rendering model, harder PyInstaller story |
| GUI framework | CustomTkinter | tkinter (raw) | Works but looks like Windows 95. CustomTkinter adds modern look for ~1.5 MB |
| GUI framework | CustomTkinter | Electron/webview | 100+ MB overhead, separate runtime, defeats "lightweight companion" goal |
| Tray integration | `run_detached()` | pystray on main + tkinter in thread | tkinter crashes when not on main thread — hard constraint |
| Tray integration | `run_detached()` | Drop pystray, use tkinter tray | tkinter has no native system tray API; would need additional library anyway |

## Sources

All findings verified by direct code inspection and live execution:

- **CustomTkinter 5.2.2**: `pip show customtkinter` + package source inspection (HIGH confidence)
- **pystray 0.19.5 `run_detached()`**: Source inspection of `pystray._win32.Icon` (HIGH confidence)
- **PyInstaller asset bundling**: CustomTkinter source `theme_manager.py` line 16-20 + `font/__init__.py` lines 10-18 (HIGH confidence)
- **Threading model**: Live proof-of-concept execution confirming `run_detached()` frees main thread (HIGH confidence)
- **Widget API**: Live instantiation and method verification of CTkTextbox, CTkSwitch, CTkSegmentedButton, CTkTabview (HIGH confidence)
- **tkinter main-thread requirement**: Standard tkinter constraint, verified by CustomTkinter using stdlib tkinter internals (HIGH confidence)

---
*Research completed: 2025-07-17*
