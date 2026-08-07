#!/usr/bin/env python3
"""Validate itinerary dates, load, topology, and dynamic evidence."""
from datetime import date

from travel_common import JsonArgumentParser, TravelInputError, emit, read_json


def issue(code, message, path=None):
    value = {"code": code, "message": message}
    if path:
        value["path"] = path
    return value


def validate(payload):
    issues = []
    if not isinstance(payload, dict):
        return {"ok": False, "issue_count": 1, "issues": [issue("invalid_input", "Input must be a JSON object")]}
    days_value = payload.get("days", [])
    if not isinstance(days_value, list) or any(not isinstance(day, dict) for day in days_value):
        return {"ok": False, "issue_count": 1, "issues": [issue("invalid_days", "days must be an array of JSON objects", "days")]}
    route_value = payload.get("route", [])
    if not isinstance(route_value, list) or any(not isinstance(location, str) for location in route_value):
        return {"ok": False, "issue_count": 1, "issues": [issue("invalid_route", "route must be an array of strings", "route")]}
    claims_value = payload.get("dynamic_claims", [])
    if not isinstance(claims_value, list) or any(not isinstance(claim, dict) for claim in claims_value):
        return {"ok": False, "issue_count": 1, "issues": [issue("invalid_dynamic_claims", "dynamic_claims must be an array of JSON objects", "dynamic_claims")]}
    try:
        start = date.fromisoformat(payload["start_date"])
        end = date.fromisoformat(payload["end_date"])
        if end < start:
            issues.append(issue("date_range_invalid", "end_date precedes start_date"))
            expected_days = expected_nights = 0
        else:
            expected_nights = (end - start).days
            expected_days = expected_nights + 1
        hotel_nights = payload.get("hotel_nights")
        if isinstance(hotel_nights, bool) or not isinstance(hotel_nights, int) or hotel_nights < 0:
            issues.append(issue("hotel_nights_invalid", "hotel_nights must be a nonnegative integer", "hotel_nights"))
        elif hotel_nights != expected_nights:
            issues.append(issue("hotel_nights_mismatch", "hotel_nights must equal the number of nights in the date range", "hotel_nights"))
        days = payload.get("days", [])
        if len(days) != expected_days:
            issues.append(issue("day_count_mismatch", "days must contain one entry for every calendar date", "days"))
        expected_dates = [(start.fromordinal(start.toordinal() + offset)).isoformat() for offset in range(expected_days)]
        actual_dates = [day.get("date") for day in days]
        if len(days) == expected_days and actual_dates != expected_dates:
            issues.append(issue("day_dates_mismatch", "day dates must be consecutive and match the trip range", "days"))
    except (KeyError, TypeError, ValueError):
        issues.append(issue("date_format_invalid", "start_date and end_date must be ISO calendar dates"))
        days = payload.get("days", [])

    limit = payload.get("max_core_activities_per_day", 1)
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        issues.append(issue("load_limit_invalid", "max_core_activities_per_day must be a nonnegative integer"))
    for index, day in enumerate(days):
        activities = day.get("core_activities", [])
        path = f"days[{index}].core_activities"
        if not isinstance(activities, list):
            issues.append(issue("invalid_core_activities", "core_activities must be an array", path))
        elif isinstance(limit, int) and not isinstance(limit, bool) and limit >= 0 and len(activities) > limit:
            issues.append(issue("core_activity_overload", "day exceeds the declared core-activity limit", path))

    route = payload.get("route", [])
    first_seen = {}
    for index, location in enumerate(route):
        if location in first_seen and index - first_seen[location] > 1:
            issues.append(issue("route_backtracking", "route returns to a previously departed location", f"route[{index}]"))
            break
        first_seen[location] = index

    allowed_status = {"verified", "auxiliary", "unknown", "login_required"}
    for index, claim in enumerate(payload.get("dynamic_claims", [])):
        status = claim.get("status")
        path = f"dynamic_claims[{index}]"
        if not isinstance(status, str) or status not in allowed_status:
            issues.append(issue("evidence_status_invalid", "dynamic claim has an invalid evidence status", path))
            continue
        source = claim.get("source")
        queried_at = claim.get("queried_at")
        invalid_fields = False
        if source is not None and (not isinstance(source, str) or not source.strip()):
            issues.append(issue("evidence_source_invalid", "dynamic claim source must be a non-empty string", path))
            invalid_fields = True
        if queried_at is not None and (not isinstance(queried_at, str) or not queried_at.strip()):
            issues.append(issue("evidence_query_time_invalid", "dynamic claim query time must be a non-empty string", path))
            invalid_fields = True
        stated = claim.get("value") not in (None, "")
        supported = status in {"verified", "auxiliary"} and source and queried_at and not invalid_fields
        if stated and not supported:
            issues.append(issue("unsupported_dynamic_claim", "a stated dynamic value requires verified/auxiliary evidence, source, and query time", path))
    return {"ok": not issues, "issue_count": len(issues), "issues": issues}


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        result = validate(read_json(args.input))
    except (OSError, ValueError) as exc:
        code = exc.code if isinstance(exc, TravelInputError) else "invalid_input"
        result = {"ok": False, "issue_count": 1, "issues": [issue(code, str(exc))]}
    return emit(result, 0 if result["ok"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
