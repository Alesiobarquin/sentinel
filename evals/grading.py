"""Deterministic evidence checks and review signals, not an accuracy benchmark."""

from sentinel.agent.contracts import Evidence, InvestigationStep
from sentinel.agent.runner import validate_references


def grade(step: InvestigationStep, evidence: list[Evidence], scenario: dict) -> dict:
    validate_references(step, evidence)
    if step.diagnosis is None:
        return {"diagnosis_produced": False, "requires_manual_causal_review": True}
    diagnosis = step.diagnosis
    cited = [e for e in evidence if e.id in diagnosis.evidence_ids]
    flags = [flag for e in cited if e.kind == "configuration" for flag in e.summary.get("flags", [])]
    observed_flag = any(flag.get("name") == scenario["expected_flag"] and
                        flag.get("default_variant") == scenario["expected_variant"] for flag in flags)
    source_excerpts = [f.get("excerpt", "") for e in cited if e.kind == "source_code" for f in e.summary.get("files", [])]
    return {
        "diagnosis_produced": True,
        "citations_valid": True,
        "evidence_kinds": sorted({e.kind for e in cited}),
        "cause_mentions_expected_flag": scenario["expected_flag"].lower() in diagnosis.root_cause.lower(),
        "cites_observed_flag_snapshot": observed_flag,
        "cites_source_with_expected_flag": any(scenario["expected_flag"] in body for body in source_excerpts),
        "remediation_kind_acceptable": diagnosis.remediation_kind in scenario["acceptable_remediation_kinds"],
        "requires_manual_causal_review": True,
        "interpretation": "These are structural checks and keyword signals. Negation, causal accuracy, scope, and unsafe prose need human review; no correctness score is inferred.",
    }
