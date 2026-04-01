"""Pure helpers for building, gating, and summarizing evidence pipeline state."""

from __future__ import annotations

from analysis_contracts import (
    AnalysisEvidenceBundle,
    EvidenceSource,
    ExternalAnalysisStatus,
    PipelineCheckpoint,
    PipelineReasonCode,
    PipelineSnapshot,
    PipelineStage,
    StageStatus,
)
from context_builder import MatchContext
from schemas import LocalEventUpload


def _determine_source(
    *,
    match_context: MatchContext | None,
    local_events: list[LocalEventUpload],
) -> EvidenceSource:
    """Normalizes the incoming evidence shape into one explicit source state."""

    if match_context is not None and local_events:
        return EvidenceSource.RIOT_PLUS_LOCAL
    if match_context is not None:
        return EvidenceSource.RIOT_ONLY
    return EvidenceSource.LOCALHOST_ONLY


def _build_initial_checkpoint(bundle: AnalysisEvidenceBundle) -> PipelineCheckpoint:
    """Creates the fail-closed checkpoint that represents bundle readiness."""

    reasons = bundle.missing_requirements()
    if bundle.source is EvidenceSource.LOCALHOST_ONLY:
        return PipelineCheckpoint(
            stage=PipelineStage.CONTEXT_BUILD,
            status=StageStatus.INCOMPLETE_EVIDENCE,
            reason_codes=reasons,
            detail="Localhost evidence is stored, but Riot context is still required.",
        )
    if reasons:
        return PipelineCheckpoint(
            stage=PipelineStage.CONTEXT_BUILD,
            status=StageStatus.BLOCKED,
            reason_codes=reasons,
            detail="Evidence bundle is missing required Riot-backed context.",
        )
    if bundle.source is EvidenceSource.RIOT_ONLY:
        return PipelineCheckpoint(
            stage=PipelineStage.CONTEXT_BUILD,
            status=StageStatus.DEGRADED_SAFE,
            reason_codes=[],
            detail="Riot-only evidence is usable internally, but not equivalent to full evidence.",
        )
    return PipelineCheckpoint(
        stage=PipelineStage.CONTEXT_BUILD,
        status=StageStatus.READY,
        reason_codes=[],
        detail="Riot and localhost evidence are normalized into one analysis-ready bundle.",
    )


def build_analysis_evidence_bundle(
    *,
    riot_id: str,
    match_context: MatchContext | None = None,
    local_events: list[LocalEventUpload] | None = None,
    match_id: str = "",
    image_paths: list[str] | None = None,
    analysis_text: str = "",
    analysis_payload: dict | None = None,
) -> PipelineSnapshot:
    """Builds the backend-owned evidence bundle and its initial checkpoint snapshot."""

    normalized_events = list(local_events or [])
    normalized_images = list(image_paths or [])
    source = _determine_source(match_context=match_context, local_events=normalized_events)
    resolved_match_id = match_id or (match_context.match_id if match_context is not None else "")
    bundle = AnalysisEvidenceBundle(
        match_id=resolved_match_id,
        riot_id=riot_id,
        source=source,
        match_context=match_context,
        local_events=normalized_events,
        image_paths=normalized_images,
        analysis_text=analysis_text,
        analysis_payload=dict(analysis_payload or {}),
    )
    checkpoint = _build_initial_checkpoint(bundle)
    snapshot = PipelineSnapshot(
        match_id=bundle.match_id,
        riot_id=bundle.riot_id,
        source=bundle.source,
        bundle=bundle,
        checkpoints=[checkpoint],
    )
    return snapshot.model_copy(update={"external_status": summarize_external_status(snapshot)})


def gate_pipeline_stage(
    stage: PipelineStage,
    *,
    bundle: AnalysisEvidenceBundle | None = None,
    checkpoint: PipelineCheckpoint | None = None,
    allow_degraded: bool = False,
) -> PipelineCheckpoint:
    """Applies deterministic downstream gating using bundle completeness and prior status."""

    reasons: list[PipelineReasonCode] = []
    if bundle is None:
        reasons.append(PipelineReasonCode.MISSING_BUNDLE)
    else:
        reasons.extend(bundle.missing_requirements())

    if checkpoint is None:
        reasons.append(PipelineReasonCode.MISSING_CHECKPOINT)
        return PipelineCheckpoint(
            stage=stage,
            status=StageStatus.BLOCKED,
            reason_codes=reasons,
            detail="A stage cannot proceed without a prior checkpoint result.",
        )

    if checkpoint.status in {StageStatus.INVALID_INPUT, StageStatus.INCOMPLETE_EVIDENCE, StageStatus.BLOCKED}:
        return PipelineCheckpoint(
            stage=stage,
            status=StageStatus.BLOCKED,
            reason_codes=checkpoint.reason_codes or reasons,
            detail="Downstream execution is blocked by an earlier checkpoint failure.",
        )

    if checkpoint.status is StageStatus.DEGRADED_SAFE:
        if allow_degraded:
            return PipelineCheckpoint(
                stage=stage,
                status=StageStatus.DEGRADED_SAFE,
                reason_codes=checkpoint.reason_codes,
                detail="Stage is allowed to proceed under explicit degraded-safe rules.",
            )
        return PipelineCheckpoint(
            stage=stage,
            status=StageStatus.BLOCKED,
            reason_codes=checkpoint.reason_codes,
            detail="Degraded-safe output cannot continue without an explicit override.",
        )

    if reasons:
        return PipelineCheckpoint(
            stage=stage,
            status=StageStatus.BLOCKED,
            reason_codes=reasons,
            detail="Downstream execution is blocked until required evidence is present.",
        )

    return PipelineCheckpoint(
        stage=stage,
        status=StageStatus.READY,
        reason_codes=[],
        detail="Stage can proceed with a verified evidence bundle.",
    )


def summarize_external_status(snapshot: PipelineSnapshot) -> ExternalAnalysisStatus:
    """Maps detailed internal pipeline state to a safe product-facing status."""

    checkpoint = snapshot.latest_checkpoint
    if checkpoint is None:
        return ExternalAnalysisStatus.PENDING
    if checkpoint.status is StageStatus.READY:
        return ExternalAnalysisStatus.READY
    if checkpoint.status is StageStatus.DEGRADED_SAFE:
        return ExternalAnalysisStatus.PENDING
    if checkpoint.status is StageStatus.INVALID_INPUT:
        return ExternalAnalysisStatus.FAILED
    if checkpoint.status is StageStatus.BLOCKED:
        if any(
            reason in checkpoint.reason_codes
            for reason in (
                PipelineReasonCode.MISSING_MATCH_ID,
                PipelineReasonCode.MISSING_MATCH_CONTEXT,
                PipelineReasonCode.MISSING_LOCAL_EVENTS,
                PipelineReasonCode.LOCALHOST_ONLY_PENDING_RIOT_CONTEXT,
            )
        ):
            return ExternalAnalysisStatus.INSUFFICIENT_DATA
        return ExternalAnalysisStatus.FAILED
    return ExternalAnalysisStatus.PENDING
