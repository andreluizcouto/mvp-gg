# ProjectB/coach_app.py
"""
Entry point do CoachApp local.
3-thread model: main=CustomTkinter, background=pystray, daemon=asyncio.
EventBus bridges cross-thread communication via queue.Queue + after() polling.
"""
import asyncio
import logging
import os
import sys
import threading

from dotenv import load_dotenv

# Resolve diretorio base: funciona tanto em dev quanto no .exe (PyInstaller one-dir)
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(_BASE_DIR, ".env"))

import httpx

import customtkinter as ctk
from PIL import Image, ImageTk
from app_config import get_config, update_config
from event_bus import EventBus, EventType, Event
from live_coach import LiveCoachSession
from tray_icon import TrayIcon, _STATUS_LABELS, _COLORS, SITE_URL

# Logging para arquivo (console=False no .exe nao mostra nada)
_log_file = os.path.join(_BASE_DIR, "coach_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger("coach_app")
logger.info("CoachApp iniciando - base_dir=%s", _BASE_DIR)

# Logo path (project root — _BASE_DIR is backend/)
_LOGO_PATH = os.path.join(_BASE_DIR, "..", "mvpgg.png")

# Dark mode MUST be set before CTk() constructor
ctk.set_appearance_mode("dark")

# Constantes
BACKEND_URL = os.environ.get("BACKEND_URL", "https://lol-coach-backend-z4b7.onrender.com")
# Nunca embuta o segredo do app local no binario.
LOCAL_APP_TOKEN = (os.environ.get("LOCAL_APP_TOKEN") or os.environ.get("APP_TOKEN") or "").strip()
POLL_INTERVAL = 10  # segundos entre checks de status


def _build_auth_headers() -> dict[str, str] | None:
    if not LOCAL_APP_TOKEN:
        return None
    return {"X-App-Token": LOCAL_APP_TOKEN}


async def _upload(session: LiveCoachSession, tray: TrayIcon) -> str | None:
    """Envia dados da partida ao backend. Retorna riot_id ou None em caso de falha."""
    headers = _build_auth_headers()
    if not headers:
        logger.error("LOCAL_APP_TOKEN/APP_TOKEN nao configurado no CoachApp. Configure o .env antes de enviar uploads.")
        return None

    payload = session.get_postgame_payload()
    if not payload:
        logger.warning("Sem dados para upload.")
        return None

    events = []
    for evt in payload.get("events", []):
        events.append(
            {
                "event_type": evt.get("event_type", ""),
                "game_time": evt.get("game_time", "00:00"),
                "champion": evt.get("champion", ""),
                "killer": evt.get("killer"),
                "victim": evt.get("victim"),
                "detail": evt.get("detail", ""),
                "assisters": evt.get("assisters", []),
                "minimap_base64": evt.get("minimap_base64", ""),
            }
        )

    riot_id = payload.get("riot_id") or ""
    match_id = payload.get("match_id") or ""
    player_map = payload.get("player_map") or {}

    body = {"riot_id": riot_id, "events": events, "match_id": match_id, "player_map": player_map}

    # Warmup: acorda o Render (cold start pode levar 30-60s)
    try:
        logger.info("Acordando backend (warmup)...")
        async with httpx.AsyncClient(timeout=60.0) as warmup:
            await warmup.get(f"{BACKEND_URL}/")
        logger.info("Backend respondeu - enviando upload...")
    except Exception:
        logger.warning("Warmup falhou - tentando upload mesmo assim...")

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/local/upload",
                json=body,
                headers=headers,
            )
            if resp.status_code == 401:
                logger.error("Upload rejeitado: LOCAL_APP_TOKEN invalido ou ausente (401 Unauthorized)")
                return None
            if resp.status_code == 500:
                logger.error("Erro no servidor backend (500): %s", resp.text)
                return None
            resp.raise_for_status()
            logger.info("Upload aceito: %s", resp.json())
            return riot_id
    except httpx.ConnectError:
        logger.error("Nao conseguiu conectar ao backend - servidor pode estar dormindo (Render cold start)")
        return None
    except httpx.TimeoutException:
        logger.error("Timeout ao enviar upload (90s) - servidor pode estar sobrecarregado")
        return None
    except Exception as e:
        logger.error("Erro no upload: %s", e)
        return None


