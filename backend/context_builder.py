"""
context_builder.py - Preparador de Contexto para a IA
Transforma dados brutos e matemáticos da Riot em JSONs ricos e tipados.
O Gemini recebe esse JSON e faz a inferência e o feedback em linguagem natural.
"""

import logging
import math
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from riot_client import (
    MatchData, MatchTimeline, MatchParticipant,
    get_ward_events, get_kill_events,
)
from game_rules import (
    CS_BENCHMARKS, GANK_DETECTION_RADIUS, FIGHT_MIN_ENEMIES, TEAMFIGHT_MIN_ALLIES,
    OBJECTIVE_VISION_RADIUS, BARON_PIT, DRAGON_PIT, HERALD_PIT,
    GOLD_DEFICIT_THRESHOLD, STREAK_DEATH_COUNT, STREAK_TIME_WINDOW,
    STREAK_RECOVERY_TIME, RECALL_GOLD_THRESHOLD, RECALL_KILL_WINDOW,
    get_game_phase, get_minion_speed, LANE_LENGTH_TO_CENTER,
    MINION_SPAWN_TIME, get_wave_interval,
    NEXUS, BOOTS_ITEM_IDS, ANTIHEAL_ITEM_IDS,
)

logger = logging.getLogger(__name__)

# wardType → (duration_sec, vision_radius_units)
# duration_sec = -1 → permanente até ser destruída
_WARD_PROPS: dict[str, tuple[int, int]] = {
    "YELLOW_TRINKET": (90,  900),
    "SIGHT_WARD":     (90,  900),
    "CONTROL_WARD":   (-1,  900),
    "BLUE_TRINKET":   (-1,  500),
}
_WARD_PROPS_DEFAULT = (90, 900)


# ─────────────────────────────────────────
# Utilitário de distância
# ─────────────────────────────────────────

def _dist(ax: int, ay: int, bx: int, by: int) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _bounty_for_streak(streak: int) -> int:
    """Shutdown gold que o assassino recebe ao matar alguém com kill streak.
    Tabela baseada no sistema de bounty atual do LoL (2024/2025).
    streak=2 → 150g | streak=3 → 300g | streak=4+ → escala até 900g.
    """
    if streak <= 1:
        return 0
    return min((streak - 1) * 150, 900)


# ─────────────────────────────────────────
# Modelos Pydantic (Contratos de Dados)
# ─────────────────────────────────────────

class PlayerPosition(BaseModel):
    champion: str
    x: int
    y: int
    is_enemy: bool
    distance_to_player: float


class DeathContext(BaseModel):
    timestamp_sec: float
    game_phase: str
    player_x: int
    player_y: int
    killer_champion: Optional[str] = None
    assisters: List[str] = Field(default_factory=list)
    enemies_nearby: List[PlayerPosition] = Field(default_factory=list)
    allies_nearby: List[PlayerPosition] = Field(default_factory=list)
    death_type: str = "UNKNOWN"
    had_vision_of_killer: bool = False
    enemies_count: int = 0
    allies_count: int = 0
    gold_deficit_at_death: int = 0
    wave_state: Optional[str] = None   # PROXY (confidence LOW) — estimativa de ciclo de spawn
    is_early_death: bool = False       # True se morreu antes dos 3 minutos (first blood)
    # Campos de risco — calculados deterministicamente a partir de fatos da timeline/match
    risk_score: int = 0                # 0–10
    risk_reasons: List[str] = Field(default_factory=list)  # ex: ["NO_VISION","OUTNUMBERED"]
    risk_confidence: str = "HIGH"      # HIGH se todos inputs de match/timeline; MED se proxy
    kill_streak_before_death: int = 0  # kills consecutivas sem morrer antes desta morte
    bounty_gold_lost: int = 0          # shutdown gold cedido ao assassino (0 se streak <= 1)


class ObjectiveContext(BaseModel):
    objective_type: str
    timestamp_sec: float
    game_phase: str
    had_vision_on_pit: bool
    allies_nearby: int
    enemies_nearby: int
    killer_team: Optional[str] = None


class RecallContext(BaseModel):
    timestamp_sec: float
    game_phase: str
    gold_earned_last_minute: int
    had_recent_kill: bool
    had_vision_nearby: bool
    wave_state: Optional[str] = None
    is_questionable: bool


class GoldContext(BaseModel):
    timestamp_sec: float
    game_phase: str
    player_total_gold: int
    opponent_total_gold: int
    gold_diff: int
    gold_diff_severity: str = "OK"   # OK, MEDIUM, HIGH, CRITICAL (só negativo é ruim)
    xp_diff: int = 0                 # XP do jogador - XP do oponente de lane


class CSContext(BaseModel):
    phase: str
    cs_at_phase_end: int
    cs_per_min: float
    benchmark: int
    cs_diff_to_benchmark: float
    gold_lost_estimate: int


class DeathStreakContext(BaseModel):
    deaths_in_streak: int
    start_time_sec: float
    end_time_sec: float
    game_phase: str
    recovered: bool


class TowerEventContext(BaseModel):
    timestamp_sec: float
    game_phase: str
    tower_tier: str        # OUTER, INNER, BASE, NEXUS
    lane: str              # TOP, MID, BOT
    lost_by_ally: bool     # True = time do jogador perdeu a torre
    player_was_nearby: bool  # jogador estava em raio ~3000u do evento


class MultiKillContext(BaseModel):
    timestamp_sec: float
    game_phase: str
    kill_count: int        # 2=double, 3=triple, 4=quadra, 5=penta


class ItemTimelineEntry(BaseModel):
    """Entrada cronológica de evento de item do jogador."""
    t: float
    item_id: int
    action: str   # PURCHASED | SOLD | UNDO
    name: str     # Nome resolvido ou "UnknownItem(<id>)" — nunca descartado silenciosamente


class DataQuality(BaseModel):
    """Relatório de qualidade dos dados para o LLM calibrar sua confiança."""
    warnings: List[str] = Field(default_factory=list)
    items_resolved_ratio: float = 1.0   # 0.0–1.0; < 1.0 = itens sem nome no DDragon
    notes: Optional[str] = None


