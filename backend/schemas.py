"""
Schemas Pydantic - request/response models da API.
"""
from typing import Any, Optional
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# -- Feedback --

class FeedbackRequest(StrictRequestModel):
    match_id: str = Field(min_length=3, max_length=80)
    player: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


# -- Live events (SSE debug) --

class LiveEventUpload(StrictRequestModel):
    event_type: str = Field(min_length=1, max_length=40)
    game_time_sec: float = Field(ge=0, le=10800)
    champion: str = Field(min_length=1, max_length=64)
    detail: str = Field(default="", max_length=300)
    killer: Optional[str] = Field(default=None, max_length=64)
    victim: Optional[str] = Field(default=None, max_length=64)
    assisters: list[str] = Field(default_factory=list, max_length=10)
    objective_stolen: bool = False
    minimap_base64: str = Field(min_length=20, max_length=4_000_000)


class LiveUploadRequest(StrictRequestModel):
    puuid: str = Field(min_length=8, max_length=120)
    match_id: str = Field(min_length=3, max_length=80)
    events: list[LiveEventUpload] = Field(min_length=1, max_length=120)


class LiveUploadResponse(BaseModel):
    match_id: str
    analysis: str
    event_count: int


# -- Coaching --

class CoachingSaveRequest(StrictRequestModel):
    match_id: str = Field(min_length=3, max_length=80)
    puuid: str = Field(default="", max_length=120)
    riot_id: str = Field(default="", max_length=64)
    analysis: str = Field(min_length=10, max_length=30_000)


class CoachingAnalysisResponse(BaseModel):
    match_id: str
    has_analysis: bool
    status: Literal["ready", "pending", "insufficient_data", "failed"] = "pending"
    analysis: Optional[str] = None
    message: Optional[str] = None


class CoachingStatusResponse(BaseModel):
    match_id: str
    has_analysis: bool
    status: Literal["ready", "pending", "insufficient_data", "failed"]
    message: Optional[str] = None


class CoachingRegenerateResponse(BaseModel):
    match_id: str
    status: Literal["blocked"]
    message: str


# -- Scoreboard --

class ScoreboardPlayer(BaseModel):
    puuid: str
    summoner_name: str
    champion: str
    position: str
    kills: int
    deaths: int
    assists: int
    cs: int
    cs_per_min: float
    total_damage: int
    damage_share_pct: float
    gold_earned: int
    vision_score: int
    items: list[int]
    summoner1_id: int
    summoner2_id: int
    is_target: bool


class ScoreboardTeam(BaseModel):
    side: str
    win: bool
    players: list[ScoreboardPlayer]


class ScoreboardResponse(BaseModel):
    match_id: str
    duration_min: float
    teams: list[ScoreboardTeam]


# -- Local app --

class LocalEventUpload(StrictRequestModel):
    event_type: str = Field(min_length=1, max_length=40)
    game_time: str = Field(default="", max_length=10)
    champion: str = Field(default="", max_length=64)
    killer: Optional[str] = Field(default=None, max_length=64)
    victim: Optional[str] = Field(default=None, max_length=64)
    detail: str = Field(default="", max_length=300)
    assisters: list[str] = Field(default_factory=list, max_length=10)
    minimap_base64: str = Field(default="", max_length=4_000_000)


class LocalUploadRequest(StrictRequestModel):
    riot_id: str = Field(min_length=3, max_length=64)
    events: list[LocalEventUpload] = Field(min_length=1, max_length=120)
    match_id: str = Field(default="", max_length=80)
    player_map: dict[str, str] = Field(default_factory=dict)

    @field_validator("player_map")
    @classmethod
    def _limit_player_map(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 20:
            raise ValueError("player_map muito grande")
        for key, champion in value.items():
            if not key or len(key) > 64:
                raise ValueError("riot_id invalido no player_map")
            if not champion or len(champion) > 64:
                raise ValueError("champion invalido no player_map")
        return value


class LocalUploadResponse(BaseModel):
    accepted: bool
    job_id: str


# -- Analyze --

class AnalyzeRequest(StrictRequestModel):
    game_name: str = Field(min_length=1, max_length=32)
    tag_line: str = Field(min_length=1, max_length=16)
    match_index: int = Field(default=0, ge=0, le=20)


class InsightResponse(BaseModel):
    category: str
    severity: str
    timestamp: float
    title: str
    detail: str
    suggestion: str


class AnalyzeResponse(BaseModel):
    match_id: str
    player: str
    champion: str
    position: str
    win: bool
    duration_min: float
    kda: str
    cs_per_min: float
    vision_score: int
    kill_participation_pct: float
    damage_share_pct: float
    time_dead_pct: float
    rank: str
    insights: list[InsightResponse]
    feedback: str


# -- Match history --

class MatchHistoryItem(BaseModel):
    match_id: str
    index: int
    champion: str
    kills: int
    deaths: int
    assists: int
    win: bool
    duration_min: int
    position: str
    wards_placed: Optional[int] = None
    wards_killed: Optional[int] = None
    summoner1_id: Optional[int] = None
    summoner2_id: Optional[int] = None
    cs: int = 0
    cs_per_min: float = 0.0
    vision_score: int = 0
    kill_participation_pct: float = 0.0
    damage_share_pct: float = 0.0
    doubles: int = 0
    triples: int = 0
    quadras: int = 0
    pentas: int = 0
    allies: list[dict[str, Any]] = Field(default_factory=list)
    items: list[int] = Field(default_factory=list)
    total_damage: int = 0


class MatchHistoryResponse(BaseModel):
    summoner: str
    puuid: str
    rank: str
    matches: list[MatchHistoryItem]
    wins: int = 0
    losses: int = 0
    has_more: bool = False
    next_offset: int = 0