async def _poll_status(riot_id: str, tray: TrayIcon) -> None:
    """Faz polling ate analise estar pronta, entao muda icone para verde."""
    headers = _build_auth_headers()
    if not headers:
        logger.error("Polling abortado: LOCAL_APP_TOKEN/APP_TOKEN nao configurado.")
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(60):  # maximo 10 minutos (60 * 10s)
            await asyncio.sleep(POLL_INTERVAL)
            try:
                resp = await client.get(
                    f"{BACKEND_URL}/local/status",
                    params={"riot_id": riot_id},
                    headers=headers,
                )
                data = resp.json()
                logger.info("[poll %s/60] riot_id=%s status=%s", attempt + 1, riot_id, data)
                if data.get("ready"):
                    logger.info("Analise pronta! match_id=%s", data.get("match_id"))
                    tray.set_state("ready")
                    return
            except Exception as e:
                logger.debug("Erro ao checar status: %s", e)
    logger.warning("Timeout aguardando analise - icone mantido em uploading.")


async def coach_loop(tray: TrayIcon, stop_event: threading.Event, event_bus: EventBus) -> None:
    """Loop principal: aguarda jogo -> grava -> envia -> poll."""
    while not stop_event.is_set():
        logger.info("Aguardando LoL iniciar...")
        tray.set_state("waiting")
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "waiting"}))

        session = LiveCoachSession()
        try:
            await session.start()
        except Exception as e:
            logger.error("Erro ao iniciar sessao: %s", e)
            event_bus.emit(Event(EventType.ERROR, {"message": str(e)}))
            await asyncio.sleep(10.0)
            continue

        while session.is_running and not stop_event.is_set():
            active = getattr(session, "_player_name", None)
            if active:
                champion = getattr(session, "_player_champion", None) or ""
                tray.set_state("recording", detail=champion)
                event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "recording", "champion": champion, "riot_id": active}))
            await asyncio.sleep(1.0)

        if stop_event.is_set():
            await session.stop()
            break

        logger.info("Partida encerrada. Iniciando upload...")
        tray.set_state("uploading")
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "uploading"}))

        riot_id = await _upload(session, tray)
        if riot_id:
            event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "uploading", "riot_id": riot_id}))
            await _poll_status(riot_id, tray)
            event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "ready", "riot_id": riot_id}))
        else:
            tray.set_state("waiting")

        await asyncio.sleep(5.0)


def _run_async_loop(tray: TrayIcon, stop_event: threading.Event, event_bus: EventBus) -> None:
    """Roda o loop asyncio em thread separada."""
    asyncio.run(coach_loop(tray, stop_event, event_bus))


