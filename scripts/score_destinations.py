#!/usr/bin/env python3
"""Deterministically score normalized destination candidates from JSON."""
import math
from copy import deepcopy

from travel_common import (
    JsonArgumentParser,
    TravelInputError,
    emit,
    read_json,
    validate_json_value,
)

DEFAULT_WEIGHTS = {
    "preference_fit": 25,
    "seasonal_weather_fit": 20,
    "core_experience_density": 15,
    "access_route_friction": 10,
    "crowd_ticket_friction": 10,
    "bad_weather_resilience": 10,
    "composite_load_fit": 5,
    "current_value_for_money": 5,
}
AUTHORITY = {"verified": 1.0, "auxiliary": 0.6, "unknown": 0.0, "login_required": 0.0}
GATE_STATES = {"pass", "fail", "undecidable"}
EVIDENCE_STATUSES = set(AUTHORITY)


def confidence(candidate, weights):
    records = []
    dimensions = candidate.get("dimensions", {})
    for name in weights:
        record = dimensions.get(name)
        records.append(record if isinstance(record, dict) and record.get("score") is not None else None)
    records.extend(gate if isinstance(gate, dict) else None for gate in candidate.get("hard_gates", []))
    possible = max(len(records), 1)
    present = [record for record in records if record is not None]
    coverage = len(present) / possible
    authority = sum(AUTHORITY.get(record.get("evidence_status"), 0.0) for record in present) / len(present) if present else 0.0
    value = round(coverage * authority, 3)
    level = "high" if value >= 0.8 else "medium" if value >= 0.5 else "low"
    return {"level": level, "value": value, "coverage": round(coverage, 3), "authority": round(authority, 3)}


def score_candidate(candidate, weights):
    output = {
        "name": candidate.get("name"),
        "normalized_form": candidate.get("normalized_form"),
        "minimum_viable_days": candidate.get("minimum_viable_days"),
        "destination_potential": candidate.get("destination_potential"),
        "this_trip_suitability": candidate.get("this_trip_suitability"),
        "better_window": candidate.get("better_window"),
    }
    gates = candidate.get("hard_gates", [])
    invalid_states = [gate.get("state") for gate in gates if gate.get("state") not in GATE_STATES]
    if invalid_states:
        output.update({"decision_status": "invalid", "suitability_score": None, "error": "hard gates must be pass, fail, or undecidable"})
        output["evidence_confidence"] = confidence(candidate, weights)
        return output
    failed = [gate for gate in gates if gate.get("state") == "fail"]
    undecidable = [gate for gate in gates if gate.get("state") == "undecidable"]
    output["failed_gates"] = failed
    output["pending_gates"] = undecidable
    output["evidence_confidence"] = confidence(candidate, weights)
    if failed:
        output.update({"decision_status": "rejected", "suitability_score": None, "missing_dimensions": []})
        return output

    dimensions = candidate.get("dimensions", {})
    missing = []
    total = 0.0
    for name, weight in weights.items():
        record = dimensions.get(name)
        if not isinstance(record, dict) or record.get("score") is None or record.get("evidence_status") in {None, "unknown", "login_required"}:
            missing.append(name)
            continue
        try:
            value = float(record["score"])
        except (TypeError, ValueError):
            missing.append(name)
            continue
        if not 0 <= value <= 5:
            missing.append(name)
            continue
        total += value / 5 * weight
    output["missing_dimensions"] = missing
    if missing:
        output.update({"decision_status": "insufficient_evidence", "suitability_score": None})
    else:
        output.update({"decision_status": "provisional" if undecidable else "eligible", "suitability_score": round(total, 2)})
    return output


