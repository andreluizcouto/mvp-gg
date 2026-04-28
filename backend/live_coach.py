"""
Orquestrador de coaching ao vivo: detecta mortes, kills, multi-kills e
objetivos via polling, captura minimapa e salva prints em disco para
analise pos-partida em lote.
"""
import asyncio
import base64
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from live_game_client import LiveGameClient
from minimap_capture import capture_minimap, get_screen_resolution, save_minimap_to_disk

logger = logging.getLogger(__name__)

DEATH_POLL_INTERVAL = 0.3   # polling agressivo para morte (300ms)
EVENT_POLL_TICKS = 1        # tick de eventos a cada N ticks de morte (~300ms)


# ──────────────────────────────────────────
# Tipos de evento
# ──────────────────────────────────────────

EVENT_DEATH = "death"
EVENT_KILL = "kill"
EVENT_MULTIKILL = "multikill"
EVENT_BARON = "baron"
EVENT_DRAGON = "dragon"
EVENT_HERALD = "herald"
EVENT_TURRET = "turret"

_MULTIKILL_NAMES = {2: "Double Kill", 3: "Triple Kill", 4: "Quadra Kill", 5: "Penta Kill"}


@dataclass
class LiveEvent:
    event_type: str
    timestamp_sec: float
    summoner_name: str
    champion: str
    detail: str = ""
    killer: Optional[str] = None
    victim: Optional[str] = None
    assisters: list[str] = field(default_factory=list)
    objective_stolen: bool = False
    minimap_path: Optional[str] = None
    captured_at: datetime = field(default_factory=datetime.now)

    def game_time_str(self) -> str:
        m = int(self.timestamp_sec // 60)
        s = int(self.timestamp_sec % 60)
        return f"{m:02d}:{s:02d}"

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "timestamp_sec": self.timestamp_sec,
            "game_time": self.game_time_str(),
            "summoner_name": self.summoner_name,
            "champion": self.champion,
            "detail": self.detail,
            "killer": self.killer,
            "victim": self.victim,
            "assisters": self.assisters,
            "objective_stolen": self.objective_stolen,
            "minimap_path": self.minimap_path,
            "captured_at": self.captured_at.isoformat(),
        }