def _try_get_lcu_riot_id() -> str:
    """Try LCU API (client open, no game needed) for current summoner riot_id."""
    import subprocess, re
    try:
        ps_cmd = (
            "Get-CimInstance Win32_Process -Filter \"Name='LeagueClientUx.exe'\" "
            "| Select-Object -ExpandProperty CommandLine"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        cmdline = result.stdout
        if not cmdline or "LeagueClientUx" not in cmdline:
            return ""

        port_m = re.search(r"--app-port=(\d+)", cmdline)
        token_m = re.search(r"--remoting-auth-token=([\w_-]+)", cmdline)
        if not port_m or not token_m:
            return ""

        port = port_m.group(1)
        token = token_m.group(1)

        import httpx as _httpx
        with _httpx.Client(verify=False, timeout=2.0, auth=("riot", token)) as c:
            resp = c.get(f"https://127.0.0.1:{port}/lol-summoner/v1/current-summoner")
            if resp.status_code == 200:
                data = resp.json()
                name = data.get("gameName", "")
                tag = data.get("tagLine", "")
                if name and tag:
                    return f"{name}#{tag}"
    except Exception:
        pass
    return ""


def _play_detect_sound():
    """Play a short success sound when account is detected."""
    try:
        import winsound
        # Two-tone ascending chime: short beep then higher beep
        winsound.Beep(600, 150)
        winsound.Beep(900, 200)
    except Exception:
        pass


def main() -> None:
    stop_event = threading.Event()
    event_bus = EventBus()
    _current_riot_id = {"value": ""}

    # 1. Create CTk window on main thread
    app = ctk.CTk()
    app.title("MVPApp")
    app.geometry("450x600")
    app.resizable(False, False)

    # 2. Custom window icon
    if os.path.exists(_LOGO_PATH):
        _icon_pil = Image.open(_LOGO_PATH).resize((64, 64), Image.Resampling.LANCZOS)
        _icon_photo = ImageTk.PhotoImage(_icon_pil)
        app._iconbitmap_method_called = True
        app.iconphoto(True, _icon_photo)
        app._icon_ref = _icon_photo

    # Load logo once
    _logo_pil = None
    if os.path.exists(_LOGO_PATH):
        _logo_pil = Image.open(_LOGO_PATH)

    # ─── SCREEN 1: Account Detection ───────────────────────────
    _detect_frame = ctk.CTkFrame(app, fg_color="transparent")
    _detect_frame.pack(fill="both", expand=True)

    if _logo_pil:
        _d_logo = ctk.CTkImage(light_image=_logo_pil, dark_image=_logo_pil, size=(200, 133))
        ctk.CTkLabel(_detect_frame, text="", image=_d_logo).pack(pady=(60, 15))

    _detect_label = ctk.CTkLabel(
        _detect_frame, text="🔍  Detectando conta...",
        font=ctk.CTkFont(size=20, weight="bold"),
    )
    _detect_label.pack(pady=(10, 5))

    _detect_sub = ctk.CTkLabel(
        _detect_frame, text="Abra o League of Legends para continuar",
        font=ctk.CTkFont(size=13), text_color="gray50",
    )
    _detect_sub.pack(pady=(0, 15))

    _detect_nick = ctk.CTkLabel(
        _detect_frame, text="",
        font=ctk.CTkFont(size=18, weight="bold"), text_color="#4ade80",
    )

    _detect_spinner = ctk.CTkProgressBar(_detect_frame, width=200, mode="indeterminate")
    _detect_spinner.pack(pady=10)
    _detect_spinner.start()

    _detect_skip_btn = ctk.CTkButton(
        _detect_frame, text="Pular detecção", command=lambda: _show_main_screen(""),
        font=ctk.CTkFont(size=12), height=30,
        fg_color="transparent", hover_color="gray25", text_color="gray50",
    )
    _detect_skip_btn.pack(pady=(25, 0))

    # ─── SCREEN 2: Main App ───────────────────────────────────
    _main_frame = ctk.CTkFrame(app, fg_color="transparent")

    # Logo — small at top
    if _logo_pil:
        _m_logo = ctk.CTkImage(light_image=_logo_pil, dark_image=_logo_pil, size=(120, 80))
        ctk.CTkLabel(_main_frame, text="", image=_m_logo).pack(pady=(10, 2))

    # Nick section — clickable profile link (packed directly, no extra frame)
    _nick_btn = ctk.CTkButton(
        _main_frame, text="",
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="gray20", hover_color="gray25", text_color="#4ade80",
        height=32, corner_radius=8,
        command=lambda: _open_profile(),
    )

    def _open_profile():
        import webbrowser
        rid = _current_riot_id["value"]
        if rid and "#" in rid:
            name, tag = rid.split("#", 1)
            webbrowser.open(f"{SITE_URL}/summoner/{name}/{tag}")

    # Status section
    _status_frame = ctk.CTkFrame(_main_frame, fg_color="transparent")
    _status_frame.pack(pady=(3, 3))

    _status_dot = ctk.CTkLabel(
        _status_frame, text="●", font=ctk.CTkFont(size=18),
        text_color="#787878", width=24,
    )
    _status_dot.pack(side="left", padx=(0, 6))

    _status_label = ctk.CTkLabel(
        _status_frame, text="Aguardando LoL...",
        font=ctk.CTkFont(size=16, weight="bold"),
    )
    _status_label.pack(side="left")

    def _update_status_ui(state: str, detail: str = ""):
        """Update status dot and label + auto-hide on recording."""
        label = _STATUS_LABELS.get(state, state)
        if detail:
            label = f"{label} ({detail})"
        color = _COLORS.get(state, (120, 120, 120, 255))
        hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
        _status_dot.configure(text_color=hex_color)
        _status_label.configure(text=label)

        if state == "recording":
            if app.state() != "withdrawn":
                app.withdraw()
                logger.info("Janela ocultada automaticamente durante gravação")
        elif state in ("uploading", "ready", "waiting"):
            if app.state() == "withdrawn":
                app.deiconify()
                app.lift()
                logger.info("Janela restaurada após gravação")

    # Separator
    ctk.CTkFrame(_main_frame, height=2, fg_color="gray30").pack(fill="x", padx=30, pady=(8, 8))

    # Options section
    _opts_frame = ctk.CTkFrame(_main_frame, fg_color="transparent")
    _opts_frame.pack(fill="x", padx=40)

    cfg = get_config()
    _minimap_left_var = ctk.BooleanVar(value=cfg.get("minimap_left", False))
    _minimap_large_var = ctk.BooleanVar(value=cfg.get("minimap_large", False))

    def _on_toggle_left():
        update_config("minimap_left", _minimap_left_var.get())

    _sw_left = ctk.CTkSwitch(
        _opts_frame, text="Minimapa à esquerda",
        variable=_minimap_left_var, command=_on_toggle_left,
        font=ctk.CTkFont(size=14),
    )
    _sw_left.pack(anchor="w", pady=4)

    _sw_large = ctk.CTkSwitch(
        _opts_frame, text="Minimapa grande",
        variable=_minimap_large_var,
        command=lambda: update_config("minimap_large", _minimap_large_var.get()),
        font=ctk.CTkFont(size=14),
    )
    _sw_large.pack(anchor="w", pady=(4, 0))

    ctk.CTkLabel(
        _opts_frame, text="⭐ Recomendado para precisão da IA",
        font=ctk.CTkFont(size=11, slant="italic"), text_color="gray50",
    ).pack(anchor="w", padx=(52, 0), pady=(0, 2))

    ctk.CTkLabel(
        _opts_frame, text="📐  Tamanho recomendado do minimapa no LoL: 50",
        font=ctk.CTkFont(size=12), text_color="#4a9ed4",
    ).pack(anchor="w", padx=(8, 0), pady=(0, 3))

    # Separator
    ctk.CTkFrame(_main_frame, height=2, fg_color="gray30").pack(fill="x", padx=30, pady=(8, 8))

    # Action buttons
    _btns_frame = ctk.CTkFrame(_main_frame, fg_color="transparent")
    _btns_frame.pack(fill="x", padx=40)

    def _open_analysis():
        import webbrowser
        rid = _current_riot_id["value"]
        if rid and "#" in rid:
            name, tag = rid.split("#", 1)
            webbrowser.open(f"{SITE_URL}/summoner/{name}/{tag}")
        else:
            webbrowser.open(SITE_URL)

    ctk.CTkButton(
        _btns_frame, text="🔍  Ver análise", command=_open_analysis,
        font=ctk.CTkFont(size=14), height=40,
        fg_color="#4a9ed4", hover_color="#3a8ec4",
    ).pack(fill="x", pady=4)

    _btn_quit = ctk.CTkButton(
        _btns_frame, text="Sair", command=lambda: None,
        font=ctk.CTkFont(size=14), height=36,
        fg_color="gray30", hover_color="#b03030", text_color="gray70",
    )
    _btn_quit.pack(fill="x", pady=(4, 0))

    # "Como funciona" help button
    def _show_how_it_works():
        _help_win = ctk.CTkToplevel(app)
        _help_win.title("Como funciona")
        _help_win.geometry("420x380")
        _help_win.resizable(False, False)
        _help_win.attributes("-topmost", True)
        _help_win.grab_set()

        ctk.CTkLabel(
            _help_win, justify="left", wraplength=380,
            font=ctk.CTkFont(size=13),
            text=(
                "🎮  Como funciona o MVPApp\n\n"
                "1. Abra o League of Legends e inicie uma partida\n\n"
                "2. O MVPApp detecta automaticamente o jogo\n"
                "   e começa a gravar eventos (kills, mortes,\n"
                "   objetivos) com prints do minimapa\n\n"
                "3. Ao final da partida, os dados são enviados\n"
                "   para a IA analisar seu desempenho\n\n"
                "4. Clique em \"Ver análise\" para ver o coaching\n"
                "   personalizado no site mvpgg.vercel.app\n\n"
                "💡 Dica: Deixe o app aberto em segundo plano.\n"
                "   Ele funciona no tray (bandeja do sistema)."
            ),
        ).pack(padx=20, pady=20, anchor="w")

        ctk.CTkButton(
            _help_win, text="Entendi!", command=_help_win.destroy,
            font=ctk.CTkFont(size=14), height=36,
        ).pack(pady=(0, 15))

    ctk.CTkButton(
        _btns_frame, text="❓  Como funciona", command=_show_how_it_works,
        font=ctk.CTkFont(size=12), height=28,
        fg_color="transparent", hover_color="gray25", text_color="gray50",
        border_width=1, border_color="gray35",
    ).pack(fill="x", pady=(6, 0))

    # ─── Screen transition logic ────────────────────────────────
    def _show_main_screen(riot_id: str):
        """Switch from detection screen to main screen."""
        _detect_spinner.stop()
        _detect_frame.pack_forget()

        _current_riot_id["value"] = riot_id
        if riot_id:
            _nick_btn.configure(text=f"🎮  {riot_id}  →")
            _nick_btn.pack(padx=60, pady=(2, 2), fill="x")

        _main_frame.pack(fill="both", expand=True)

    def _detection_loop():
        """Background thread: poll LCU until account detected or timeout."""
        import time
        time.sleep(1)  # Small delay so detection screen is visible
        for _ in range(30):
            rid = _try_get_lcu_riot_id()
            if rid:
                app.after(0, lambda r=rid: _on_account_detected(r))
                return
            time.sleep(3)
        app.after(0, lambda: _show_main_screen(""))

    def _on_account_detected(riot_id: str):
        """Show welcome screen briefly then transition to main."""
        _detect_spinner.stop()
        _detect_spinner.pack_forget()
        _detect_skip_btn.pack_forget()
        _detect_label.configure(text="✅  Conta detectada!")
        _detect_sub.configure(
            text=f"Seja bem-vindo(a)!",
            font=ctk.CTkFont(size=14),
            text_color="gray60",
        )
        _detect_nick.configure(text=f"🎮  {riot_id}")
        _detect_nick.pack(pady=(10, 0))
        # Play success chime in background thread
        threading.Thread(target=_play_detect_sound, daemon=True).start()
        app.after(2500, lambda: _show_main_screen(riot_id))

    # Center on screen
    app.update_idletasks()
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    w, h = app.winfo_width(), app.winfo_height()
    app.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # Start account detection in background
    threading.Thread(target=_detection_loop, daemon=True).start()

    # Show/restore window function
    def show_window():
        app.deiconify()
        app.lift()
        app.focus_force()
        tray.remove_notification()

    # Close-to-tray handler
    def on_close_to_tray():
        app.withdraw()
        cfg = get_config()
        if not cfg.get("hide_tray_notification", False):
            tray.notify("MVPApp continua rodando no tray")

    app.protocol("WM_DELETE_WINDOW", on_close_to_tray)

    # Quit handler
    def on_quit():
        logger.info("Encerrando CoachApp...")
        stop_event.set()
        app.after(0, app.quit)

    _btn_quit.configure(command=on_quit)

    # Tray
    def on_show_from_tray():
        app.after(0, show_window)

    tray = TrayIcon(on_quit=on_quit, on_show=on_show_from_tray)
    tray.run_detached()

    # Asyncio loop
    async_thread = threading.Thread(
        target=_run_async_loop,
        args=(tray, stop_event, event_bus),
        daemon=True,
    )
    async_thread.start()

    # EventBus listener — update window status + track riot_id
    def _on_state_event(event: Event):
        state = event.data.get("state", "waiting")
        detail = event.data.get("champion", "")
        rid = event.data.get("riot_id", "")
        if rid:
            _current_riot_id["value"] = rid
            # Update nick button if it was empty
            app.after(0, lambda: _nick_btn.configure(text=f"🎮  {rid}  →"))
            if not _nick_btn.winfo_ismapped():
                app.after(0, lambda: _nick_btn.pack(pady=(0, 5)))
        app.after(0, lambda: _update_status_ui(state, detail))

    event_bus.subscribe(EventType.STATE_CHANGE, _on_state_event)
    event_bus.start_polling(app)

    # Enter main loop
    app.mainloop()

    # Cleanup
    tray.stop()
    async_thread.join(timeout=5.0)
    try:
        app.destroy()
    except Exception:
        pass
    logger.info("CoachApp encerrado.")


if __name__ == "__main__":
    main()
