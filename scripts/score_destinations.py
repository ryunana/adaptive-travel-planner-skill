#!/usr/bin/env python3
"""Deterministically score normalized destination candidates from JSON."""
from copy import deepcopy

from travel_common import JsonArgumentParser, emit, read_json

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
    invalid_states = [gate.get("state") for gate in gates if gate.get("state") not in {"pass", "fail", "undecidable"}]
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
    try:
        weights = {key: float(value) for key, value in weights.items()}
    except (TypeError, ValueError):
        return {"ok": False, "error": {"code": "invalid_weights", "message": "Weights must be numeric"}}
    if any(value < 0 for value in weights.values()) or abs(sum(weights.values()) - 100) > 1e-9:
        return {"ok": False, "error": {"code": "invalid_weights", "message": "Weights must be nonnegative and total 100"}}
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list) or any(not isinstance(candidate, dict) for candidate in raw_candidates):
        return {"ok": False, "error": {"code": "invalid_candidates", "message": "candidates must be an array of JSON objects"}}
    for candidate in raw_candidates:
        if not isinstance(candidate.get("dimensions", {}), dict) or not isinstance(candidate.get("hard_gates", []), list):
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "candidate dimensions must be an object and hard_gates must be an array"}}
        if any(not isinstance(gate, dict) for gate in candidate.get("hard_gates", [])):
            return {"ok": False, "error": {"code": "invalid_candidate", "message": "every hard gate must be a JSON object"}}
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
        result = {"ok": False, "error": {"code": "invalid_input", "message": str(exc)}}
    return emit(result, 0 if result.get("ok") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
