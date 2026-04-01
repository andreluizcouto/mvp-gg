"""
game_rules.py - Constantes e regras do jogo League of Legends
Fonte: Wiki oficial da Riot + Leaguepedia
Atualizado para patch atual (2025)
"""

# ─────────────────────────────────────────
# MINIONS - Spawn e wave
# ─────────────────────────────────────────

MINION_SPAWN_TIME = 65

def get_wave_interval(game_time_seconds: float) -> int:
    """Retorna o intervalo entre waves em segundos."""
    if game_time_seconds >= 30 * 60:
        return 20
    elif game_time_seconds >= 14 * 60:
        return 25
    return 30

def get_minion_speed(game_time_seconds: float) -> int:
    """
    Retorna a velocidade de movimento dos minions baseada no tempo de jogo.
    A velocidade aumenta aos 15, 20, 25 e 30 minutos. Bônus máximo: +130 MS.
    """
    minutes = game_time_seconds / 60
    base_speed = 350
    if minutes >= 30: return base_speed + 130
    if minutes >= 25: return base_speed + 90
    if minutes >= 20: return base_speed + 50
    if minutes >= 15: return base_speed + 25
    return base_speed

# ─────────────────────────────────────────
# ROTAS - Comprimentos
# ─────────────────────────────────────────

LANE_LENGTH_TO_CENTER = {
    "TOP":    14500,
    "BOTTOM": 14500,
    "MIDDLE": 10000,
}

# ─────────────────────────────────────────
# POSIÇÕES NO MAPA (coordenadas X,Y)
# ─────────────────────────────────────────

BARON_PIT  = {"x": 5007, "y": 10471}
DRAGON_PIT = {"x": 9866, "y": 4414}
HERALD_PIT = {"x": 5007, "y": 10471}

OBJECTIVE_VISION_RADIUS = 1500

NEXUS = {
    "blue": {"x": 917,   "y": 684},
    "red":  {"x": 14298, "y": 14820},
}

# ─────────────────────────────────────────
# GANK - Distâncias para classificação
# ─────────────────────────────────────────

GANK_DETECTION_RADIUS = 2000
FIGHT_MIN_ENEMIES     = 3
TEAMFIGHT_MIN_ALLIES  = 2

# ─────────────────────────────────────────
# CS - Benchmarks por elo
# ─────────────────────────────────────────

CS_BENCHMARKS = {
    "IRON":     {"10min": 55, "15min": 82,  "20min": 110, "25min": 137, "30min": 165},
    "BRONZE":   {"10min": 60, "15min": 90,  "20min": 120, "25min": 150, "30min": 180},
    "SILVER":   {"10min": 65, "15min": 97,  "20min": 130, "25min": 162, "30min": 195},
    "GOLD":     {"10min": 70, "15min": 105, "20min": 140, "25min": 175, "30min": 210},
    "PLATINUM": {"10min": 75, "15min": 112, "20min": 150, "25min": 187, "30min": 225},
    "EMERALD":  {"10min": 80, "15min": 120, "20min": 160, "25min": 200, "30min": 240},
    "DIAMOND":  {"10min": 85, "15min": 127, "20min": 170, "25min": 212, "30min": 255},
    "DEFAULT":  {"10min": 65, "15min": 97,  "20min": 130, "25min": 162, "30min": 195},
}

# ─────────────────────────────────────────
# STREAKS - Sequência de mortes
# ─────────────────────────────────────────

STREAK_DEATH_COUNT   = 3
STREAK_TIME_WINDOW   = 5 * 60
STREAK_RECOVERY_TIME = 8 * 60

# ─────────────────────────────────────────
# OURO - Thresholds
# ─────────────────────────────────────────

GOLD_DEFICIT_THRESHOLD = {
    "CRITICAL": 2000,
    "HIGH":     1500,
    "MEDIUM":   800,
}

# ─────────────────────────────────────────
# FASES DO JOGO
# ─────────────────────────────────────────

GAME_PHASES = {
    "EARLY": {"start": 0,       "end": 14 * 60},
    "MID":   {"start": 14 * 60, "end": 25 * 60},
    "LATE":  {"start": 25 * 60, "end": 999999},
}

def get_game_phase(game_time_seconds: float) -> str:
    """Retorna a fase do jogo baseado no tempo."""
    if game_time_seconds < GAME_PHASES["MID"]["start"]:
        return "EARLY"
    elif game_time_seconds < GAME_PHASES["LATE"]["start"]:
        return "MID"
    return "LATE"

# ─────────────────────────────────────────
# RECALL - Detecção de recall ruim
# ─────────────────────────────────────────

RECALL_GOLD_THRESHOLD   = 100
RECALL_KILL_WINDOW      = 60

# ─────────────────────────────────────────
# ITEMS - Allowlists para spikes/detecção
# ─────────────────────────────────────────

BOOTS_ITEM_IDS = frozenset({
    1001, 3006, 3009, 3020, 3047, 3111, 3117, 3158,
})

ANTIHEAL_ITEM_IDS = frozenset({
    3076, 3123, 3165, 3075, 3033, 3036, 3011, 6609, 3916,
})