class LiveCoachSession:
    """
    Mantém um loop de polling que detecta eventos relevantes do jogador
    e salva prints de minimapa em disco para análise pós-partida.
    """

    def __init__(self):
        self.events_queue: asyncio.Queue[LiveEvent] = asyncio.Queue()
        self._running = False
        self._was_dead = False
        self._task: Optional[asyncio.Task] = None
        self._screen_size: Optional[tuple[int, int]] = None
        self.event_history: list[LiveEvent] = []
        self._processed_event_ids: set[int] = set()
        self._player_name: Optional[str] = None
        self._player_champion: Optional[str] = None
        self._player_team: Optional[str] = None          # "ORDER" ou "CHAOS"
        self._name_to_champion: dict[str, str] = {}      # summoner → champion
        self._name_to_team: dict[str, str] = {}           # summoner → "ORDER"/"CHAOS"
        self._prints_dir: str = ""
        self._puuid: Optional[str] = None
        self._match_start_ids: list[str] = []
        self._finished_match_id: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def finished_match_id(self) -> Optional[str]:
        return self._finished_match_id

    @property
    def prints_dir(self) -> str:
        return self._prints_dir

    def get_postgame_payload(self) -> Optional[dict]:
        """Retorna os dados para upload pos-game, ou None se nao ha dados."""
        if not self._finished_match_id or not self.event_history:
            return None

        events = []
        image_paths = []
        for evt in self.event_history:
            evt_data = evt.to_dict()
            if evt.minimap_path and os.path.exists(evt.minimap_path):
                with open(evt.minimap_path, "rb") as f:
                    evt_data["minimap_base64"] = base64.b64encode(f.read()).decode()
                image_paths.append(evt.minimap_path)
            events.append(evt_data)

        return {
            "riot_id": self._player_name or "",
            "puuid": self._puuid or "",
            "match_id": self._finished_match_id,
            "events": events,
            "image_paths": image_paths,
            "player_map": self._name_to_champion,  # riot_id → champion name
        }

    async def start(self):
        if self._running:
            return
        self._running = True
        self._screen_size = get_screen_resolution()
        self._prints_dir = os.path.join(
            tempfile.gettempdir(),
            "lol_coach_prints",
            datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        os.makedirs(self._prints_dir, exist_ok=True)
        logger.info(f"Prints serao salvos em: {self._prints_dir}")
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("LiveCoachSession iniciada")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("LiveCoachSession encerrada")

    # ──────────────────────────────────────────
    # Loop principal — dual polling
    # ──────────────────────────────────────────

    async def _poll_loop(self):
        async with LiveGameClient() as client:
            while self._running:
                if await client.is_game_active():
                    break
                logger.debug("Jogo nao detectado, aguardando...")
                await asyncio.sleep(2.0)

            logger.info("Jogo detectado — identificando jogador...")
            await self._identify_player(client)
            logger.info(f"Jogador: {self._player_name} ({self._player_champion})")

            api_key = os.getenv("RIOT_API_KEY", "")
            if api_key and self._player_name and "#" in self._player_name:
                game_name, tag_line = self._player_name.split("#", 1)
                self._puuid = await client.get_puuid_from_riot_id(game_name, tag_line, api_key)
                if self._puuid:
                    self._match_start_ids = await client.get_recent_match_ids(self._puuid, api_key)
                    logger.info(f"PUUID: {self._puuid[:8]}... | Match IDs pre-jogo: {len(self._match_start_ids)}")
                else:
                    logger.warning("Não foi possível obter PUUID — detecção de match ID desativada")
            elif not api_key:
                logger.info("RIOT_API_KEY não configurada — backend detectará o match ID via riot_id")
            

            logger.info("Polling de eventos iniciado")

            death_counter = 0
            null_ticks = 0          # ticks consecutivos sem resposta do Live Client
            NULL_TICK_LIMIT = 10    # ~3s sem resposta = jogo provavelmente encerrou
            while self._running:
                try:
                    player = await client.get_active_player_with_status()
                    if player is None:
                        null_ticks += 1
                        if null_ticks >= NULL_TICK_LIMIT:
                            logger.info("Live Client sem resposta por 3s — verificando fim de partida...")
                            await self._check_game_ended(client)
                            if not self._running:
                                break
                            null_ticks = 0
                    else:
                        null_ticks = 0
                        is_dead = player.get("isDead", False)
                        if is_dead and not self._was_dead:
                            asyncio.create_task(self._handle_death(client, player))
                        self._was_dead = is_dead
                        death_counter += 1
                        if death_counter >= EVENT_POLL_TICKS:
                            death_counter = 0
                            await self._tick_events(client)
                except Exception as e:
                    logger.error(f"Erro no tick de polling: {e}")
                await asyncio.sleep(DEATH_POLL_INTERVAL)

    async def _finalize_match(self):
        """Chamado quando GameEnd é detectado — busca match ID rapidamente e finaliza."""
        if not self._puuid:
            logger.info(f"Finalizando via riot_id={self._player_name}")
            self._finished_match_id = f"pending_{(self._player_name or 'unknown').replace('#', '_')}"
            self._running = False
            return

        api_key = os.getenv("RIOT_API_KEY", "")
        # Riot API pode levar alguns segundos pra registrar a partida
        for attempt in range(4):
            await asyncio.sleep(5.0)
            try:
                current_ids = await LiveGameClient().get_recent_match_ids(self._puuid, api_key)
                new_id = next((mid for mid in current_ids if mid not in self._match_start_ids), None)
                if new_id:
                    logger.info(f"Match ID encontrado: {new_id}")
                    self._finished_match_id = new_id
                    self._running = False
                    return
                logger.info(f"Match ID ainda não disponível, tentativa {attempt+1}/4...")
            except Exception as e:
                logger.warning(f"Erro ao buscar match ID: {e}")

        # Fallback — bot game ou Riot API lenta
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_id = f"local_{ts}"
        logger.warning(f"Match ID não encontrado — usando fallback: {fallback_id}")
        self._finished_match_id = fallback_id
        self._running = False

    async def _check_game_ended(self, client: LiveGameClient):
        """Fallback: quando Live Client desconecta sem GameEnd event."""
        if not self._player_name:
            logger.warning("Sem player_name — marcando partida como finalizada sem match ID")
            self._finished_match_id = f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._running = False
            return

        # Sem PUUID: backend resolve via riot_id
        if not self._puuid:
            retries = 0
            while retries < 5:
                if await client.is_game_active():
                    logger.info("Live Client voltou — jogo ainda ativo")
                    return
                await asyncio.sleep(3.0)
                retries += 1
            logger.info(f"Partida finalizada. Backend resolverá via riot_id={self._player_name}")
            self._finished_match_id = f"pending_{self._player_name.replace('#', '_')}"
            self._running = False
            return

        api_key = os.getenv("RIOT_API_KEY", "")
        for retries in range(5):
            if await client.is_game_active():
                logger.info("Live Client voltou — jogo ainda ativo")
                return
            await asyncio.sleep(3.0)

            current_ids = await client.get_recent_match_ids(self._puuid, api_key)
            new_id = next((mid for mid in current_ids if mid not in self._match_start_ids), None)
            if new_id:
                logger.info(f"Partida finalizada! Match ID: {new_id}")
                self._finished_match_id = new_id
                self._running = False
                return

        # Fallback
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_id = f"local_{ts}"
        logger.warning(f"Match ID não encontrado — usando fallback: {fallback_id}")
        self._finished_match_id = fallback_id
        self._running = False

    def _resolve_champion(self, summoner_name: str) -> str:
        """Converte summoner name para champion name; retorna o proprio nome se nao encontrar."""
        return self._name_to_champion.get(summoner_name, summoner_name)

    def _resolve_champions(self, names: list[str]) -> list[str]:
        return [self._resolve_champion(n) for n in names]

    def _is_ally(self, summoner_name: str) -> bool:
        return self._name_to_team.get(summoner_name) == self._player_team

    async def _identify_player(self, client: LiveGameClient):
        """Identifica nome e campeão do jogador local + monta mapeamento de todos os players."""
        active = await client.get_active_player()
        if active:
            self._player_name = active.get("riotId") or active.get("summonerName", "")

        player_list = await client.get_player_list()
        for p in player_list:
            pid = p.get("riotId") or p.get("summonerName", "")
            champ = p.get("championName", "")
            team = p.get("team", "")
            self._name_to_champion[pid] = champ
            self._name_to_team[pid] = team
            if pid == self._player_name:
                self._player_champion = champ
                self._player_team = team

    # ──────────────────────────────────────────
    # Tick de eventos (300ms efetivo)
    # ──────────────────────────────────────────

    async def _tick_events(self, client: LiveGameClient):
        events = await client.get_events()
        game_stats = await client.get_game_stats()
        game_time = game_stats.get("gameTime", 0.0) if game_stats else 0.0

        for i, evt in enumerate(events):
            if i in self._processed_event_ids:
                continue

            event_name = evt.get("EventName", "")
            killer = evt.get("KillerName", "")

            # Detecta fim de partida via evento GameEnd
            if event_name == "GameEnd":
                self._processed_event_ids.add(i)
                logger.info("GameEnd detectado via eventos — partida acabou!")
                await self._finalize_match()
                return

            if event_name == "ChampionKill" and self._is_local_player(killer):
                self._processed_event_ids.add(i)
                victim = evt.get("VictimName", "")
                assisters = evt.get("Assisters", [])
                asyncio.create_task(self._handle_kill(
                    game_time=evt.get("EventTime", game_time),
                    victim=victim,
                    assisters=assisters,
                ))

            elif event_name == "Multikill" and self._is_local_player(killer):
                self._processed_event_ids.add(i)
                streak = evt.get("KillStreak", 2)
                asyncio.create_task(self._handle_multikill(
                    game_time=evt.get("EventTime", game_time),
                    streak=streak,
                ))

            # Objetivos: captura de QUALQUER time
            elif event_name == "DragonKill":
                self._processed_event_ids.add(i)
                stolen = bool(evt.get("Stolen", False))
                dragon_type = evt.get("DragonType", "")
                obj_killer = evt.get("KillerName", "")
                ally = self._is_ally(obj_killer)
                team_tag = "time aliado" if ally else "time inimigo"
                stolen_tag = " — ROUBADO" if stolen else ""
                asyncio.create_task(self._handle_objective(
                    event_type=EVENT_DRAGON,
                    game_time=evt.get("EventTime", game_time),
                    detail=f"Dragon {dragon_type} ({team_tag}{stolen_tag})",
                    stolen=stolen,
                ))

            elif event_name == "BaronKill":
                self._processed_event_ids.add(i)
                stolen = bool(evt.get("Stolen", False))
                obj_killer = evt.get("KillerName", "")
                ally = self._is_ally(obj_killer)
                team_tag = "time aliado" if ally else "time inimigo"
                stolen_tag = " — ROUBADO" if stolen else ""
                asyncio.create_task(self._handle_objective(
                    event_type=EVENT_BARON,
                    game_time=evt.get("EventTime", game_time),
                    detail=f"Baron Nashor ({team_tag}{stolen_tag})",
                    stolen=stolen,
                ))

            elif event_name == "HeraldKill":
                self._processed_event_ids.add(i)
                stolen = bool(evt.get("Stolen", False))
                obj_killer = evt.get("KillerName", "")
                ally = self._is_ally(obj_killer)
                team_tag = "time aliado" if ally else "time inimigo"
                stolen_tag = " — ROUBADO" if stolen else ""
                asyncio.create_task(self._handle_objective(
                    event_type=EVENT_HERALD,
                    game_time=evt.get("EventTime", game_time),
                    detail=f"Rift Herald ({team_tag}{stolen_tag})",
                    stolen=stolen,
                ))

            elif event_name == "TurretKilled":
                self._processed_event_ids.add(i)
                turret_name = evt.get("TurretKilled", "")
                asyncio.create_task(self._handle_objective(
                    event_type=EVENT_TURRET,
                    game_time=evt.get("EventTime", game_time),
                    detail=f"Turret {turret_name}" if turret_name else "Turret",
                    stolen=False,
                ))

    def _is_local_player(self, name: str) -> bool:
        if not self._player_name:
            return False
        return name == self._player_name or name == self._player_name.split("#")[0]

    # ──────────────────────────────────────────
    # Handlers de eventos
    # ──────────────────────────────────────────

    async def _capture_and_save(self, event_type: str, game_time_sec: float) -> str:
        width, height = self._screen_size
        # Lê config se app_config disponível (app local); usa defaults no servidor
        try:
            from app_config import get_config
            cfg = get_config()
        except ImportError:
            cfg = {"minimap_left": False, "minimap_large": False}
        img = capture_minimap(
            width, height,
            minimap_left=cfg["minimap_left"],
            minimap_large=cfg["minimap_large"],
        )
        return save_minimap_to_disk(img, self._prints_dir, event_type, game_time_sec)

    async def _emit(self, event: LiveEvent):
        self.event_history.append(event)
        await self.events_queue.put(event)

    async def _handle_death(self, client: LiveGameClient, player: dict):
        logger.info(f"MORTE detectada: {self._player_champion}")

        events = await client.get_events()
        game_stats = await client.get_game_stats()
        game_time = game_stats.get("gameTime", 0.0) if game_stats else 0.0

        try:
            png_path = await self._capture_and_save(EVENT_DEATH, game_time)
        except Exception as e:
            logger.warning(f"Falha ao capturar minimapa: {e}")
            png_path = None
        kill_event = self._find_kill_event(events, game_time)

        raw_killer = kill_event.get("KillerName") if kill_event else None
        raw_assisters = kill_event.get("Assisters", []) if kill_event else []

        event = LiveEvent(
            event_type=EVENT_DEATH,
            timestamp_sec=game_time,
            summoner_name=self._player_name or "",
            champion=self._player_champion or "",
            detail="Morte",
            killer=self._resolve_champion(raw_killer) if raw_killer else None,
            assisters=self._resolve_champions(raw_assisters),
            minimap_path=png_path,
        )

        await self._emit(event)

    async def _handle_kill(self, game_time: float, victim: str, assisters: list[str]):
        victim_champ = self._resolve_champion(victim)
        logger.info(f"KILL detectada: {self._player_champion} matou {victim_champ}")
        try:
            png_path = await self._capture_and_save(EVENT_KILL, game_time)
        except Exception as e:
            logger.warning(f"Falha ao capturar minimapa: {e}")
            png_path = None

        event = LiveEvent(
            event_type=EVENT_KILL,
            timestamp_sec=game_time,
            summoner_name=self._player_name or "",
            champion=self._player_champion or "",
            detail=f"Kill em {victim_champ}",
            victim=victim_champ,
            assisters=self._resolve_champions(assisters),
            minimap_path=png_path,
        )

        await self._emit(event)

    async def _handle_multikill(self, game_time: float, streak: int):
        name = _MULTIKILL_NAMES.get(streak, f"{streak}-kill")
        logger.info(f"MULTIKILL detectada: {self._player_champion} — {name}")
        try:
            png_path = await self._capture_and_save(EVENT_MULTIKILL, game_time)
        except Exception as e:
            logger.warning(f"Falha ao capturar minimapa: {e}")
            png_path = None

        event = LiveEvent(
            event_type=EVENT_MULTIKILL,
            timestamp_sec=game_time,
            summoner_name=self._player_name or "",
            champion=self._player_champion or "",
            detail=name,
            minimap_path=png_path,
        )

        await self._emit(event)

    async def _handle_objective(self, event_type: str, game_time: float, detail: str, stolen: bool):
        logger.info(f"OBJETIVO detectado: {detail}")
        try:
            png_path = await self._capture_and_save(event_type, game_time)
        except Exception as e:
            logger.warning(f"Falha ao capturar minimapa: {e}")
            png_path = None

        event = LiveEvent(
            event_type=event_type,
            timestamp_sec=game_time,
            summoner_name=self._player_name or "",
            champion=self._player_champion or "",
            detail=detail,
            objective_stolen=stolen,
            minimap_path=png_path,
        )

        await self._emit(event)

    def _find_kill_event(self, events: list[dict], game_time: float) -> Optional[dict]:
        """Encontra o evento ChampionKill mais recente onde o jogador local morreu."""
        recent = [
            e for e in events
            if e.get("EventName") == "ChampionKill"
            and self._is_local_player(e.get("VictimName", ""))
            and abs(e.get("EventTime", 0) - game_time) < 5
        ]
        return recent[-1] if recent else None
