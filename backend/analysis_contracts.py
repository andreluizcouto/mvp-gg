"""Internal evidence and checkpoint contracts for the analysis pipeline."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from context_builder import MatchContext
from schemas import LocalEventUpload


class InternalContractModel(BaseModel):
    """Strict base model for backend-owned pipeline contracts."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceSource(StrEnum):
    """Declares which evidence sources are present in a bundle."""

    RIOT_ONLY = "riot_only"
    LOCALHOST_ONLY = "localhost_only"
    RIOT_PLUS_LOCAL = "riot_plus_local"


class PipelineStage(StrEnum):
    """Represents a checkpointed stage in the backend pipeline."""

    INGESTION = "ingestion"
    CONTEXT_BUILD = "context_build"
    ANALYSIS_GENERATION = "analysis_generation"
    OUTPUT_VALIDATION = "output_validation"
    DELIVERY = "delivery"


class StageStatus(StrEnum):
    """Internal stage result categories used to gate downstream work."""

    ACCEPTED = "accepted"
    INVALID_INPUT = "invalid_input"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"
    DEGRADED_SAFE = "degraded_safe"
    READY = "ready"
    BLOCKED = "blocked"


class ExternalAnalysisStatus(StrEnum):
    """Safe, product-facing summary of internal pipeline state."""

    READY = "ready"
    PENDING = "pending"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"


class PipelineReasonCode(StrEnum):
    """Machine-readable explanation for why a checkpoint did or did not pass."""

    MISSING_MATCH_ID = "missing_match_id"
    MISSING_MATCH_CONTEXT = "missing_match_context"
    MISSING_LOCAL_EVENTS = "missing_local_events"
    INVALID_AI_OUTPUT = "invalid_ai_output"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    LOCALHOST_ONLY_PENDING_RIOT_CONTEXT = "localhost_only_pending_riot_context"
    MISSING_ANALYSIS_TEXT = "missing_analysis_text"
    MISSING_ANALYSIS_PAYLOAD = "missing_analysis_payload"
    MISSING_CHECKPOINT = "missing_checkpoint"
    MISSING_BUNDLE = "missing_bundle"


class AnalysisEvidenceBundle(InternalContractModel):
    """Normalized internal bundle consumed by analysis and delivery helpers."""

    match_id: str = Field(default="", max_length=80)
    riot_id: str = Field(min_length=3, max_length=64)
    source: EvidenceSource
    match_context: MatchContext | None = None
    local_events: list[LocalEventUpload] = Field(default_factory=list)
    image_paths: list[str] = Field(default_factory=list)
    analysis_text: str = Field(default="", max_length=30_000)
    analysis_payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_bundle_completeness(self) -> AnalysisEvidenceBundle:
        """Fail closed for invalid combinations while preserving localhost-only drafts."""

        if self.source is EvidenceSource.LOCALHOST_ONLY:
            if self.match_context is not None:
                raise ValueError("localhost_only bundles cannot include Riot match context")
            if not self.local_events:
                raise ValueError("localhost_only bundles require local events")
            return self

        if not self.match_id:
            raise ValueError("Riot-backed bundles require a match_id")
        if self.match_context is None:
            raise ValueError("Riot-backed bundles require match_context")
        if self.source is EvidenceSource.RIOT_PLUS_LOCAL and not self.local_events:
            raise ValueError("riot_plus_local bundles require local_events")
        return self

    def missing_requirements(self) -> list[PipelineReasonCode]:
        """Returns deterministic missing-evidence reasons for stage gating."""

        reasons: list[PipelineReasonCode] = []
        if not self.match_id:
            reasons.append(PipelineReasonCode.MISSING_MATCH_ID)
        if self.match_context is None:
            reasons.append(PipelineReasonCode.MISSING_MATCH_CONTEXT)
        if self.source is EvidenceSource.RIOT_PLUS_LOCAL and not self.local_events:
            reasons.append(PipelineReasonCode.MISSING_LOCAL_EVENTS)
        if self.source is EvidenceSource.LOCALHOST_ONLY:
            reasons.append(PipelineReasonCode.LOCALHOST_ONLY_PENDING_RIOT_CONTEXT)
        return reasons

    def is_analysis_ready(self) -> bool:
        """True only when the bundle has the Riot-backed evidence required for analysis."""

        return not self.missing_requirements()


class PipelineCheckpoint(InternalContractModel):
    """Structured result for one pipeline stage."""

    stage: PipelineStage
    status: StageStatus
    reason_codes: list[PipelineReasonCode] = Field(default_factory=list)
    detail: str = Field(default="", max_length=500)

    def allows_progress(self, *, allow_degraded: bool = False) -> bool:
        """Determines whether downstream execution may continue from this checkpoint."""

        if self.status in {StageStatus.ACCEPTED, StageStatus.READY}:
            return True
        if allow_degraded and self.status is StageStatus.DEGRADED_SAFE:
            return True
        return False


class PipelineSnapshot(InternalContractModel):
    """Captures the current internal pipeline state plus its safe external summary."""

    match_id: str = Field(default="", max_length=80)
    riot_id: str = Field(default="", max_length=64)
    source: EvidenceSource | None = None
    bundle: AnalysisEvidenceBundle | None = None
    checkpoints: list[PipelineCheckpoint] = Field(default_factory=list)
    external_status: ExternalAnalysisStatus = ExternalAnalysisStatus.PENDING

    @property
    def latest_checkpoint(self) -> PipelineCheckpoint | None:
        """Returns the most recent checkpoint for status summarization."""

        if not self.checkpoints:
            return None
        return self.checkpoints[-1]
