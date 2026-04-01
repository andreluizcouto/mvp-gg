"""Regression coverage for internal evidence pipeline contracts."""

from analysis_contracts import (
    EvidenceSource,
    ExternalAnalysisStatus,
    PipelineReasonCode,
    PipelineStage,
    StageStatus,
)
from context_builder import MatchContext
from db import _normalize_snapshot_payload
from evidence_pipeline import (
    build_analysis_evidence_bundle,
    gate_pipeline_stage,
    summarize_external_status,
)
from schemas import LocalEventUpload


def _make_match_context() -> MatchContext:
    """Builds the minimal Riot-backed context needed for pipeline tests."""

    return MatchContext(
        match_id="BR1_123456789",
        player_riot_id="tester#BR1",
        player_champion="Ahri",
        role="MIDDLE",
        win=True,
        duration_min=30.2,
        kda="8/2/10",
        cs_per_min=7.5,
        vision_score=21,
        kill_participation_pct=63.0,
        damage_share_pct=28.4,
        time_dead_pct=2.5,
    )


def _make_local_events() -> list[LocalEventUpload]:
    """Builds representative localhost evidence for bundle normalization tests."""

    return [
        LocalEventUpload(
            event_type="kill",
            game_time="12:34",
            champion="Ahri",
            detail="Picked the enemy support before dragon.",
            assisters=["Jarvan IV"],
            minimap_base64="MDEyMzQ1Njc4OWFiY2RlZg==",
        )
    ]


def test_builds_normalized_bundle_from_riot_and_local():
    snapshot = build_analysis_evidence_bundle(
        riot_id="tester#BR1",
        match_context=_make_match_context(),
        local_events=_make_local_events(),
        image_paths=["C:/tmp/minimap-1.png"],
    )

    assert snapshot.bundle is not None
    assert snapshot.bundle.source is EvidenceSource.RIOT_PLUS_LOCAL
    assert snapshot.bundle.match_context is not None
    assert snapshot.bundle.local_events
    assert snapshot.latest_checkpoint is not None
    assert snapshot.latest_checkpoint.status is StageStatus.READY
    assert snapshot.latest_checkpoint.reason_codes == []


def test_incomplete_bundle_returns_checkpoint_reason():
    snapshot = build_analysis_evidence_bundle(
        riot_id="tester#BR1",
        local_events=_make_local_events(),
    )

    assert snapshot.bundle is not None
    assert snapshot.bundle.source is EvidenceSource.LOCALHOST_ONLY
    assert snapshot.latest_checkpoint is not None
    assert snapshot.latest_checkpoint.status in {
        StageStatus.INCOMPLETE_EVIDENCE,
        StageStatus.BLOCKED,
    }
    assert PipelineReasonCode.LOCALHOST_ONLY_PENDING_RIOT_CONTEXT in snapshot.latest_checkpoint.reason_codes
    assert PipelineReasonCode.MISSING_MATCH_CONTEXT in snapshot.latest_checkpoint.reason_codes


def test_stage_results_gate_downstream_execution():
    ready_snapshot = build_analysis_evidence_bundle(
        riot_id="tester#BR1",
        match_context=_make_match_context(),
        local_events=_make_local_events(),
    )
    incomplete_snapshot = build_analysis_evidence_bundle(
        riot_id="tester#BR1",
        local_events=_make_local_events(),
    )

    ready_gate = gate_pipeline_stage(
        PipelineStage.ANALYSIS_GENERATION,
        bundle=ready_snapshot.bundle,
        checkpoint=ready_snapshot.latest_checkpoint,
    )
    blocked_gate = gate_pipeline_stage(
        PipelineStage.ANALYSIS_GENERATION,
        bundle=incomplete_snapshot.bundle,
        checkpoint=incomplete_snapshot.latest_checkpoint,
    )

    degraded_gate = gate_pipeline_stage(
        PipelineStage.DELIVERY,
        checkpoint=ready_gate.model_copy(update={"status": StageStatus.DEGRADED_SAFE}),
        allow_degraded=True,
    )

    assert ready_gate.status is StageStatus.READY
    assert blocked_gate.status is StageStatus.BLOCKED
    assert PipelineReasonCode.MISSING_MATCH_CONTEXT in blocked_gate.reason_codes
    assert degraded_gate.status is StageStatus.DEGRADED_SAFE

    assert summarize_external_status(ready_snapshot) is ExternalAnalysisStatus.READY
    assert summarize_external_status(
        ready_snapshot.model_copy(update={"checkpoints": [degraded_gate]})
    ) is ExternalAnalysisStatus.PENDING
    assert summarize_external_status(incomplete_snapshot) is ExternalAnalysisStatus.PENDING
    assert summarize_external_status(
        incomplete_snapshot.model_copy(update={"checkpoints": [blocked_gate]})
    ) is ExternalAnalysisStatus.INSUFFICIENT_DATA


def test_summarize_external_status_degraded_safe_is_not_ready():
    snapshot = build_analysis_evidence_bundle(
        riot_id="tester#BR1",
        match_context=_make_match_context(),
        local_events=_make_local_events(),
    )
    degraded_checkpoint = gate_pipeline_stage(
        PipelineStage.DELIVERY,
        checkpoint=snapshot.latest_checkpoint.model_copy(update={"status": StageStatus.DEGRADED_SAFE}),
        allow_degraded=True,
    )
    degraded_snapshot = snapshot.model_copy(update={"checkpoints": [degraded_checkpoint]})

    assert summarize_external_status(degraded_snapshot) is ExternalAnalysisStatus.PENDING


def test_summarize_external_status_localhost_only_is_pending():
    snapshot = build_analysis_evidence_bundle(
        riot_id="tester#BR1",
        local_events=_make_local_events(),
    )

    assert snapshot.bundle is not None
    assert snapshot.bundle.source is EvidenceSource.LOCALHOST_ONLY
    assert summarize_external_status(snapshot) is ExternalAnalysisStatus.PENDING


def test_snapshot_normalization_marks_weak_signal_as_insufficient_data():
    normalized = _normalize_snapshot_payload(
        {
            "stage": "delivery",
            "status": "ready",
            "source": "riot_plus_local",
            "reason_codes": [],
            "external_status": "ready",
            "has_analysis_text": True,
            "weak_signal": True,
        }
    )

    assert normalized["source"] == "riot_plus_local"
    assert normalized["weak_signal"] is True
    assert normalized["external_status"] == "insufficient_data"