class MatchContext(BaseModel):
    match_id: str
    player_riot_id: str
    player_champion: str
    role: str
    win: bool
    duration_min: float
    kda: str
    cs_per_min: float
    vision_score: int
    kill_participation_pct: float
    damage_share_pct: float
    time_dead_pct: float
    rank: str = "DEFAULT"
    wards_placed: int = 0
    wards_killed: int = 0
    control_wards_placed: int = 0
    final_items: List[str] = Field(default_factory=list)
    summoner_spells: List[str] = Field(default_factory=list)
    deaths: List[DeathContext] = Field(default_factory=list)
    objectives: List[ObjectiveContext] = Field(default_factory=list)
    bad_recalls: List[RecallContext] = Field(default_factory=list)
    gold_curve: List[GoldContext] = Field(default_factory=list)
    cs_stats: List[CSContext] = Field(default_factory=list)
    death_streaks: List[DeathStreakContext] = Field(default_factory=list)
    # ── VOD Proxy JSON — campos adicionados ──────────────────────────────────────
    item_timeline: List[ItemTimelineEntry] = Field(default_factory=list)
    boots_purchase_time_sec: Optional[float] = None
    first_completed_item_time_sec: Optional[float] = None  # heurística: 1ª compra >=8 min, não-bota
    antiheal_purchase_time_sec: Optional[float] = None
    fact_log: List[dict] = Field(default_factory=list)      # linha do tempo cronológica tipada
    data_quality: Optional[DataQuality] = None
    confidence_overview: Optional[Dict[str, int]] = None    # contagem HIGH/MED/LOW no fact_log
    # ── Novos campos ────────────────────────────────────────────────────────────
    tower_events: List[TowerEventContext] = Field(default_factory=list)
    multi_kills: List[MultiKillContext] = Field(default_factory=list)
    kills_converted_to_objective: int = 0   # kills que geraram torre/objective em 90s
    kills_not_converted: int = 0
    kill_conversion_rate: float = 0.0


# ─────────────────────────────────────────
# Construtor de Contexto
# ─────────────────────────────────────────

