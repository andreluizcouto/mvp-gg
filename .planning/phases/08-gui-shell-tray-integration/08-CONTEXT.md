# Phase 8: GUI Shell + Tray Integration - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a functional dark-themed CustomTkinter window that coexists with the existing system tray. The window shows app branding, hides to tray on close (instead of quitting), and can be restored via double-click or tray menu. This phase adds the visual shell only — content panels (status, settings, activity log) are Phase 9-10.

</domain>

<decisions>
## Implementation Decisions

### Window Appearance
- **D-01:** Use CustomTkinter default dark theme (#2b2b2b) — no custom color overrides needed
- **D-02:** Display the mvp.gg logo (`mvpgg.png` at project root) at the top of the window as branding
- **D-03:** Window title: "MVPApp" (or "mvp.gg")
- **D-04:** Window size is at the agent's discretion — choose dimensions that make sense for the content (status + future panels). Tamanho fixo, não redimensionável.
- **D-05:** Window opens centered on screen

### Close-to-Tray Behavior
- **D-06:** Clicking the X button hides the window to tray (withdraw) instead of quitting the app
- **D-07:** Show a tray notification/balloon when minimizing to tray ("MVPApp continua rodando no tray")
- **D-08:** Add a "Não mostrar novamente" option — persist this preference in config.json via `update_config("hide_tray_notification", True)`
- **D-09:** First time always shows notification; subsequent closes respect the user's preference

### Tray Integration
- **D-10:** Double-click on tray icon restores (deiconify) the window — standard Windows behavior
- **D-11:** Add "Abrir MVPApp" menu item to tray context menu (right-click), positioned as first item
- **D-12:** Existing tray menu items (status, Ver análise, minimap settings, Sair) remain unchanged
- **D-13:** "Sair" menu item quits the entire app (existing behavior preserved)

### Agent's Discretion
- Window dimensions (pick appropriate size for status + branding + future content)
- Whether to use CTk `set_appearance_mode("dark")` or let it auto-detect
- Icon for window titlebar (use mvpgg.png or convert as needed)
- Animation/transition when showing/hiding window (if any)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 7 Foundation
- `.planning/phases/07-threading-foundation-eventbus/07-RESEARCH.md` — Threading model, EventBus API, pystray.run_detached() pattern
- `.planning/phases/07-threading-foundation-eventbus/07-01-PLAN.md` — EventBus implementation details
- `.planning/phases/07-threading-foundation-eventbus/07-02-PLAN.md` — 3-thread model restructure

### Core Implementation Files
- `backend/coach_app.py` — Main entry point, 3-thread orchestration, CTk window creation (currently hidden via withdraw())
- `backend/tray_icon.py` — TrayIcon class, menu structure, set_state(), run_detached()
- `backend/event_bus.py` — EventBus, EventType enum, subscribe/emit/start_polling API
- `backend/app_config.py` — Thread-safe config read/write with RLock, get_config/update_config

### Assets
- `mvpgg.png` (project root) — App logo/icon for window branding
- `frontend/public/favicon.svg` — SVG favicon (purple lightning bolt, brand color #863bff)

### Requirements
- `.planning/REQUIREMENTS.md` §v1.1 Desktop App Window — WIN-01, WIN-02, WIN-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **CTk window**: Already created in `coach_app.py` as `app = ctk.CTk()` → currently `app.withdraw()`. Phase 8 will show this window.
- **EventBus**: Fully functional cross-thread event system. Subscribe to STATE_CHANGE for real-time status updates.
- **TrayIcon**: Has `set_state()`, menu management, `run_detached()`. Needs new "Abrir MVPApp" menu item and double-click handler.
- **app_config**: Thread-safe config. Will add `hide_tray_notification` key for D-08.
- **mvpgg.png**: Logo file at project root for window branding.

### Established Patterns
- **Threading**: CTk mainloop on main thread, pystray on background thread, asyncio on daemon thread
- **Cross-thread comms**: EventBus (queue.Queue + after() polling at 100ms)
- **Config**: `update_config(key, value)` for atomic read-modify-write with RLock
- **State colors**: Gray=waiting, Gold=recording, Blue=uploading, Green=ready (from tray_icon.py)

### Integration Points
- `coach_app.py:main()` — Remove `app.withdraw()`, add window setup before `app.mainloop()`
- `tray_icon.py` — Add "Abrir MVPApp" menu item, add double-click callback, add notification on hide
- `app_config.py` — Add `hide_tray_notification` to defaults
- Window protocol `WM_DELETE_WINDOW` — Override to hide instead of destroy

</code_context>

<specifics>
## Specific Ideas

- Logo is a purple lightning bolt (brand color #863bff) — keep visual consistency
- User wants tray notification every time they close to tray, with option to suppress ("não mostrar novamente")
- Behavior should feel like standard Windows app (Discord-style hide-to-tray)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-gui-shell-tray-integration*
*Context gathered: 2026-04-02*
