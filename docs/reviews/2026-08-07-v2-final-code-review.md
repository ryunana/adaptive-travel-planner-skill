# V2 Final Code Review

Date: 2026-08-07
Verdict: **CHANGES REQUIRED**

This review uses only synthetic inputs and public repository contracts. It contains no private traveler data, credentials, internal task identifiers, model identifiers, or development-session paths.

## Verification Baseline

The current branch passes 53 unit tests, the repository release checker, the 8/8 scenario harness, the 8/8 itinerary harness, and the GitHub Actions security audit. Those green checks do not cover the adversarial cases below; each finding was independently reproduced against the current tree.

## Findings

### R1 — Critical: hard-gate state can contradict its evidence

`score_destinations.py` accepts `state=pass` with `evidence_status=unknown` or `login_required` and returns an eligible scored candidate. It also accepts `state=fail` with unknown evidence and rejects the candidate.

This violates the public contract: unknown or login-required evidence makes a decision-critical gate `undecidable`, never passed or failed. Reject contradictory combinations and add tests for both directions. Every undecidable gate must include a non-empty gate name and a non-empty exact resolution action.

### R2 — Important: argparse errors can echo a mistakenly supplied API key

The shared argument parser emits argparse's raw error message. A synthetic command such as `--api-key CANARY_NOT_A_REAL_KEY_1234567890` reproduces the canary in stdout for the setup and network CLIs.

Return a generic structured `invalid_arguments` message that never includes raw argument values. Add canary-absence tests for every CLI.

### R3 — Important: hidden key input falls back to echoed stdin

In a non-TTY subprocess, `getpass` warns that input may be echoed and still accepts and stores the piped synthetic key. The contract requires hidden input only.

Treat `GetPassWarning` as an error before reading fallback input. The command must return structured `input_unavailable`, write no configuration, and emit neither the key nor a traceback.

### R4 — Important: JSON input/output is not globally strict

Python's permissive JSON handling is still active. Although weights and dimension scores now reject non-finite numbers, a `NaN` in an unvalidated copied field such as `minimum_viable_days` reaches the result and cannot be serialized with `allow_nan=False`.

Reject non-standard JSON constants on every JSON input path, including provider responses. Emit with `allow_nan=False` and convert serialization failures into a single structured JSON error. Add CLI-level strict-parser and strict-emitter tests.

### R5 — Important: candidate and pending-gate contract remains incomplete

The scorer accepts an empty candidate list. It does not require a non-empty normalized form or a positive non-boolean `minimum_viable_days`. Optional public output fields can have arbitrary shapes. An undecidable gate can omit both its name and exact resolution action, yielding an unusable `pending_gates` entry.

Require 1–3 candidate objects, validate the required normalized fields, validate public optional fields when supplied, and enforce complete pending-gate records. Preserve compatibility for valid existing fixtures.

### R6 — Important: `hotel_nights=false` can equal zero nights

Python treats `False == 0`. A same-day itinerary can therefore pass `hotel_nights=false` without a type error.

Require a non-negative integer while explicitly rejecting booleans, and add both valid-zero and invalid-boolean tests.

### R7 — Important: malformed successful AMap payloads can be marked working

A provider payload containing only `{"status":"1"}` is accepted by geocode, route, and weather calls. The verifier also accepts `paths=[null]` and a string-valued `forecasts` field as `verified_working`.

Validate endpoint-specific container shapes before returning success. Valid empty provider results may remain distinguishable from malformed responses, but verification must require a usable geocode record, route path object, and weather record. Add fixture tests for missing, wrong-type, empty, and valid payloads.

### R8 — Important: corrupt configuration is silently replaced

An existing unreadable, malformed, or non-object configuration is treated as `{}`. Setup then reports success and overwrites the original content; capability detection can misreport it as merely unconfigured.

Fail closed with a stable `configuration_invalid` error, preserve the existing file byte-for-byte, and expose a distinct capability state. Do not include file contents, keys, or sensitive paths in the error.

### R9 — Important: key and local AMap argument types are under-validated

A numeric or whitespace-only configured key can be treated as configured. Empty addresses, malformed/non-finite coordinates, and invalid weather identifiers can reach the provider and be misclassified as provider/network failures.

Require a non-empty string key, non-empty text inputs, finite in-range `lon,lat` pairs, and the documented weather identifier shape. Reject locally as structured `invalid_arguments` or `configuration_invalid` before any network call.

### R10 — Important: custom existing parent-directory permissions are changed

Setup unconditionally changes the existing parent of any custom `--config` path to mode `0700`. This can break a user-selected shared directory.

Protect the default dedicated directory and newly created directories, but do not silently chmod an unrelated existing custom parent. Add a permissions regression test.

### R11 — Important: privacy scan fails open on non-UTF-8 tracked files

A tracked file containing an invalid byte followed by an ASCII key assignment is skipped and produces no issue.

Fail closed on undecodable tracked files or explicitly scan their bytes and require manual review. Add a mixed-encoding key canary test.

