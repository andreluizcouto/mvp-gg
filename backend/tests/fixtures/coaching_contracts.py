"""Shared payload factories for coaching/status regression contracts."""


def ready_snapshot() -> dict:
    return {
        "stage": "delivery",
        "status": "ready",
        "source": "riot_plus_local",
        "reason_codes": [],
        "external_status": "ready",
        "has_analysis_text": True,
    }


def pending_snapshot() -> dict:
    return {
        "stage": "analysis_generation",
        "status": "incomplete_evidence",
        "source": "localhost_only",
        "reason_codes": ["missing_match_context"],
        "external_status": "pending",
        "has_analysis_text": False,
    }


def insufficient_snapshot() -> dict:
    return {
        "stage": "delivery",
        "status": "blocked",
        "source": "riot_only",
        "reason_codes": ["missing_local_evidence"],
        "external_status": "insufficient_data",
        "has_analysis_text": False,
    }


def failed_snapshot() -> dict:
    return {
        "stage": "analysis_generation",
        "status": "failed",
        "source": "riot_plus_local",
        "reason_codes": ["provider_error"],
        "external_status": "failed",
        "has_analysis_text": False,
    }