class ContextBuilder:
    def __init__(self, target_puuid: str, rank: str = "DEFAULT"):
        self.target_puuid = target_puuid
        self.rank = rank.upper()
        self._cs_bench = CS_BENCHMARKS.get(self.rank, CS_BENCHMARKS["DEFAULT"])

        # Dicionários de lookup — construídos UMA VEZ em build() — O(1) nas buscas
        self._pid_to_team: Dict[int, int] = {}
        self._pid_to_champ: Dict[int, str] = {}
        self._puuid_to_pid: Dict[str, int] = {}
        self._player_pid: Optional[int] = None
        self._player_team: Optional[int] = None
        # Acumulador de warnings de qualidade — resetado a cada build()
        self._warnings: List[str] = []

    def build(self, match: MatchData, timeline: MatchTimeline, item_names: Dict[str, str] | None = None) -> MatchContext:
        """Método principal. Constrói os dicionários de lookup e orquestra as análises."""

        # Reset de estado por chamada
        self._warnings = []

        # ── Constrói todos os lookups UMA VEZ — corrige bug O(N³) ──
        for tl_p in timeline.participants:
            pid   = tl_p.get("participantId")
            puuid = tl_p.get("puuid")
            self._puuid_to_pid[puuid] = pid
            for mp in match.participants:
                if mp.puuid == puuid:
                    self._pid_to_team[pid]  = mp.team_id
                    self._pid_to_champ[pid] = mp.champion_name
                    break

        self._player_pid  = self._puuid_to_pid.get(self.target_puuid)
        self._player_team = self._pid_to_team.get(self._player_pid)

        player = self._find_player(match)
        if not player:
            raise ValueError(f"Jogador com PUUID {self.target_puuid} não encontrado.")

        opponent = self._find_lane_opponent(match, player)
        duration_min = match.game_duration / 60
        cs_per_min = player.creep_score / duration_min if duration_min > 0 else 0

        allies     = [p for p in match.participants if p.team_id == player.team_id]
        team_kills = sum(p.kills for p in allies)
        team_dmg   = sum(p.damage_dealt for p in allies)

        kp       = (player.kills + player.assists) / max(team_kills, 1) * 100
        ds       = player.damage_dealt / max(team_dmg, 1) * 100
        dead_pct = (player.time_spent_dead / match.game_duration) * 100 if match.game_duration > 0 else 0

        _item_names = item_names or {}

        # ── Item timeline (antes de resolver final_items para compartilhar warnings) ──
        item_tl, item_tl_warnings, boots_t, first_item_t, antiheal_t, items_ratio = \
            self._build_item_timeline(timeline, _item_names)
        self._warnings.extend(item_tl_warnings)

        # ── Objetivos primeiro — timestamps necessários para risk score das mortes ──
        objectives     = self._build_objectives(match, timeline)
        obj_timestamps = [o.timestamp_sec for o in objectives]

        # ── Kill streaks pré-computados (para bounty nas mortes) ──
        streak_map = self._compute_kill_streak_map(timeline)

        # ── Mortes com risk scores determinísticos e bounty ──
        deaths = self._build_deaths(match, timeline, player, opponent, obj_timestamps, streak_map)

        # ── Novos: torres, multi-kills, conversão de kills ──
        tower_events                     = self._build_tower_events(timeline)
        multi_kills                      = self._build_multi_kills(timeline)
        conv_yes, conv_no, conv_rate     = self._build_kill_conversion(timeline)

        # ── Fact log (linha do tempo cronológica — VOD proxy) ──
        fact_log = self._build_fact_log(timeline, deaths, objectives, item_tl)

        # ── Confidence overview ──
        conf_counts: Dict[str, int] = {"HIGH": 0, "MED": 0, "LOW": 0}
        for entry in fact_log:
            c = entry.get("confidence", "LOW")
            conf_counts[c] = conf_counts.get(c, 0) + 1

        data_quality = DataQuality(
            warnings=list(self._warnings),
            items_resolved_ratio=items_ratio,
        )

        return MatchContext(
            match_id=match.match_id,
            player_riot_id=player.riot_id,
            player_champion=player.champion_name,
            role=player.position,
            win=player.win,
            duration_min=round(duration_min, 1),
            kda=f"{player.kills}/{player.deaths}/{player.assists}",
            cs_per_min=round(cs_per_min, 1),
            vision_score=player.vision_score,
            kill_participation_pct=round(kp, 1),
            damage_share_pct=round(ds, 1),
            time_dead_pct=round(dead_pct, 1),
            rank=self.rank,
            wards_placed=player.wards_placed,
            wards_killed=player.wards_killed,
            control_wards_placed=player.detector_wards_placed,
            final_items=self._resolve_items(player.items, _item_names),
            summoner_spells=[str(s) for s in player.summoner_spells],
            deaths=deaths,
            objectives=objectives,
            gold_curve=self._build_gold(timeline, opponent),
            cs_stats=self._build_cs(player, timeline, duration_min),
            bad_recalls=self._build_recalls(timeline, player.position),
            death_streaks=self._build_death_streaks(timeline),
            # VOD Proxy JSON
            item_timeline=item_tl,
            boots_purchase_time_sec=boots_t,
            first_completed_item_time_sec=first_item_t,
            antiheal_purchase_time_sec=antiheal_t,
            fact_log=fact_log,
            data_quality=data_quality,
            confidence_overview=conf_counts,
            # Novos campos
            tower_events=tower_events,
            multi_kills=multi_kills,
            kills_converted_to_objective=conv_yes,
            kills_not_converted=conv_no,
            kill_conversion_rate=conv_rate,
        )

    # ─────────────────────────────────────
    # Mortes
    # ─────────────────────────────────────

    def _build_deaths(
        self, match: MatchData, timeline: MatchTimeline,
        player: MatchParticipant, opponent: Optional[MatchParticipant],
        obj_timestamps: List[float] | None = None,
        streak_map: dict | None = None,
    ) -> List[DeathContext]:
        if not self._player_pid:
            return []

        kill_events = get_kill_events(timeline)
        ward_events = get_ward_events(timeline)
        my_deaths   = [e for e in kill_events if e.get("victimId") == self._player_pid]
        result      = []

        for death in my_deaths:
            ts    = death.get("timestamp", 0) / 1000
            phase = get_game_phase(ts)

            death_pos = death.get("position", {})
            px, py    = death_pos.get("x", 0), death_pos.get("y", 0)

            frame_minute = max(0, int(ts // 60) - 1)
            positions    = self._get_positions_at_frame(timeline, frame_minute)

            enemies_nearby = []
            allies_nearby  = []

            for pid, pos in positions.items():
                if pid == self._player_pid:
                    continue
                dist = _dist(px, py, pos["x"], pos["y"])
                if dist > GANK_DETECTION_RADIUS:
                    continue

                # O(1) — usa lookup pré-construído
                pid_team = self._pid_to_team.get(pid)
                is_enemy = (pid_team != self._player_team)
                champ    = self._pid_to_champ.get(pid, "Unknown")

                entry = PlayerPosition(
                    champion=champ, x=pos["x"], y=pos["y"],
                    is_enemy=is_enemy, distance_to_player=round(dist, 1),
                )
                if is_enemy:
                    enemies_nearby.append(entry)
                else:
                    allies_nearby.append(entry)

            n_enemies = len(enemies_nearby)
            n_allies  = len(allies_nearby)

            if n_enemies >= FIGHT_MIN_ENEMIES and n_allies >= TEAMFIGHT_MIN_ALLIES:
                death_type = "TEAMFIGHT"
            elif n_enemies >= FIGHT_MIN_ENEMIES:
                death_type = "TRIPLE_GANK"
            elif n_enemies == 2 and n_allies == 0:
                death_type = "GANK"
            elif n_enemies == 1 and n_allies == 0:
                death_type = "DUEL"
            else:
                death_type = "UNKNOWN"

            had_vision   = self._had_vision_of_killer(death, ward_events)
            # Se o killer é o oponente de lane direto, visão sempre = True
            # (minions fornecem visão do laner — não é surpresa de gank)
            killer_pid    = death.get("killerId")
            opponent_pid  = self._puuid_to_pid.get(opponent.puuid) if opponent else None
            if opponent_pid and killer_pid == opponent_pid:
                had_vision = True
            gold_diff    = self._get_gold_diff_at(timeline, opponent, ts)
            wave_state   = self._calculate_wave_state(ts, player.position)
            killer_champ = self._pid_to_champ.get(death.get("killerId"), "Unknown")
            assisters    = [
                self._pid_to_champ.get(a, "Unknown")
                for a in death.get("assistingParticipantIds", [])
            ]
            is_early = ts < 180

            # Risk score determinístico — apenas fatos de match/timeline, sem wave_state
            risk_score, risk_reasons, risk_confidence = self._compute_death_risk(
                ts=ts, px=px, py=py,
                had_vision=had_vision,
                n_enemies=n_enemies, n_allies=n_allies,
                gold_diff=gold_diff,
                is_early=is_early,
                obj_timestamps=obj_timestamps or [],
            )

            death_ts_ms = death.get("timestamp", 0)
            streak, bounty = (streak_map or {}).get(death_ts_ms, (0, 0))

            result.append(DeathContext(
                timestamp_sec=round(ts, 1),
                game_phase=phase,
                player_x=px, player_y=py,
                killer_champion=killer_champ,
                assisters=assisters,
                enemies_nearby=enemies_nearby,
                allies_nearby=allies_nearby,
                death_type=death_type,
                had_vision_of_killer=had_vision,
                enemies_count=n_enemies,
                allies_count=n_allies,
                gold_deficit_at_death=gold_diff,
                wave_state=wave_state,
                is_early_death=is_early,
                risk_score=risk_score,
                risk_reasons=risk_reasons,
                risk_confidence=risk_confidence,
                kill_streak_before_death=streak,
                bounty_gold_lost=bounty,
            ))

        return result

    # ─────────────────────────────────────
    # Objetivos
    # ─────────────────────────────────────

    def _build_objectives(self, match: MatchData, timeline: MatchTimeline) -> List[ObjectiveContext]:
        ward_events = get_ward_events(timeline)
        obj_events  = [e for e in timeline.events if e.get("type") == "ELITE_MONSTER_KILL"]
        result      = []

        for obj in obj_events:
            monster = obj.get("monsterType", "")
            if monster not in ("DRAGON", "BARON_NASHOR", "RIFTHERALD"):
                continue

            ts    = obj.get("timestamp", 0) / 1000
            phase = get_game_phase(ts)
            pit   = BARON_PIT if monster == "BARON_NASHOR" else (
                    HERALD_PIT if monster == "RIFTHERALD" else DRAGON_PIT)

            had_vision = self._had_vision_near(ward_events, pit, ts, OBJECTIVE_VISION_RADIUS)

            positions    = self._get_positions_at_frame(timeline, int(ts // 60))
            allies_near  = 0
            enemies_near = 0
            for pid, pos in positions.items():
                if _dist(pit["x"], pit["y"], pos["x"], pos["y"]) > OBJECTIVE_VISION_RADIUS * 1.5:
                    continue
                if self._pid_to_team.get(pid) == self._player_team:
                    allies_near += 1
                else:
                    enemies_near += 1

            killer_pid  = obj.get("killerId")
            killer_team = str(self._pid_to_team.get(killer_pid, "")) or None

            result.append(ObjectiveContext(
                objective_type=monster,
                timestamp_sec=round(ts, 1),
                game_phase=phase,
                had_vision_on_pit=had_vision,
                allies_nearby=allies_near,
                enemies_nearby=enemies_near,
                killer_team=killer_team,
            ))

        return result

    # ─────────────────────────────────────
    # Curva de Gold — CORRIGIDO (sem abs, só negativo é ruim)
    # ─────────────────────────────────────

    def _build_gold(self, timeline: MatchTimeline, opponent: Optional[MatchParticipant]) -> List[GoldContext]:
        if not self._player_pid or not opponent:
            return []

        opponent_pid = self._puuid_to_pid.get(opponent.puuid)
        if not opponent_pid:
            return []

        result = []
        for frame in timeline.frames:
            ts = frame.get("timestamp", 0) / 1000
            if ts % 300 > 30:
                continue

            pf     = frame.get("participantFrames", {})
            p_data = pf.get(str(self._player_pid), {})
            o_data = pf.get(str(opponent_pid), {})
            p_gold = p_data.get("totalGold", 0)
            o_gold = o_data.get("totalGold", 0)
            diff   = p_gold - o_gold
            xp_diff = p_data.get("xp", 0) - o_data.get("xp", 0)
            phase  = get_game_phase(ts)

            # Só classifica como ruim se for NEGATIVO (jogador atrás)
            if diff <= -GOLD_DEFICIT_THRESHOLD["CRITICAL"]:
                severity = "CRITICAL"
            elif diff <= -GOLD_DEFICIT_THRESHOLD["HIGH"]:
                severity = "HIGH"
            elif diff <= -GOLD_DEFICIT_THRESHOLD["MEDIUM"]:
                severity = "MEDIUM"
            else:
                severity = "OK"

            result.append(GoldContext(
                timestamp_sec=round(ts, 1),
                game_phase=phase,
                player_total_gold=p_gold,
                opponent_total_gold=o_gold,
                gold_diff=diff,
                gold_diff_severity=severity,
                xp_diff=xp_diff,
            ))

        return result

    # ─────────────────────────────────────
    # CS por fase
    # ─────────────────────────────────────

    def _build_cs(self, player: MatchParticipant, timeline: MatchTimeline, duration_min: float) -> List[CSContext]:
        if not self._player_pid or player.position == "JUNGLE":
            return []

        result = []
        # (phase_name, start_sec, end_sec, phase_end_min, bench_key)
        # phase_end_min = None → usa duration_min real da partida
        phases = [
            ("EARLY", 0,       14 * 60, 14.0,  "15min"),
            ("MID",   14 * 60, 25 * 60, 25.0,  "25min"),
            ("LATE",  25 * 60, 999999,  None,   "30min"),
        ]

        for phase_name, start, end, phase_end_min, bench_key in phases:
            if start >= duration_min * 60:
                break

            frame_idx      = min(int(end / 60), len(timeline.frames) - 1)
            pf             = timeline.frames[frame_idx].get("participantFrames", {})
            pd             = pf.get(str(self._player_pid), {})
            cs             = pd.get("minionsKilled", 0) + pd.get("jungleMinionsKilled", 0)
            actual_end_min = min(phase_end_min, duration_min) if phase_end_min is not None else duration_min
            cs_pm          = cs / max(actual_end_min, 1)

            bench     = self._cs_bench.get(bench_key, 0)
            diff      = cs - bench
            gold_lost = int(max(0, -diff) * 20)

            result.append(CSContext(
                phase=phase_name,
                cs_at_phase_end=cs,
                cs_per_min=round(cs_pm, 1),
                benchmark=bench,
                cs_diff_to_benchmark=round(diff, 1),
                gold_lost_estimate=gold_lost,
            ))

        return result

    # ─────────────────────────────────────
    # Recalls — CORRIGIDO (visão local, não global)
    # ─────────────────────────────────────

    def _build_recalls(self, timeline: MatchTimeline, player_role: str = "") -> List[RecallContext]:
        if not self._player_pid:
            return []

        # Tenta pegar eventos RECALL_START direto da timeline
        recall_events = [
            e for e in timeline.events
            if e.get("type") in ("RECALL_START", "RECALL")
            and e.get("participantId") == self._player_pid
        ]

        # Fallback: infere por proximidade ao nexus
        if not recall_events:
            recall_events = self._infer_recalls_from_position(timeline)

        kill_events = get_kill_events(timeline)
        ward_events = get_ward_events(timeline)
        result      = []

        for recall in recall_events:
            ts    = recall.get("timestamp", 0) / 1000
            phase = get_game_phase(ts)

            # Posição do jogador no momento do recall
            frame_idx = min(int(ts // 60), len(timeline.frames) - 1)
            pf        = timeline.frames[frame_idx].get("participantFrames", {})
            pos       = pf.get(str(self._player_pid), {}).get("position", {})
            px, py    = pos.get("x", 0), pos.get("y", 0)

            # Gold ganho no minuto anterior
            frame_before = max(0, frame_idx - 1)
            gold_before  = timeline.frames[frame_before].get("participantFrames", {}).get(str(self._player_pid), {}).get("totalGold", 0)
            gold_now     = pf.get(str(self._player_pid), {}).get("totalGold", 0)
            gold_earned  = max(0, gold_now - gold_before)

            # Kill recente
            had_kill = any(
                e.get("killerId") == self._player_pid and
                abs(e.get("timestamp", 0) / 1000 - ts) < RECALL_KILL_WINDOW
                for e in kill_events
            )

            # CORRIGIDO: visão PERTO do jogador, não global
            player_pos   = {"x": px, "y": py}
            had_vision   = self._had_vision_near(ward_events, player_pos, ts, radius=2000)
            wave_state   = self._calculate_wave_state(ts, player_role)

            # Cenário A: recall após kill com wave empurrando → desperdiça pressão de lane
            scenario_a = had_kill and wave_state == "PUSHING_TO_ENEMY"
            # Cenário B: recall desnecessário — tinha segurança mas voltou sem farm
            scenario_b = had_vision and gold_earned < RECALL_GOLD_THRESHOLD
            is_questionable = scenario_a or scenario_b

            if is_questionable:
                result.append(RecallContext(
                    timestamp_sec=round(ts, 1),
                    game_phase=phase,
                    gold_earned_last_minute=gold_earned,
                    had_recent_kill=had_kill,
                    had_vision_nearby=had_vision,
                    wave_state=wave_state,
                    is_questionable=True,
                ))

        return result

    # ─────────────────────────────────────
    # Streaks de morte
    # ─────────────────────────────────────

    def _build_death_streaks(self, timeline: MatchTimeline) -> List[DeathStreakContext]:
        if not self._player_pid:
            return []

        kill_events = get_kill_events(timeline)
        my_deaths   = sorted(
            [e for e in kill_events if e.get("victimId") == self._player_pid],
            key=lambda e: e.get("timestamp", 0),
        )

        result = []
        i = 0
        while i < len(my_deaths):
            streak = [my_deaths[i]]
            j = i + 1
            while j < len(my_deaths):
                window = (my_deaths[j]["timestamp"] - my_deaths[i]["timestamp"]) / 1000
                if window <= STREAK_TIME_WINDOW:
                    streak.append(my_deaths[j])
                    j += 1
                else:
                    break

            if len(streak) >= STREAK_DEATH_COUNT:
                start_ts = streak[0]["timestamp"] / 1000
                end_ts   = streak[-1]["timestamp"] / 1000
                phase    = get_game_phase(start_ts)

                recovered = True
                if j < len(my_deaths):
                    next_ts   = my_deaths[j]["timestamp"] / 1000
                    recovered = (next_ts - end_ts) >= STREAK_RECOVERY_TIME

                result.append(DeathStreakContext(
                    deaths_in_streak=len(streak),
                    start_time_sec=round(start_ts, 1),
                    end_time_sec=round(end_ts, 1),
                    game_phase=phase,
                    recovered=recovered,
                ))
                i = j
            else:
                i += 1

        return result

    # ─────────────────────────────────────
    # Wave State — IMPLEMENTADO (sem migué!)
    # ─────────────────────────────────────

    def _calculate_wave_state(self, game_time_sec: float, lane: str) -> str:
        """
        Estima o estado da wave baseado no ciclo de spawn e velocidade dos minions.

        Lógica:
        - Minions nascem a cada 30s (reduz com o tempo)
        - Levam X segundos para chegar ao centro dependendo da lane e velocidade
        - Se o tempo atual está no primeiro terço do ciclo = wave empurrando para inimigo
        - Se está no terço final = wave empurrando para aliado
        - No meio = neutra
        """
        if game_time_sec < MINION_SPAWN_TIME:
            return "NEUTRAL"

        speed        = get_minion_speed(game_time_sec)
        lane_key     = lane if lane in LANE_LENGTH_TO_CENTER else "MIDDLE"
        lane_dist    = LANE_LENGTH_TO_CENTER[lane_key]

        # Tempo que a wave leva pra atravessar metade da lane (base → centro)
        travel_time  = lane_dist / speed  # segundos

        # Intervalo de spawn atual
        wave_interval = get_wave_interval(game_time_sec)

        # Tempo dentro do ciclo de wave atual
        elapsed_since_spawn = (game_time_sec - MINION_SPAWN_TIME) % wave_interval

        # Fração do ciclo: 0.0 = recém nasceu, 1.0 = quase chegando ao destino
        cycle_fraction = elapsed_since_spawn / max(wave_interval, 1)

        if cycle_fraction < 0.33:
            return "PUSHING_TO_ENEMY"   # wave saiu da base aliada, avançando
        elif cycle_fraction > 0.67:
            return "PUSHING_TO_ALLY"    # wave avançou demais, voltando ao equilíbrio
        else:
            return "NEUTRAL"            # wave no meio da rota

    # ─────────────────────────────────────
    # Utilitários internos
    # ─────────────────────────────────────

    def _find_player(self, match: MatchData) -> Optional[MatchParticipant]:
        for p in match.participants:
            if p.puuid == self.target_puuid:
                return p
        return None

    def _find_lane_opponent(self, match: MatchData, player: MatchParticipant) -> Optional[MatchParticipant]:
        for p in match.participants:
            if p.team_id != player.team_id and p.position == player.position:
                return p
        return None

    def _get_positions_at_frame(self, timeline: MatchTimeline, frame_idx: int) -> dict:
        if frame_idx >= len(timeline.frames):
            frame_idx = len(timeline.frames) - 1
        frame     = timeline.frames[frame_idx]
        positions = {}
        for pid, data in frame.get("participantFrames", {}).items():
            pos = data.get("position", {})
            positions[int(pid)] = {"x": pos.get("x", 0), "y": pos.get("y", 0)}
        return positions

    def _had_vision_of_killer(self, death_event: dict, ward_events: list) -> bool:
        kill_time = death_event.get("timestamp", 0)   # ms
        kill_pos  = death_event.get("position", {})
        kx, ky    = kill_pos.get("x", 0), kill_pos.get("y", 0)

        active_wards: dict = {}
        for e in ward_events:
            t = e.get("timestamp", 0)
            if t >= kill_time:
                break
            etype    = e.get("type")
            ward_pos = e.get("position", {})
            wx, wy   = ward_pos.get("x", 0), ward_pos.get("y", 0)
            wid      = f"{wx}_{wy}"
            if etype == "WARD_PLACED":
                # Só conta wards colocadas pelo time aliado
                creator_team = self._pid_to_team.get(e.get("creatorId"))
                if creator_team != self._player_team:
                    continue
                ward_type      = e.get("wardType", "YELLOW_TRINKET")
                dur, radius    = _WARD_PROPS.get(ward_type, _WARD_PROPS_DEFAULT)
                expiry_ms      = -1 if dur == -1 else t + dur * 1000
                active_wards[wid] = {"x": wx, "y": wy, "expiry_ms": expiry_ms, "radius": radius}
            elif etype == "WARD_KILL":
                active_wards.pop(wid, None)

        for ward in active_wards.values():
            if ward["expiry_ms"] != -1 and ward["expiry_ms"] < kill_time:
                continue  # ward expirou antes da morte
            if _dist(ward["x"], ward["y"], kx, ky) <= ward["radius"]:
                return True
        return False

    def _had_vision_near(self, ward_events: list, position: dict, before_sec: float, radius: int = 900) -> bool:
        """Verifica se o time aliado tinha visão cobrindo `position` antes de `before_sec`.
        O `radius` é ignorado na checagem final — usa-se o raio real de cada tipo de ward.
        """
        before_ms    = before_sec * 1000
        active_wards: dict = {}
        px, py       = position.get("x", 0), position.get("y", 0)

        for e in ward_events:
            t = e.get("timestamp", 0)
            if t > before_ms:
                break
            etype    = e.get("type")
            ward_pos = e.get("position", {})
            wx, wy   = ward_pos.get("x", 0), ward_pos.get("y", 0)
            wid      = f"{wx}_{wy}"
            if etype == "WARD_PLACED":
                # Só conta wards do time aliado
                creator_team = self._pid_to_team.get(e.get("creatorId"))
                if creator_team != self._player_team:
                    continue
                ward_type   = e.get("wardType", "YELLOW_TRINKET")
                dur, w_rad  = _WARD_PROPS.get(ward_type, _WARD_PROPS_DEFAULT)
                expiry_ms   = -1 if dur == -1 else t + dur * 1000
                active_wards[wid] = {"x": wx, "y": wy, "expiry_ms": expiry_ms, "w_radius": w_rad}
            elif etype == "WARD_KILL":
                active_wards.pop(wid, None)

        for ward in active_wards.values():
            if ward["expiry_ms"] != -1 and ward["expiry_ms"] < before_ms:
                continue  # ward expirou antes do momento verificado
            if _dist(ward["x"], ward["y"], px, py) <= ward["w_radius"]:
                return True
        return False

    def _get_gold_diff_at(self, timeline: MatchTimeline, opponent: Optional[MatchParticipant], at_sec: float) -> int:
        if not opponent:
            return 0
        opponent_pid = self._puuid_to_pid.get(opponent.puuid)
        if not opponent_pid:
            return 0
        frame_idx = min(int(at_sec // 60), len(timeline.frames) - 1)
        pf        = timeline.frames[frame_idx].get("participantFrames", {})
        p_gold    = pf.get(str(self._player_pid), {}).get("totalGold", 0)
        o_gold    = pf.get(str(opponent_pid), {}).get("totalGold", 0)
        return p_gold - o_gold

    def _resolve_items(self, item_ids: list[int], item_names: Dict[str, str]) -> list[str]:
        """
        Resolve IDs de itens para nomes.
        - Slots vazios (id=0) → ignorados silenciosamente.
        - IDs não resolvidos → "UnknownItem(<id>)" + warning em data_quality.
          NUNCA descarta silenciosamente: a IA precisa saber que o item existe.
        """
        result = []
        for item_id in item_ids:
            if item_id == 0:
                continue
            name = item_names.get(str(item_id))
            if name:
                result.append(name)
            else:
                warn_key = f"ITEM_ID_NOT_FOUND:{item_id}"
                if warn_key not in self._warnings:
                    self._warnings.append(warn_key)
                result.append(f"UnknownItem({item_id})")
        return result

    # ─────────────────────────────────────
    # Item Timeline
    # ─────────────────────────────────────

    def _build_item_timeline(
        self,
        timeline: MatchTimeline,
        item_names: Dict[str, str],
    ) -> tuple:
        """
        Extrai eventos ITEM_PURCHASED / ITEM_SOLD / ITEM_UNDO do jogador.
        Retorna: (entries, extra_warnings, boots_t, first_item_t, antiheal_t, resolve_ratio)

        - Nunca descarta IDs sem nome: usa "UnknownItem(<id>)" e acumula warning.
        - Se a timeline não tiver eventos de item → warning "MISSING_ITEM_TIMELINE".
        - first_completed_item_time_sec: proxy (heurística temporal ≥ 8 min, não-bota) → confidence MED.
        """
        if not self._player_pid:
            return [], [], None, None, None, 1.0

        item_events = sorted(
            [
                e for e in timeline.events
                if e.get("type") in ("ITEM_PURCHASED", "ITEM_SOLD", "ITEM_UNDO")
                and e.get("participantId") == self._player_pid
            ],
            key=lambda e: e.get("timestamp", 0),
        )

        if not item_events:
            return [], ["MISSING_ITEM_TIMELINE"], None, None, None, 1.0

        extra_warnings: List[str] = []
        entries: List[ItemTimelineEntry] = []
        boots_t: Optional[float] = None
        first_item_t: Optional[float] = None
        antiheal_t: Optional[float] = None
        total = resolved = 0

        for e in item_events:
            etype = e.get("type")
            ts    = e.get("timestamp", 0) / 1000

            if etype == "ITEM_UNDO":
                item_id = e.get("beforeId", 0)
                action  = "UNDO"
            elif etype == "ITEM_SOLD":
                item_id = e.get("itemId", 0)
                action  = "SOLD"
            else:
                item_id = e.get("itemId", 0)
                action  = "PURCHASED"

            if item_id == 0:
                continue

            total += 1
            name = item_names.get(str(item_id))
            if name:
                resolved += 1
                display = name
            else:
                display  = f"UnknownItem({item_id})"
                warn_key = f"ITEM_ID_NOT_FOUND:{item_id}"
                if warn_key not in extra_warnings:
                    extra_warnings.append(warn_key)

            entries.append(ItemTimelineEntry(t=round(ts, 1), item_id=item_id, action=action, name=display))

            if action == "PURCHASED":
                if boots_t is None and item_id in BOOTS_ITEM_IDS:
                    boots_t = round(ts, 1)
                if antiheal_t is None and item_id in ANTIHEAL_ITEM_IDS:
                    antiheal_t = round(ts, 1)
                # Heurística de primeiro item completo: 1ª compra não-bota após 8 min
                # Confidence MED — proxy temporal (custo não verificado via DDragon)
                if first_item_t is None and item_id not in BOOTS_ITEM_IDS and ts >= 480:
                    first_item_t = round(ts, 1)

        ratio = resolved / total if total > 0 else 1.0
        return entries, extra_warnings, boots_t, first_item_t, antiheal_t, round(ratio, 3)

    # ─────────────────────────────────────
    # Risk Score de morte (determinístico)
    # ─────────────────────────────────────

    def _compute_death_risk(
        self,
        ts: float, px: int, py: int,
        had_vision: bool,
        n_enemies: int, n_allies: int,
        gold_diff: int,
        is_early: bool,
        obj_timestamps: List[float],
    ) -> tuple[int, List[str], str]:
        """
        Calcula (risk_score, risk_reasons, risk_confidence) de forma determinística.
        Inputs: apenas fatos de match/timeline. NÃO usa wave_state (proxy).
        Todos os inputs têm origem HIGH → risk_confidence sempre "HIGH".

        Pontuação:
          NO_VISION          +3  (ward events)
          OUTNUMBERED        +2  (frame positions)
          ALONE              +1  (frame positions)
          DEEP_POSITION      +2  (kill event position vs nexus — threshold = 10.000 units)
          PRE_OBJECTIVE_WINDOW +2 (elite_monster_kill timestamps ± 120s)
          BEHIND_IN_GOLD     +1  (participant frames, deficit > 800)
          EARLY_DEATH        +1  (timestamp < 180s)
          Máximo: 10
        """
        reasons: List[str] = []
        score = 0

        if not had_vision:
            reasons.append("NO_VISION")
            score += 3

        if n_enemies > n_allies + 1:
            reasons.append("OUTNUMBERED")
            score += 2

        if n_allies == 0 and n_enemies >= 1:
            reasons.append("ALONE")
            score += 1

        if self._player_team is not None:
            nexus_key = "blue" if self._player_team == 100 else "red"
            nx, ny    = NEXUS[nexus_key]["x"], NEXUS[nexus_key]["y"]
            if _dist(px, py, nx, ny) > 10000:
                reasons.append("DEEP_POSITION")
                score += 2

        for obj_ts in obj_timestamps:
            if abs(ts - obj_ts) <= 120:
                reasons.append("PRE_OBJECTIVE_WINDOW")
                score += 2
                break

        if gold_diff < -800:
            reasons.append("BEHIND_IN_GOLD")
            score += 1

        if is_early:
            reasons.append("EARLY_DEATH")
            score += 1

        return min(score, 10), reasons, "HIGH"

    # ─────────────────────────────────────
    # Fact Log (linha do tempo cronológica — VOD Proxy)
    # ─────────────────────────────────────

    def _build_fact_log(
        self,
        timeline: MatchTimeline,
        deaths: List[DeathContext],
        objectives: List[ObjectiveContext],
        item_timeline: List[ItemTimelineEntry],
    ) -> List[dict]:
        """
        Monta a linha do tempo cronológica de eventos relevantes do jogador.

        Regras de confidence:
          HIGH → dado direto de match/timeline (kill, ward, item com nome resolvido, objetivo)
          MED  → dado parcial (item com nome não resolvido)
          LOW  → proxy derivado (ex.: wave_state) — explicitado em proxy_context
        """
        entries: List[dict] = []
        kill_events = get_kill_events(timeline)
        ward_events = get_ward_events(timeline)

        # 1. Mortes do jogador
        for d in deaths:
            proxy_ctx: Optional[dict] = None
            if d.wave_state is not None:
                proxy_ctx = {
                    "wave_state": d.wave_state,
                    "confidence": "LOW",
                    "source": "derived_proxy",
                    "note": "Estimativa de ciclo de spawn — não observado na timeline",
                }
            entries.append({
                "t": d.timestamp_sec,
                "type": "DEATH",
                "facts": {
                    "killer": d.killer_champion,
                    "assisters": d.assisters,
                    "death_type": d.death_type,
                    "had_vision_of_killer": d.had_vision_of_killer,
                    "enemies_nearby": d.enemies_count,
                    "allies_nearby": d.allies_count,
                    "gold_deficit": d.gold_deficit_at_death,
                    "risk_score": d.risk_score,
                    "risk_reasons": d.risk_reasons,
                    **({"proxy_context": proxy_ctx} if proxy_ctx else {}),
                },
                "confidence": "HIGH",
                "sources": ["timeline", "match_v5"],
            })

        # 2. Kills do jogador
        if self._player_pid:
            for e in kill_events:
                if e.get("killerId") != self._player_pid:
                    continue
                ts           = e.get("timestamp", 0) / 1000
                victim_champ = self._pid_to_champ.get(e.get("victimId"), "Unknown")
                entries.append({
                    "t": round(ts, 1),
                    "type": "KILL",
                    "facts": {
                        "victim": victim_champ,
                        "assisters": [
                            self._pid_to_champ.get(a, "Unknown")
                            for a in e.get("assistingParticipantIds", [])
                        ],
                    },
                    "confidence": "HIGH",
                    "sources": ["timeline"],
                })

        # 3. Objetivos (dragon / baron / herald)
        for obj in objectives:
            player_team_took = (obj.killer_team == str(self._player_team))
            entries.append({
                "t": obj.timestamp_sec,
                "type": "OBJECTIVE",
                "facts": {
                    "objective_type": obj.objective_type,
                    "player_team_took": player_team_took,
                    "had_vision_on_pit": obj.had_vision_on_pit,
                    "allies_nearby": obj.allies_nearby,
                    "enemies_nearby": obj.enemies_nearby,
                },
                "confidence": "HIGH",
                "sources": ["timeline"],
            })

        # 4. Eventos de item do jogador
        for item in item_timeline:
            is_known = not item.name.startswith("UnknownItem")
            entries.append({
                "t": item.t,
                "type": f"ITEM_{item.action}",
                "facts": {"item_id": item.item_id, "name": item.name},
                "confidence": "HIGH" if is_known else "MED",
                "sources": ["timeline"],
            })

        # 5. Wards colocadas pelo jogador
        if self._player_pid:
            for e in ward_events:
                if e.get("type") != "WARD_PLACED":
                    continue
                if e.get("creatorId") != self._player_pid:
                    continue
                ts  = e.get("timestamp", 0) / 1000
                pos = e.get("position", {})
                entries.append({
                    "t": round(ts, 1),
                    "type": "WARD_PLACED",
                    "facts": {
                        "ward_type": e.get("wardType", "UNKNOWN"),
                        "x": pos.get("x", 0),
                        "y": pos.get("y", 0),
                    },
                    "confidence": "HIGH",
                    "sources": ["timeline"],
                })

        entries.sort(key=lambda e: e["t"])
        return entries

    # ─────────────────────────────────────
    # Kill streaks e bounty
    # ─────────────────────────────────────

    def _compute_kill_streak_map(self, timeline: MatchTimeline) -> dict:
        """
        Pré-computa o kill streak do jogador no instante de cada morte.
        Retorna: {death_timestamp_ms: (streak, bounty_gold)}
        Processa kills e mortes do jogador em ordem cronológica.
        """
        if not self._player_pid:
            return {}

        events = []
        for e in get_kill_events(timeline):
            if e.get("killerId") == self._player_pid:
                events.append(("kill", e.get("timestamp", 0)))
            elif e.get("victimId") == self._player_pid:
                events.append(("death", e.get("timestamp", 0)))

        events.sort(key=lambda x: x[1])

        streak = 0
        result = {}
        for etype, ts in events:
            if etype == "kill":
                streak += 1
            else:
                result[ts] = (streak, _bounty_for_streak(streak))
                streak = 0
        return result

    # ─────────────────────────────────────
    # Torres
    # ─────────────────────────────────────

    def _build_tower_events(self, timeline: MatchTimeline) -> List[TowerEventContext]:
        _TIER_MAP = {
            "OUTER_TURRET": "OUTER",
            "INNER_TURRET": "INNER",
            "BASE_TURRET":  "BASE",
            "NEXUS_TURRET": "NEXUS",
        }
        _LANE_MAP = {
            "TOP_LANE": "TOP",
            "MID_LANE": "MID",
            "BOT_LANE": "BOT",
        }
        result = []

        for event in timeline.events:
            if event.get("type") != "BUILDING_KILL":
                continue
            if event.get("buildingType") != "TOWER_BUILDING":
                continue

            ts  = event.get("timestamp", 0) / 1000
            pos = event.get("position", {})
            tx, ty = pos.get("x", 0), pos.get("y", 0)

            player_nearby = False
            if self._player_pid and timeline.frames:
                frame_idx = min(int(ts // 60), len(timeline.frames) - 1)
                pf    = timeline.frames[frame_idx].get("participantFrames", {})
                p_pos = pf.get(str(self._player_pid), {}).get("position", {})
                player_nearby = _dist(p_pos.get("x", 0), p_pos.get("y", 0), tx, ty) <= 3000

            # teamId = time que ERA dono da torre (quem PERDEU)
            lost_by_ally = (event.get("teamId", 0) == self._player_team)

            result.append(TowerEventContext(
                timestamp_sec=round(ts, 1),
                game_phase=get_game_phase(ts),
                tower_tier=_TIER_MAP.get(event.get("towerType", ""), "OUTER"),
                lane=_LANE_MAP.get(event.get("laneType", ""), "MID"),
                lost_by_ally=lost_by_ally,
                player_was_nearby=player_nearby,
            ))

        return result

    # ─────────────────────────────────────
    # Multi-kills
    # ─────────────────────────────────────

    def _build_multi_kills(self, timeline: MatchTimeline) -> List[MultiKillContext]:
        if not self._player_pid:
            return []

        MULTI_WINDOW_MS = 10_000  # 10 segundos

        player_kills = sorted(
            [e for e in get_kill_events(timeline) if e.get("killerId") == self._player_pid],
            key=lambda e: e.get("timestamp", 0),
        )
        result = []
        i = 0
        while i < len(player_kills):
            streak = [player_kills[i]]
            j = i + 1
            while j < len(player_kills):
                if player_kills[j]["timestamp"] - player_kills[j - 1]["timestamp"] <= MULTI_WINDOW_MS:
                    streak.append(player_kills[j])
                    j += 1
                else:
                    break

            if len(streak) >= 2:
                ts = streak[0]["timestamp"] / 1000
                result.append(MultiKillContext(
                    timestamp_sec=round(ts, 1),
                    game_phase=get_game_phase(ts),
                    kill_count=len(streak),
                ))
                i = j
            else:
                i += 1

        return result

    # ─────────────────────────────────────
    # Kill conversion (kill → objective/torre em 90s)
    # ─────────────────────────────────────

    def _build_kill_conversion(self, timeline: MatchTimeline) -> tuple:
        """
        Para cada kill do jogador, verifica se em 90s houve torre ou objective pelo time aliado.
        Retorna: (converted, not_converted, rate_pct)
        """
        if not self._player_pid:
            return 0, 0, 0.0

        player_kills = sorted(
            [e for e in get_kill_events(timeline) if e.get("killerId") == self._player_pid],
            key=lambda e: e.get("timestamp", 0),
        )
        if not player_kills:
            return 0, 0, 0.0

        WINDOW_MS = 90_000

        # Eventos de estrutura e objective tomados pelo time aliado
        ally_conversions = [
            e for e in timeline.events
            if e.get("type") in ("BUILDING_KILL", "ELITE_MONSTER_KILL")
            and self._pid_to_team.get(e.get("killerId")) == self._player_team
        ]

        converted = not_converted = 0
        for kill in player_kills:
            kill_ts  = kill.get("timestamp", 0)
            window_end = kill_ts + WINDOW_MS
            found = any(kill_ts <= c.get("timestamp", 0) <= window_end for c in ally_conversions)
            if found:
                converted += 1
            else:
                not_converted += 1

        total = converted + not_converted
        rate  = round(converted / total * 100, 1) if total > 0 else 0.0
        return converted, not_converted, rate

    def _infer_recalls_from_position(self, timeline: MatchTimeline) -> list:
        """Infere recalls por proximidade ao nexus ALIADO quando RECALL_START não está disponível."""
        NEXUS_BLUE    = {"x": 917,   "y": 684}
        NEXUS_RED     = {"x": 14298, "y": 14820}
        RECALL_RADIUS = 1500
        recalls       = []
        prev_near     = False

        # Usa apenas o nexus do próprio time — evita falso positivo quando jogador está no nexus inimigo
        own_nexus = NEXUS_BLUE if self._player_team == 100 else NEXUS_RED

        for frame in timeline.frames:
            pf  = frame.get("participantFrames", {})
            pos = pf.get(str(self._player_pid), {}).get("position", {})
            px, py = pos.get("x", 0), pos.get("y", 0)

            near = _dist(px, py, own_nexus["x"], own_nexus["y"]) < RECALL_RADIUS

            if near and not prev_near:
                recalls.append({"timestamp": frame.get("timestamp", 0)})
            prev_near = near

        return recalls
