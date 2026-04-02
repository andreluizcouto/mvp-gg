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
from app_config import get_config
from event_bus import EventBus, EventType, Event
from live_coach import LiveCoachSession
from tray_icon import TrayIcon

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
                event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "recording", "champion": champion}))
            await asyncio.sleep(1.0)

        if stop_event.is_set():
            await session.stop()
            break

        logger.info("Partida encerrada. Iniciando upload...")
        tray.set_state("uploading")
        event_bus.emit(Event(EventType.STATE_CHANGE, {"state": "uploading"}))

        riot_id = await _upload(session, tray)
        if riot_id:
            await _poll_status(riot_id, tray)
        else:
            tray.set_state("waiting")

        await asyncio.sleep(5.0)


def _run_async_loop(tray: TrayIcon, stop_event: threading.Event, event_bus: EventBus) -> None:
    """Roda o loop asyncio em thread separada."""
    asyncio.run(coach_loop(tray, stop_event, event_bus))


def main() -> None:
    stop_event = threading.Event()
    event_bus = EventBus()

    # 1. Create CTk window on main thread (MUST be main thread)
    app = ctk.CTk()
    app.title("MVPApp")
    app.geometry("450x600")
    app.resizable(False, False)

    # 2. Custom window icon (prevent CTk's 200ms default icon override)
    if os.path.exists(_LOGO_PATH):
        _icon_pil = Image.open(_LOGO_PATH).resize((64, 64), Image.Resampling.LANCZOS)
        _icon_photo = ImageTk.PhotoImage(_icon_pil)
        app._iconbitmap_method_called = True
        app.iconphoto(True, _icon_photo)
        app._icon_ref = _icon_photo  # prevent GC

    # 3. Logo branding in window
    if os.path.exists(_LOGO_PATH):
        _logo_pil = Image.open(_LOGO_PATH)
        _logo_ctk = ctk.CTkImage(light_image=_logo_pil, dark_image=_logo_pil, size=(280, 187))
        _logo_label = ctk.CTkLabel(app, text="", image=_logo_ctk)
        _logo_label.pack(pady=(30, 10))

    # 4. Center on screen
    app.update_idletasks()
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    w, h = app.winfo_width(), app.winfo_height()
    app.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # 5. Show/restore window function
    def show_window():
        """Restore window to foreground. MUST run on main thread."""
        app.deiconify()
        app.lift()
        app.focus_force()
        tray.remove_notification()

    # 6. Close-to-tray handler
    def on_close_to_tray():
        """WM_DELETE_WINDOW — hide to tray with optional notification."""
        app.withdraw()
        cfg = get_config()
        if not cfg.get("hide_tray_notification", False):
            tray.notify("MVPApp continua rodando no tray")

    app.protocol("WM_DELETE_WINDOW", on_close_to_tray)

    # 7. Quit handler
    def on_quit():
        """Called from any thread to initiate clean shutdown."""
        logger.info("Encerrando CoachApp...")
        stop_event.set()
        app.after(0, app.quit)

    # 8. Create and start tray on background thread
    def on_show_from_tray():
        """Called from pystray thread. Schedules show on main thread."""
        app.after(0, show_window)

    tray = TrayIcon(on_quit=on_quit, on_show=on_show_from_tray)
    tray.run_detached()

    # 9. Start asyncio loop on daemon thread
    async_thread = threading.Thread(
        target=_run_async_loop,
        args=(tray, stop_event, event_bus),
        daemon=True,
    )
    async_thread.start()

    # 10. Start EventBus polling (bridges queue → main thread)
    event_bus.start_polling(app)

    # 11. Enter main loop (blocks until app.quit())
    app.mainloop()

    # 12. Cleanup after mainloop exits
    tray.stop()
    async_thread.join(timeout=5.0)
    try:
        app.destroy()
    except Exception:
        pass  # Window may already be destroyed
    logger.info("CoachApp encerrado.")


if __name__ == "__main__":
    main()
