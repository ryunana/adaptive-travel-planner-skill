import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DIMS = ["preference_fit", "seasonal_weather_fit", "core_experience_density", "access_route_friction", "crowd_ticket_friction", "bad_weather_resilience", "composite_load_fit", "current_value_for_money"]


def candidate(name, score: float = 4.0, status="verified", gates=None):
    return {
        "name": name,
        "normalized_form": name + " 5-day route",
        "minimum_viable_days": 5,
        "hard_gates": gates if gates is not None else [{"name": "transport", "state": "pass", "evidence_status": "verified"}],
        "dimensions": {dimension: {"score": score, "evidence_status": status} for dimension in DIMS},
        "destination_potential": "high",
        "this_trip_suitability": "good",
        "better_window": None,
    }


class ScoreTests(unittest.TestCase):
    def test_hard_gate_fail_rejects_before_scoring(self):
        import score_destinations
        item = candidate("A", gates=[{"name": "closure", "state": "fail", "evidence_status": "verified"}])
        result = score_destinations.score_payload({"candidates": [item]})
        scored = result["candidates"][0]
        self.assertEqual(scored["decision_status"], "rejected")
        self.assertIsNone(scored["suitability_score"])

    def test_missing_dimension_refuses_score_and_reduces_coverage(self):
        import score_destinations
        item = candidate("A")
        item["dimensions"].pop("seasonal_weather_fit")
        result = score_destinations.score_payload({"candidates": [item]})["candidates"][0]
        self.assertIsNone(result["suitability_score"])
        self.assertEqual(result["decision_status"], "insufficient_evidence")
        self.assertIn("seasonal_weather_fit", result["missing_dimensions"])
        self.assertEqual(result["evidence_confidence"]["coverage"], 0.889)
        self.assertLess(result["evidence_confidence"]["value"], 1.0)

    def test_auxiliary_evidence_scores_but_reduces_confidence(self):
        import score_destinations
        result = score_destinations.score_payload({"candidates": [candidate("A", status="auxiliary")]})["candidates"][0]
        self.assertEqual(result["suitability_score"], 80.0)
        self.assertEqual(result["evidence_confidence"]["level"], "medium")

    def test_undecidable_gate_is_provisional_and_pending(self):
        import score_destinations
        gate = {"name": "rail inventory", "state": "undecidable", "evidence_status": "login_required", "resolution_action": "check the named train in 12306"}
        result = score_destinations.score_payload({"candidates": [candidate("A", gates=[gate])]})
        self.assertEqual(result["candidates"][0]["decision_status"], "provisional")
        self.assertEqual(result["pending_gates"][0]["resolution_action"], gate["resolution_action"])

    def test_close_scores_are_a_tie(self):
        import score_destinations
        a = candidate("A", score=4)
        b = candidate("B", score=4)
        b["dimensions"]["current_value_for_money"]["score"] = 3
        result = score_destinations.score_payload({"candidates": [a, b]})
        self.assertEqual(result["ranking"][0]["rank"], 1)
        self.assertEqual(result["ranking"][1]["rank"], 1)
        self.assertTrue(result["ranking"][0]["tied"])
        self.assertEqual(result["candidates"][0]["destination_potential"], "high")
        self.assertEqual(result["candidates"][0]["this_trip_suitability"], "good")

    def test_tie_group_compares_each_score_with_group_leader(self):
        import score_destinations
        result = score_destinations.score_payload({
            "candidates": [candidate("A", score=4.5), candidate("B", score=4.4), candidate("C", score=4.3)]
        })
        self.assertEqual([item["suitability_score"] for item in result["ranking"]], [90.0, 88.0, 86.0])
        self.assertEqual([item["rank"] for item in result["ranking"]], [1, 1, 3])
        self.assertEqual([item["tied"] for item in result["ranking"]], [True, True, False])

    def test_sparse_confidence_averages_authority_over_present_records(self):
        import score_destinations
        item = candidate("A")
        item["dimensions"] = {}
        confidence = score_destinations.confidence(item, score_destinations.DEFAULT_WEIGHTS)
        self.assertEqual(confidence["coverage"], 0.111)
        self.assertEqual(confidence["authority"], 1.0)
        self.assertEqual(confidence["value"], 0.111)

    def test_confidence_without_present_records_has_zero_authority(self):
        import score_destinations
        item = candidate("A", gates=[])
        item["dimensions"] = {}
        confidence = score_destinations.confidence(item, score_destinations.DEFAULT_WEIGHTS)
        self.assertEqual(confidence["coverage"], 0.0)
        self.assertEqual(confidence["authority"], 0.0)
        self.assertEqual(confidence["value"], 0.0)


if __name__ == "__main__": unittest.main()
