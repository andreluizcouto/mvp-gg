# Phase 8: GUI Shell + Tray Integration - Research

**Researched:** 2026-04-02
**Domain:** CustomTkinter window setup / pystray tray integration / cross-thread show-hide / Windows balloon notifications
**Confidence:** HIGH

## Summary

Phase 8 transforms the currently hidden CTk window (`app.withdraw()` in `coach_app.py`) into a visible, dark-themed GUI shell with branding, and integrates bidirectional show/hide behavior with the existing system tray. The core technical challenge is cross-thread window management: pystray callbacks fire on the tray background thread, but tkinter widgets (including `withdraw()`, `deiconify()`, `lift()`) must only be called from the main thread. The solution is to schedule all window operations via `app.after(0, ...)` from pystray callbacks — the same pattern already validated in Phase 7 for EventBus.

All key APIs were **empirically validated** on the target environment (Python 3.11.9, Windows, CustomTkinter 5.2.2, pystray 0.19.5, Pillow 12.2.0):
- `CTkImage` + `CTkLabel` for logo display (1536×1024 PNG at 3:2 aspect ratio)
- `app.protocol("WM_DELETE_WINDOW", handler)` for intercept-close-to-tray
- `pystray.MenuItem(default=True)` for left-click → show window (also triggers on double-click)
- `pystray.Icon.notify(message, title)` for Windows balloon notifications — `HAS_NOTIFICATION=True` confirmed
- `app.iconphoto()` + `_iconbitmap_method_called = True` workaround for custom window icon from PNG
- `app_config.py` has a **whitelist bug**: `get_config()` only returns hardcoded keys — adding `hide_tray_notification` requires updating both `_DEFAULTS` and the return dict

