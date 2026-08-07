import math
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
    def test_requires_one_to_three_complete_candidates(self):
        import score_destinations
        invalid_payloads = (
            {"candidates": []},
            {"candidates": [candidate(str(index)) for index in range(4)]},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                result = score_destinations.score_payload(payload)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_candidates")

        for field, value in (
            ("normalized_form", " "),
            ("minimum_viable_days", 0),
            ("minimum_viable_days", True),
            ("minimum_viable_days", math.nan),
            ("destination_potential", []),
            ("this_trip_suitability", {}),
            ("better_window", 3),
        ):
            item = candidate("A")
            item[field] = value
            with self.subTest(field=field, value=value):
                result = score_destinations.score_payload({"candidates": [item]})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_candidate")

    def test_unknown_gate_evidence_requires_complete_undecidable_gate(self):
        import score_destinations
        for gate in (
            {"name": "transport", "state": "pass", "evidence_status": "unknown"},
            {"name": "transport", "state": "fail", "evidence_status": "login_required"},
            {"name": "", "state": "undecidable", "evidence_status": "unknown", "resolution_action": "verify"},
            {"name": "transport", "state": "undecidable", "evidence_status": "unknown", "resolution_action": " "},
        ):
            with self.subTest(gate=gate):
                result = score_destinations.score_payload({"candidates": [candidate("A", gates=[gate])]})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_candidate")

    def test_weights_reject_nonfinite_and_boolean_values(self):
        import score_destinations
        for invalid in (math.nan, math.inf, -math.inf, True, False):
            with self.subTest(invalid=invalid):
                weights = dict(score_destinations.DEFAULT_WEIGHTS)
                weights["preference_fit"] = invalid
                result = score_destinations.score_payload({"weights": weights, "candidates": []})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_weights")

    def test_huge_integers_are_rejected_without_overflow(self):
        import score_destinations
        huge = 10 ** 400
        weights = dict(score_destinations.DEFAULT_WEIGHTS, preference_fit=huge)
        self.assertEqual(score_destinations.score_payload({"weights": weights, "candidates": [candidate("A")]})["error"]["code"], "invalid_weights")
        item = candidate("A")
        item["minimum_viable_days"] = huge
        self.assertEqual(score_destinations.score_payload({"candidates": [item]})["error"]["code"], "invalid_candidate")
        item = candidate("A")
        item["dimensions"]["preference_fit"]["score"] = huge
        self.assertEqual(score_destinations.score_payload({"candidates": [item]})["error"]["code"], "invalid_candidate")

    def test_deep_pending_gate_is_rejected_before_copying(self):
        import score_destinations
        deep = value = {}
        for _ in range(300):
            value["child"] = {}
            value = value["child"]
        gate = {"name": "inventory", "state": "undecidable", "evidence_status": "unknown", "resolution_action": "check", "extra": deep}
        result = score_destinations.score_payload({"candidates": [candidate("A", gates=[gate])]})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_candidate")

    def test_candidate_shapes_are_validated_before_scoring(self):
        import score_destinations
        cases = []
        for mutation in (
            lambda item: item.update(name="   "),
            lambda item: item.update(dimensions=[]),
            lambda item: item.update(hard_gates={}),
            lambda item: item["hard_gates"].append([]),
            lambda item: item["hard_gates"][0].update(state=[]),
            lambda item: item["hard_gates"][0].update(evidence_status=[]),
            lambda item: item["dimensions"]["preference_fit"].update(evidence_status=[]),
            lambda item: item["dimensions"]["preference_fit"].update(score=True),
            lambda item: item["dimensions"]["preference_fit"].update(score=math.inf),
        ):
            item = candidate("A")
            mutation(item)
            cases.append(item)
        for item in cases:
            with self.subTest(item=item):
                result = score_destinations.score_payload({"candidates": [item]})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_candidate")

    def test_default_weights_total_100_remain_valid(self):
        import score_destinations
        result = score_destinations.score_payload({"candidates": [candidate("A")]})
        self.assertTrue(result["ok"])
        self.assertEqual(sum(result["weights"].values()), 100)

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