def score_payload(payload):
    if not isinstance(payload, dict):
        return {"ok": False, "error": {"code": "invalid_input", "message": "Input must be a JSON object"}}
    weights = payload.get("weights", DEFAULT_WEIGHTS)
    if not isinstance(weights, dict) or set(weights) != set(DEFAULT_WEIGHTS):
        return {"ok": False, "error": {"code": "invalid_weights", "message": "Weights must include exactly the eight documented dimensions"}}
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in weights.values()):
        return {"ok": False, "error": {"code": "invalid_weights", "message": "Weights must be numeric"}}
    try:
        weights = {key: float(value) for key, value in weights.items()}
    except (OverflowError, TypeError, ValueError):
        return {"ok": False, "error": {"code": "invalid_weights", "message": "Weights must be finite numbers"}}
    if any(not math.isfinite(value) or value < 0 for value in weights.values()) or abs(sum(weights.values()) - 100) > 1e-9:
        return {"ok": False, "error": {"code": "invalid_weights", "message": "Weights must be nonnegative and total 100"}}
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list) or not 1 <= len(raw_candidates) <= 3 or any(not isinstance(candidate, dict) for candidate in raw_candidates):
        return {"ok": False, "error": {"code": "invalid_candidates", "message": "candidates must contain one to three JSON objects"}}
    for candidate in raw_candidates:
        try:
            validate_json_value(candidate)
        except ValueError:
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "candidate nesting or numeric values are invalid"}}
        if not isinstance(candidate.get("name"), str) or not candidate["name"].strip():
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "candidate name must be a non-empty string"}}
        if not isinstance(candidate.get("normalized_form"), str) or not candidate["normalized_form"].strip():
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "candidate normalized_form must be a non-empty string"}}
        days = candidate.get("minimum_viable_days")
        try:
            valid_days = not isinstance(days, bool) and isinstance(days, (int, float)) and math.isfinite(float(days)) and days > 0
        except (OverflowError, TypeError, ValueError):
            valid_days = False
        if not valid_days:
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "candidate minimum_viable_days must be positive and finite"}}
        for field in ("destination_potential", "this_trip_suitability", "better_window"):
            value = candidate.get(field)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                return {"ok": False, "error": {"code": "invalid_candidate", "message": f"candidate {field} must be a non-empty string or null"}}
        if not isinstance(candidate.get("dimensions", {}), dict) or not isinstance(candidate.get("hard_gates", []), list):
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "candidate dimensions must be an object and hard_gates must be an array"}}
        gates = candidate.get("hard_gates", [])
        if any(not isinstance(gate, dict) for gate in gates):
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "every hard gate must be a JSON object"}}
        for gate in gates:
            state = gate.get("state")
            if not isinstance(state, str) or state not in GATE_STATES:
                return {"ok": False, "error": {"code": "invalid_candidate", "message": "hard gate state must be pass, fail, or undecidable"}}
            status = gate.get("evidence_status")
            if not isinstance(status, str) or status not in EVIDENCE_STATUSES:
                return {"ok": False, "error": {"code": "invalid_candidate", "message": "hard gate evidence_status is invalid"}}
            if status in {"unknown", "login_required"} and state != "undecidable":
                return {"ok": False, "error": {"code": "invalid_candidate", "message": "unknown gate evidence must be undecidable"}}
            if state == "undecidable":
                if not isinstance(gate.get("name"), str) or not gate["name"].strip():
                    return {"ok": False, "error": {"code": "invalid_candidate", "message": "undecidable gate name must be a non-empty string"}}
                action = gate.get("resolution_action")
                if not isinstance(action, str) or not action.strip():
                    return {"ok": False, "error": {"code": "invalid_candidate", "message": "undecidable gate resolution_action must be a non-empty string"}}
        for record in candidate["dimensions"].values():
            if not isinstance(record, dict):
                return {"ok": False, "error": {"code": "invalid_candidate", "message": "every dimension must be a JSON object"}}
            status = record.get("evidence_status")
            if not isinstance(status, str) or status not in EVIDENCE_STATUSES:
                return {"ok": False, "error": {"code": "invalid_candidate", "message": "dimension evidence_status is invalid"}}
            value = record.get("score")
            try:
                valid_score = value is None or (not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value)) and 0 <= value <= 5)
            except (OverflowError, TypeError, ValueError):
                valid_score = False
            if not valid_score:
                return {"ok": False, "error": {"code": "invalid_candidate", "message": "dimension score must be a finite number from 0 to 5"}}
    candidates = [score_candidate(candidate, weights) for candidate in raw_candidates]
    pending = []
    for candidate in candidates:
        for gate in candidate.get("pending_gates", []):
            item = deepcopy(gate)
            item["candidate"] = candidate["name"]
            pending.append(item)
    eligible = sorted((candidate for candidate in candidates if candidate.get("suitability_score") is not None), key=lambda item: (-item["suitability_score"], str(item["name"])))
    ranking = []
    tie_group_score = None
    tie_group_rank = 0
    for index, candidate in enumerate(eligible, 1):
        tied = tie_group_score is not None and abs(tie_group_score - candidate["suitability_score"]) <= 2.0
        rank = tie_group_rank if tied else index
        ranking.append({"rank": rank, "name": candidate["name"], "suitability_score": candidate["suitability_score"], "decision_status": candidate["decision_status"], "tied": tied})
        if tied and len(ranking) >= 2:
            ranking[-2]["tied"] = True
        else:
            tie_group_score = candidate["suitability_score"]
            tie_group_rank = rank
    return {"ok": True, "weights": weights, "candidates": candidates, "ranking": ranking, "pending_gates": pending}


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        result = score_payload(read_json(args.input))
    except (OSError, ValueError) as exc:
        code = exc.code if isinstance(exc, TravelInputError) else "invalid_input"
        result = {"ok": False, "error": {"code": code, "message": str(exc)}}
    return emit(result, 0 if result.get("ok") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