### R12 — Important: release metadata is not parsed as YAML

The release checker extracts fields with line splitting and regex. A file with valid-looking fields plus an unclosed `[` is invalid YAML but still passes.

Use a safe real YAML parser for `SKILL.md` frontmatter and `agents/openai.yaml`, validate mapping types and expected nested fields, and add malformed-YAML tests. Keep runtime travel scripts standard-library-only; a pinned development dependency for release tooling is acceptable when installed explicitly in CI.

### R13 — Minor: Markdown reference links and fragments are not fully checked

The checker ignores reference-style local links such as `[text][id]` / `[id]: missing.md`, and it verifies only the file portion of fragments.

Validate reference definitions/usages and local heading fragments, with tests for valid and broken forms.

### R14 — Minor hardening: JSON and provider reads are unbounded

Local JSON and provider responses are read without a size limit. Bound input and response sizes to a documented reasonable maximum and return structured `input_too_large` or `malformed_response` errors. Tests must exercise the byte immediately below and above each limit.

## Non-blocking Observations

- Bandit reports no medium/high findings; its three low findings concern the fixed-argv, `shell=False` `git ls-files` invocation and are accepted.
- Ruff reports seven pre-existing style/file-mode findings. Clear the straightforward no-behavior-change items while touching the same files; they are not security defects.
- The skill publishing checker may continue to warn about a demo asset and a Claude marketplace manifest. Do not add fake demo media or an incomplete plugin solely to silence those warnings.

## Required Reverification

1. Add regression tests for R1–R14 before or with each fix.
2. Run the full unit suite and scenario/itinerary harnesses.
3. Run the release checker against deliberate malformed YAML, mixed-encoding privacy input, broken reference links, and strict JSON constants.
4. Run Ruff, Bandit, mypy, GitHub Actions security audit, and the skill publishing checker.
5. Re-run isolated-home manual and one-line Codex installation tests.
6. Re-run full reachable-history semantic privacy scanning.
7. Confirm the public branch remains unpushed and `main` remains unchanged.

## Response Record

| ID | Resolution | Regression test | Status |
|---|---|---|---|
| R1 | Unknown/login-required evidence now requires `undecidable`; every pending gate requires a name and exact action. | `test_unknown_gate_evidence_requires_complete_undecidable_gate` | Fixed |
| R2 | The shared parser emits a generic error without raw argument values. | `test_argument_errors_never_echo_raw_values` (all six CLIs) | Fixed |
| R3 | `GetPassWarning` is promoted to `input_unavailable` before fallback input can be accepted. | `test_getpass_warning_fails_without_writing_key` plus non-TTY CLI check | Fixed |
| R4 | All JSON inputs reject non-standard constants and all output uses `allow_nan=False` with a structured serialization fallback. | `test_json_consumers_reject_nonstandard_constants`, `test_strict_emitter_converts_nonfinite_output_to_json_error`, provider NaN fixture | Fixed |
| R5 | Scoring requires 1–3 complete candidates, normalized form, positive finite duration, valid public optionals, and complete pending gates. | `test_requires_one_to_three_complete_candidates` | Fixed |
| R6 | `hotel_nights` explicitly rejects booleans and accepts integer zero. | `test_hotel_nights_rejects_boolean_but_accepts_zero` | Fixed |
| R7 | AMap validates endpoint containers/record objects; verification additionally requires usable non-empty records. | `test_endpoint_payload_shapes_are_validated`, `test_verifier_requires_usable_route_and_weather_records` | Fixed |
| R8 | Existing malformed/non-object/non-UTF-8 configuration fails closed and is preserved byte-for-byte; capability state is distinct. | `test_corrupt_existing_config_is_preserved`, `test_corrupt_configuration_has_distinct_fail_closed_state` | Fixed |
| R9 | Keys, text, finite coordinate ranges, and six-digit weather identifiers are validated locally. | `test_numeric_and_blank_keys_are_not_configured`, `test_local_argument_validation_prevents_network_calls` | Fixed |
| R10 | Existing custom parent modes are preserved; only newly created/default dedicated directories receive mode 0700. | `test_existing_custom_parent_permissions_are_preserved` | Fixed |
| R11 | Undecodable tracked files now produce a release error instead of being skipped. | `test_privacy_scan_fails_closed_on_mixed_encoding_key_canary` | Fixed |
| R12 | PyYAML `safe_load` validates mapping shapes for both metadata files; release dependency is pinned and installed in CI. | `test_yaml_metadata_rejects_malformed_and_wrong_shapes` | Fixed |
| R13 | Reference definitions/usages, local files, and Markdown heading fragments are validated. | `test_markdown_reference_links_and_fragments_are_checked` | Fixed |
| R14 | JSON/config reads are capped at 1 MiB and provider responses at 2 MiB, reading only one byte beyond each boundary. | `test_json_file_input_size_boundary`, `test_provider_response_size_boundary` | Fixed |