**Primary recommendation:** Modify `coach_app.py` to remove `app.withdraw()`, add window setup (dark theme, branding, centered, non-resizable, close-to-tray protocol). Modify `tray_icon.py` to accept a `show_window` callback, add "Abrir MVPApp" as `default=True` first menu item, and call `icon.notify()` on hide. Add `hide_tray_notification` to `app_config.py` defaults and whitelist. All pystray→GUI calls go through `app.after(0, fn)`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use CustomTkinter default dark theme (#2b2b2b) — no custom color overrides needed
- **D-02:** Display the mvp.gg logo (`mvpgg.png` at project root) at the top of the window as branding
- **D-03:** Window title: "MVPApp" (or "mvp.gg")
- **D-04:** Window size is at the agent's discretion — choose dimensions that make sense for the content (status + future panels). Tamanho fixo, não redimensionável.
- **D-05:** Window opens centered on screen
- **D-06:** Clicking the X button hides the window to tray (withdraw) instead of quitting the app
- **D-07:** Show a tray notification/balloon when minimizing to tray ("MVPApp continua rodando no tray")
- **D-08:** Add a "Não mostrar novamente" option — persist this preference in config.json via `update_config("hide_tray_notification", True)`
- **D-09:** First time always shows notification; subsequent closes respect the user's preference
- **D-10:** Double-click on tray icon restores (deiconify) the window — standard Windows behavior
- **D-11:** Add "Abrir MVPApp" menu item to tray context menu (right-click), positioned as first item
- **D-12:** Existing tray menu items (status, Ver análise, minimap settings, Sair) remain unchanged
- **D-13:** "Sair" menu item quits the entire app (existing behavior preserved)

### Agent's Discretion
- Window dimensions (pick appropriate size for status + branding + future content)
- Whether to use CTk `set_appearance_mode("dark")` or let it auto-detect
- Icon for window titlebar (use mvpgg.png or convert as needed)
- Animation/transition when showing/hiding window (if any)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WIN-01 | User sees a clean, dark-mode main window with app branding when launching MVPApp | CTk `set_appearance_mode("dark")` + CTkImage for logo + `app.resizable(False, False)` + centered geometry — all validated empirically. See Pattern 1. |
| WIN-02 | User can close the window and the app minimizes to system tray instead of exiting | `app.protocol("WM_DELETE_WINDOW", on_close_handler)` intercepts X button. `app.withdraw()` hides window. `icon.notify()` shows balloon. Config check for `hide_tray_notification`. See Pattern 2. |
| WIN-03 | User can show the window again by double-clicking the tray icon | `pystray.MenuItem(default=True)` triggers on left-click (including double-click) via `WM_LBUTTONUP`. Callback uses `app.after(0, show_window)` for thread safety. See Pattern 3. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| customtkinter | 5.2.2 | Dark-themed GUI framework | Already installed. Built-in dark mode, CTkImage for HiDPI-aware image display |
| pystray | 0.19.5 | System tray icon and menu | Already in use. `notify()`, `default=True` menu items, `run_detached()` all confirmed on Windows |
| Pillow | 12.2.0 | Image loading and resizing | Already installed. Loads mvpgg.png, creates CTkImage and iconphoto instances |
| queue (stdlib) | N/A | Thread-safe event queue | Already in use via EventBus |
| threading (stdlib) | N/A | RLock for config, Event for shutdown | Already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tkinter (stdlib) | 8.6 (bundled) | Base for CustomTkinter, `PhotoImage` for `iconphoto` | Window icon setup via `ImageTk.PhotoImage` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `iconphoto()` with PNG | `iconbitmap()` with .ico file | iconbitmap requires .ico format. iconphoto accepts PhotoImage from PIL. Using iconphoto avoids runtime .ico conversion. Requires setting `_iconbitmap_method_called = True` to prevent CTk's default icon override. |
| `set_appearance_mode("dark")` | Let CTk auto-detect OS | Auto-detect may pick "light" on some Windows configs. Explicit "dark" guarantees the user decision D-01. |

**Installation:**
```bash
# No new packages needed — all dependencies already installed
pip install customtkinter>=5.2.2  # already present
```

**Version verification (empirically confirmed on target):**
- customtkinter: 5.2.2 — INSTALLED
- pystray: 0.19.5 — INSTALLED
- Pillow: 12.2.0 — INSTALLED
- Python: 3.11.9 — INSTALLED

## Architecture Patterns

### Recommended File Changes
```
backend/
├── coach_app.py          # MODIFIED: remove withdraw(), add window setup, pass show_window to tray
├── tray_icon.py           # MODIFIED: add show_window callback, "Abrir MVPApp" menu item, notify on hide
├── app_config.py          # MODIFIED: add hide_tray_notification to _DEFAULTS and get_config whitelist
└── tests/
    ├── test_app_config.py # MODIFIED: update defaults assertions for new key
    └── test_gui_shell.py  # NEW: window setup, close-to-tray, restore tests
```

### Pattern 1: Window Setup (WIN-01)
**What:** Create a dark-themed, branded, centered, non-resizable CTk window
**When to use:** `coach_app.py` main() — replace the current `app.withdraw()` block
**Critical insights:**
- `set_appearance_mode("dark")` must be called BEFORE `ctk.CTk()` to guarantee dark theme
- `iconphoto()` sets the taskbar/titlebar icon from PIL image — but CTk overrides it after 200ms unless `_iconbitmap_method_called = True` is set
- `update_idletasks()` must be called before reading `winfo_width()/winfo_height()` for centering
- mvpgg.png is 1536×1024 (3:2 ratio) — display at ~280×187 for branding

```python
# Source: Empirically validated on Python 3.11.9, Windows, CTk 5.2.2
import customtkinter as ctk
from PIL import Image, ImageTk

# MUST be before CTk() constructor
ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("MVPApp")
app.geometry("450x600")
app.resizable(False, False)

# --- Custom window icon (prevent CTk default) ---
icon_img = Image.open("mvpgg.png").resize((64, 64), Image.Resampling.LANCZOS)
icon_photo = ImageTk.PhotoImage(icon_img)
app._iconbitmap_method_called = True  # Prevent CTk's 200ms default icon override
app.iconphoto(True, icon_photo)
app._custom_icon_ref = icon_photo  # Prevent garbage collection

# --- Logo branding ---
logo_pil = Image.open("mvpgg.png")
logo = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(280, 187))
logo_label = ctk.CTkLabel(app, text="", image=logo)
logo_label.pack(pady=(30, 10))

# --- Center on screen ---
app.update_idletasks()
sw = app.winfo_screenwidth()
sh = app.winfo_screenheight()
w = app.winfo_width()
h = app.winfo_height()
x = (sw - w) // 2
y = (sh - h) // 2
app.geometry(f"+{x}+{y}")
```

### Pattern 2: Close-to-Tray with Notification (WIN-02)
**What:** X button hides window to tray instead of quitting, with optional balloon notification
**When to use:** `coach_app.py` — register WM_DELETE_WINDOW protocol on the CTk window
**Critical insights:**
- `app.protocol("WM_DELETE_WINDOW", handler)` intercepts the X button
- `app.withdraw()` hides the window completely (no taskbar entry)
- `pystray.Icon.notify(message, title)` shows a Windows balloon notification — `HAS_NOTIFICATION=True` confirmed
- `icon.remove_notification()` cleans up the notification
- The notification check must read `hide_tray_notification` from config — but `get_config()` has a **whitelist** that drops unknown keys (see Pitfall 1)

```python
# Source: Empirically validated on target environment
from app_config import get_config

def _on_close_to_tray():
    """WM_DELETE_WINDOW handler — hides window, optionally shows notification."""
    app.withdraw()
    
    cfg = get_config()
    if not cfg.get("hide_tray_notification", False):
        tray.notify("MVPApp continua rodando no tray", "MVPApp")

app.protocol("WM_DELETE_WINDOW", _on_close_to_tray)
```

### Pattern 3: Tray-to-Window Restore (WIN-03)
**What:** Left-click or double-click on tray icon shows the window; "Abrir MVPApp" menu item does the same
**When to use:** `tray_icon.py` — add `default=True` menu item and pass `show_window` callback
**Critical insights:**
- pystray on Windows fires the default action on `WM_LBUTTONUP` (left-click release). A double-click naturally triggers this too (the first release fires it).
- `MenuItem(text, action, default=True, visible=True)` — `default=True` makes the item bold in the context menu AND triggers on left-click of the tray icon.
- The callback fires on the **pystray background thread** — MUST use `app.after(0, show_window)` to schedule on main thread.
- `deiconify()` + `lift()` + `focus_force()` is the reliable Windows restore pattern.

```python
# Source: Empirically validated cross-thread show pattern

# In coach_app.py — define the show function
def show_window():
    """Restore window. MUST run on main thread."""
    app.deiconify()
    app.lift()
    app.focus_force()

# In tray_icon.py — TrayIcon accepts a show_window callback
class TrayIcon:
    def __init__(self, on_quit: Callable, on_show: Callable | None = None):
        self._on_show = on_show
        # ...
    
    def _show_window(self, icon, item):
        """Called from pystray thread — schedule on main thread."""
        if self._on_show:
            self._on_show()  # caller provides app.after(0, show_window)
    
    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                "Abrir MVPApp",
                self._show_window,
                default=True,   # triggers on left-click AND shows bold in menu
                visible=True,   # visible in context menu per D-11
            ),
            pystray.Menu.SEPARATOR,
            # ... existing menu items unchanged (D-12) ...
        )
```

### Pattern 4: Thread-Safe Callback Wiring
**What:** Bridge pystray→main thread for all window operations
**When to use:** `coach_app.py` main() — when creating callbacks for TrayIcon
**Critical insight:** pystray callbacks run on the pystray thread. ALL tkinter calls must be scheduled via `app.after(0, fn)`. The `on_show` callback passed to TrayIcon should already include the `app.after()` wrapper.

```python
# In coach_app.py main()
def on_show_from_tray():
    """Called from pystray thread. Schedules show on main thread."""
    app.after(0, show_window)

tray = TrayIcon(on_quit=on_quit, on_show=on_show_from_tray)
```

### Anti-Patterns to Avoid
- **Calling tkinter methods from pystray thread:** `app.deiconify()` from pystray callback → Tcl error or silent corruption. Always use `app.after(0, fn)`.
- **Forgetting image reference retention:** CTkImage and PhotoImage are garbage-collected if not stored → blank image. Always keep a reference (e.g., `app._custom_icon_ref = photo`).
- **Using `app.iconify()` instead of `app.withdraw()`:** `iconify()` minimizes to taskbar (still visible). `withdraw()` fully hides (no taskbar entry) — correct for tray behavior per D-06.
- **Calling `app.geometry()` for centering before `update_idletasks()`:** Returns (1, 1) as the window hasn't been rendered yet.
- **Setting appearance mode after CTk():** The theme may not apply correctly to the window frame on Windows.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Window icon from PNG | Runtime PIL→.ico conversion | `iconphoto()` + `_iconbitmap_method_called = True` | Simpler, no temp files, works on Windows with proper flag |
| HiDPI-aware logo display | Manual PIL resize + tkinter PhotoImage | `CTkImage(light_image, dark_image, size)` | CTkImage handles DPI scaling automatically across monitors |
| Tray balloon notification | Custom Win32 `Shell_NotifyIcon` calls | `pystray.Icon.notify(message, title)` | pystray wraps the Win32 API cleanly. `HAS_NOTIFICATION=True` on Windows. |
| Double-click handler | Manual Win32 message hook | `pystray.MenuItem(default=True)` | default=True triggers on `WM_LBUTTONUP` — works for both single and double click |
| Thread-safe window show | Custom Lock + flag checking | `app.after(0, show_window)` | Standard tkinter pattern for scheduling on main thread from any thread |

**Key insight:** pystray + CustomTkinter + `app.after()` cover all requirements without any Win32 API calls or custom thread synchronization.

## Common Pitfalls

### Pitfall 1: app_config.py Whitelist Drops New Keys
**What goes wrong:** `update_config("hide_tray_notification", True)` writes the key to config.json, but `get_config()` returns a hardcoded dict with only `minimap_left` and `minimap_large` — the new key is silently dropped on read-back.
**Why it happens:** `get_config()` (lines 37-40) constructs its return dict by explicitly listing each known key. Any key not in this whitelist is ignored.
**How to avoid:** Add `"hide_tray_notification": False` to `_DEFAULTS` AND add it to the return dict in `get_config()`. Update existing test assertions for defaults (`test_get_config_returns_defaults_when_no_file`, `test_get_config_returns_defaults_for_corrupted_json`).
**Warning signs:** Notification always shows even after user clicks "don't show again" — config writes succeed but reads lose the key.
**Empirically confirmed:** Tested — `update_config("hide_tray_notification", False)` writes to JSON, but `get_config()` returns only 2 keys.

### Pitfall 2: CTk Default Icon Override at 200ms
**What goes wrong:** You set a custom window icon, but after 200ms the CustomTkinter logo appears instead.
**Why it happens:** `CTk.__init__` schedules `after(200, self._windows_set_titlebar_icon)` which calls `iconbitmap()` with the CTk default icon — but only if `_iconbitmap_method_called` is False.
**How to avoid:** Set `app._iconbitmap_method_called = True` before or immediately after calling `app.iconphoto()`. This prevents the 200ms override.
**Warning signs:** Window initially shows your icon, then flickers to the CTk gear icon.

### Pitfall 3: PhotoImage Garbage Collection
**What goes wrong:** Logo or icon appears blank or the window shows a broken image.
**Why it happens:** Python's garbage collector destroys `ImageTk.PhotoImage` objects when no reference exists. Tkinter's internal Tcl reference doesn't count as a Python reference.
**How to avoid:** Store the PhotoImage as an attribute: `app._custom_icon_ref = photo_img` and `logo_label._image_ref = logo` (CTkLabel with CTkImage usually handles this, but iconphoto's PhotoImage needs manual retention).
**Warning signs:** Image works initially, goes blank after a few seconds or after a GC cycle.

### Pitfall 4: Window Not Coming to Foreground on Restore
**What goes wrong:** User double-clicks tray icon but the window appears behind other windows or only flashes in the taskbar.
**Why it happens:** Windows has strict rules about `SetForegroundWindow` — only the foreground app can bring another window forward. `focus_force()` can bypass this but may only flash the taskbar on some Windows versions.
**How to avoid:** Use the full sequence: `deiconify()` → `lift()` → `focus_force()`. This works reliably when called via `app.after(0, ...)` from a tray click (user-initiated action).
**Warning signs:** Window state is "normal" but it's behind other windows.

### Pitfall 5: Notification Persisting After Window Restore
**What goes wrong:** The balloon notification stays visible even after the user restores the window.
**Why it happens:** `icon.notify()` shows a persistent notification on Windows. It auto-dismisses after a few seconds, but if the user restores quickly, both the notification and window are visible.
**How to avoid:** Call `icon.remove_notification()` in the `show_window` function.
**Warning signs:** Both notification balloon and restored window visible simultaneously.

### Pitfall 6: Menu Item Order Breaking Existing Behavior
**What goes wrong:** Existing tray menu items stop working or are in wrong order.
**Why it happens:** Inserting "Abrir MVPApp" as first item with `default=True` while existing items have different callback signatures.
**How to avoid:** Place "Abrir MVPApp" first, then separator, then ALL existing items unchanged. Verify callback signatures match pystray's `(icon, item)` convention (existing callbacks already use this).
**Warning signs:** Right-click menu shows items in wrong order or clicking existing items raises TypeError.

## Code Examples

### Complete Window Setup (coach_app.py modifications)
```python
# Source: Empirically validated — all patterns tested on Python 3.11.9, Windows, CTk 5.2.2, pystray 0.19.5

import os
import customtkinter as ctk
from PIL import Image, ImageTk
from app_config import get_config

# Resolve logo path relative to base dir
_LOGO_PATH = os.path.join(_BASE_DIR, "..", "mvpgg.png")  # project root

# Set dark mode BEFORE creating window
ctk.set_appearance_mode("dark")

def main() -> None:
    stop_event = threading.Event()
    event_bus = EventBus()

    # 1. Create CTk window
    app = ctk.CTk()
    app.title("MVPApp")
    app.geometry("450x600")
    app.resizable(False, False)

    # 2. Custom window icon
    icon_pil = Image.open(_LOGO_PATH).resize((64, 64), Image.Resampling.LANCZOS)
    icon_photo = ImageTk.PhotoImage(icon_pil)
    app._iconbitmap_method_called = True
    app.iconphoto(True, icon_photo)
    app._icon_ref = icon_photo  # prevent GC

    # 3. Logo branding
    logo_pil = Image.open(_LOGO_PATH)
    logo_ctk = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(280, 187))
    logo_label = ctk.CTkLabel(app, text="", image=logo_ctk)
    logo_label.pack(pady=(30, 10))

    # 4. Center on screen
    app.update_idletasks()
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    w, h = app.winfo_width(), app.winfo_height()
    app.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # 5. Show/hide functions
    def show_window():
        """Restore window to foreground. Main thread only."""
        app.deiconify()
        app.lift()
        app.focus_force()
        if tray._icon:
            tray._icon.remove_notification()

    def on_close_to_tray():
        """WM_DELETE_WINDOW handler — hide to tray with optional notification."""
        app.withdraw()
        cfg = get_config()
        if not cfg.get("hide_tray_notification", False):
            if tray._icon:
                tray._icon.notify("MVPApp continua rodando no tray", "MVPApp")

    app.protocol("WM_DELETE_WINDOW", on_close_to_tray)

    # 6. Quit handler (unchanged pattern from Phase 7)
    def on_quit():
        stop_event.set()
        app.after(0, app.quit)

    # 7. Tray with show callback
    def on_show_from_tray():
        app.after(0, show_window)

    tray = TrayIcon(on_quit=on_quit, on_show=on_show_from_tray)
    tray.run_detached()

    # 8-10: asyncio thread, EventBus polling, mainloop (same as Phase 7)
    # ...
```

### TrayIcon Modifications (tray_icon.py)
```python
# Source: Validated pattern — MenuItem(default=True) + notify()

class TrayIcon:
    def __init__(self, on_quit: Callable, on_show: Callable | None = None):
        self._state = "waiting"
        self._detail = ""
        self._on_quit = on_quit
        self._on_show = on_show  # NEW: callback to show window
        self._icon: pystray.Icon | None = None
        self._lock = threading.Lock()

    def _show_window(self, icon, item) -> None:
        """Triggered by left-click (default action) or 'Abrir MVPApp' menu item."""
        if self._on_show:
            self._on_show()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            # NEW: "Abrir MVPApp" as first item, default action, bold
            pystray.MenuItem(
                "Abrir MVPApp",
                self._show_window,
                default=True,
                visible=True,
            ),
            pystray.Menu.SEPARATOR,
            # EXISTING items preserved (D-12)
            pystray.MenuItem(
                lambda item: _STATUS_LABELS.get(self._state, ""),
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Ver analise",
                self._open_site,
                enabled=lambda item: self._state in ("uploading", "ready"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Minimapa a esquerda",
                self._toggle_left,
                checked=lambda item: get_config().get("minimap_left", False),
            ),
            pystray.MenuItem(
                "Minimapa grande",
                self._toggle_large,
                checked=lambda item: get_config().get("minimap_large", False),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._quit),
        )
```

### Config Update (app_config.py)
```python
# Source: Fixing the whitelist pattern — add hide_tray_notification

_DEFAULTS = {
    "minimap_left":  False,
    "minimap_large": False,
    "hide_tray_notification": False,  # NEW: D-08
}

def get_config(config_dir: str | None = None) -> dict:
    with _config_lock:
        config_dir = config_dir or _default_dir()
        path = os.path.join(config_dir, "config.json")
        if not os.path.exists(path):
            return dict(_DEFAULTS)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return {
                "minimap_left":  bool(data.get("minimap_left",  _DEFAULTS["minimap_left"])),
                "minimap_large": bool(data.get("minimap_large", _DEFAULTS["minimap_large"])),
                "hide_tray_notification": bool(data.get("hide_tray_notification", _DEFAULTS["hide_tray_notification"])),
            }
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULTS)
```

### "Não mostrar novamente" Pattern (D-08)
```python
# Source: Design pattern — the "don't show again" checkbox is not a Phase 8 widget
# (no checkbox in the window yet — that's Phase 9 settings). In Phase 8, the mechanism
# is: config key exists, notification checks it, and update_config can set it.
# The actual UI toggle comes in Phase 9. For now, the config key and the check are sufficient.

# In the on_close_to_tray handler:
cfg = get_config()
if not cfg.get("hide_tray_notification", False):
    tray._icon.notify("MVPApp continua rodando no tray", "MVPApp")

# Later in Phase 9, a settings toggle will call:
# update_config("hide_tray_notification", True)
```

## Window Dimensions Recommendation

**Recommended size: 450×600 (fixed)**

Rationale:
- Logo (280×187) needs ~220px vertical space with padding
- Phase 9 adds: status panel (~80px), "How it works" section (~200px), settings (~120px)
- Phase 10 adds: activity log (scrollable, remaining space)
- 450px wide accommodates text content without horizontal scroll
- Leaves comfortable margins (~85px each side for 280px logo)
- 600px height fits branding + future panels without feeling cramped
- Not too tall for 1080p screens (leaves room for taskbar)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tkinter PhotoImage for images | CTkImage with Pillow | CTk 5.x | DPI-aware, supports light/dark variants |
| Manual .ico conversion for window icon | `iconphoto()` with PhotoImage | tkinter 8.5+ | No temp file needed, works with any image format Pillow supports |
| Custom Win32 notification code | `pystray.Icon.notify()` | pystray 0.19+ | Clean API, `HAS_NOTIFICATION` capability check |
| `app.withdraw()` on startup | `app.withdraw()` only on close-to-tray | Phase 8 | Window visible on launch, hidden only when user closes |

## Open Questions

1. **"Não mostrar novamente" UI in Phase 8 or Phase 9?**
   - What we know: D-08 says persist the preference via `update_config`. D-07/D-09 describe the notification behavior.
   - What's unclear: The CONTEXT.md doesn't specify a checkbox widget in the Phase 8 window (which is just a shell + branding). The "settings" panel is Phase 9.
   - Recommendation: Phase 8 implements the **config key** (`hide_tray_notification`) and the **notification check** in the close handler. Phase 9 adds the actual toggle UI. If a quick mechanism is wanted in Phase 8, a simple approach is to include a button/link in the notification itself — but pystray's `notify()` API only supports text, not interactive elements. The planner should decide: either (a) config key only in Phase 8 (testable via manual `update_config` or config.json edit), or (b) add a minimal checkbox to the Phase 8 window shell.

2. **Logo path resolution in PyInstaller bundle**
   - What we know: `mvpgg.png` is at project root (`C:\Users\andre\Desktop\mvp-gg\mvpgg.png`). `_BASE_DIR` in coach_app.py resolves to the backend/ directory.
   - What's unclear: In Phase 11 PyInstaller build, how will the logo path resolve?
   - Recommendation: Use `os.path.join(_BASE_DIR, "..", "mvpgg.png")` for now. Phase 11 will handle bundling assets. Alternatively, move/copy the logo to `backend/` for simpler path resolution. The planner should decide.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none (uses default discovery) |
| Quick run command | `python -m pytest tests/test_gui_shell.py -x -v` |
| Full suite command | `python -m pytest tests/ -x -v --timeout=30` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIN-01 | Dark window with branding, centered, non-resizable | unit | `python -m pytest tests/test_gui_shell.py::test_window_dark_theme -x` | ❌ Wave 0 |
| WIN-01 | Logo displayed via CTkImage | unit | `python -m pytest tests/test_gui_shell.py::test_logo_displayed -x` | ❌ Wave 0 |
| WIN-02 | X button hides to tray (withdraw) | unit | `python -m pytest tests/test_gui_shell.py::test_close_to_tray -x` | ❌ Wave 0 |
| WIN-02 | Notification shown on first hide | unit | `python -m pytest tests/test_gui_shell.py::test_notification_on_hide -x` | ❌ Wave 0 |
| WIN-02 | Notification suppressed when config set | unit | `python -m pytest tests/test_gui_shell.py::test_notification_suppressed -x` | ❌ Wave 0 |
| WIN-03 | Tray default action restores window | integration | `python -m pytest tests/test_gui_shell.py::test_tray_restore_window -x` | ❌ Wave 0 |
| WIN-03 | "Abrir MVPApp" menu item exists as default | unit | `python -m pytest tests/test_gui_shell.py::test_abrir_menu_item -x` | ❌ Wave 0 |
| APP-03 | hide_tray_notification config round-trip | unit | `python -m pytest tests/test_app_config.py::test_hide_tray_notification_config -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_gui_shell.py tests/test_app_config.py -x -v`
- **Per wave merge:** `python -m pytest tests/ -x -v --timeout=30`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_gui_shell.py` — covers WIN-01, WIN-02, WIN-03 (new file, module-scoped Tk fixture pattern from test_threading.py)
- [ ] `tests/test_app_config.py` — update existing defaults assertions for `hide_tray_notification` key
- [ ] No new framework install needed — pytest 9.0.2 already configured

### Testing Strategy Notes
- Use the **module-scoped `_tk_root` fixture** pattern established in `test_threading.py` to avoid Tcl state corruption on Windows
- TrayIcon tests can mock `pystray.Icon` to avoid spawning real Win32 tray threads
- Notification tests should mock `icon.notify()` and verify it's called/not called based on config
- Window centering tests can check geometry string contains positive x,y coordinates

## Sources

### Primary (HIGH confidence)
- **Empirical validation** — all key APIs tested directly on target environment (Python 3.11.9, Windows, CTk 5.2.2, pystray 0.19.5, Pillow 12.2.0)
- **pystray source code inspection** — `Icon._on_notify()`, `Icon.__call__()`, `Menu.__call__()`, `MenuItem.__init__`, `Icon.notify()` signatures and behavior verified via `inspect.getsource()`
- **CustomTkinter source code inspection** — `CTk.__init__()`, `CTk.iconbitmap()`, `CTk._windows_set_titlebar_icon()`, `CTkImage.__init__()`, `CTkLabel.__init__()` verified via `inspect.getsource()`
- **Existing codebase** — `coach_app.py`, `tray_icon.py`, `event_bus.py`, `app_config.py` read and analyzed

### Secondary (MEDIUM confidence)
- **Phase 7 research** — threading model, EventBus patterns, `app.after()` polling validated in Phase 7 (07-RESEARCH.md)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and version-verified
- Architecture: HIGH — every pattern empirically validated on the target environment
- Pitfalls: HIGH — whitelist bug confirmed by test, CTk icon override confirmed by source inspection
- Window dimensions: MEDIUM — reasonable estimate but may need adjustment in Phase 9 when content panels are added

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable — all dependencies are installed and pinned)
