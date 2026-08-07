# V2 Final Code Review — R15–R27 Re-Review

Date: 2026-08-07
Original verdict: **CHANGES REQUIRED**
Current re-review verdict: **CONDITIONALLY APPROVED** (see R24 TOCTOU note)

This review uses only synthetic inputs and public repository contracts. It contains no private traveler data, credentials, internal task identifiers, model identifiers, or development-session paths.

## Re-Review Scope

Exact commit: `d739bcb24595b6e6a09797b6977b416a13a151a8`
Parent: `af46a3a6d02d41266051daa384f83719e8070d56`
Branch: `agent/china-destination-selection-v2`
Workspace: clean; main unchanged; remote V2 branch absent; no push.

## Independent Gate Re-Run

| Gate | Command / Evidence | Verdict |
|---|---|---|
| Unit tests | `python3 -m unittest discover -s tests -v` — Ran 88 tests, OK | **PASS** |
| Release checks | `python3 scripts/release_checks.py` — metadata, 17 resources, links, privacy passed | **PASS** |
| Ruff | `uvx ruff check scripts tests` — All checks passed! | **PASS** |
| mypy | `uvx mypy scripts --ignore-missing-imports` — Success: no issues found in 8 source files | **PASS** |
| compileall | `python3 -m compileall -q scripts tests` — exit 0 | **PASS** |
| Bandit | `uvx bandit -q -ll -r scripts` — 0 medium/high findings | **PASS** |
| zizmor | `uvx zizmor .github/workflows/ci.yml` — No findings to report | **PASS** |
| pip-audit | `uvx --python 3.12 pip-audit -r requirements-release.txt` — No known vulnerabilities found | **PASS** |
| git diff --check | clean | **PASS** |
| Luban | `bash skills/luban/tools/check-skill-repo.sh .` — PASS 11 / WARN 2 (marketplace missing, demo GIF) / FAIL 0 | **PASS** |
| Fresh scenario harness | Regenerated 8 scenarios with timezone-aware timestamps (`queried_at: 2026-08-07T12:00:00+08:00`, `valid_for: YYYY-MM-DD through YYYY-MM-DD`) — 8/8 contract + 8/8 validation | **PASS** |
| Semantic privacy scan | 4 commits × 192 tree objects; 0 hits on personal markers, local paths, internal task IDs, and prohibited model names | **PASS** |
| Author/committer identity | All 4 commits: `ryunana <76762767+ryunana@users.noreply.github.com>` | **PASS** |
| Remote state | `git ls-remote --heads origin agent/china-destination-selection-v2` — no head; main unchanged | **PASS** |
| detect-secrets | `uvx detect-secrets scan --all-files` — exit 0; only test fixtures flagged (expected) | **PASS** |
| Public URLs | All 13 external links reachable (verified in prior review cycle; no new URLs in d739bcb diff) | **PASS** |
| Fuzz / robustness | 85,000 randomized adversarial payloads across score_destinations (30k), validate_itinerary (30k), amap_cli (15k), load_config (10k) — **0 crashes, 0 serialization failures** | **PASS** |

## R15–R27 Individual Re-Probe Results

Each probe executed directly against the implementation in `d739bcb` with synthetic canary values, temporary directories, and clean environment. No real keys or private data were used.

| ID | Finding | Probe Result | Verdict |
|---|---|---|---|
| R15 | Privacy scan detects unquoted key assignments | 3/3 detection on `AMAP_API_KEY=<32chars>`, `key: <32chars>`, `token = '<32chars>'`; 0 false positives on placeholders | **Fixed** |
| R16 | Config semantic types fail-closed | 4/4 invalid shapes rejected (`enabled="false"`, `enabled=1`, `api_key=" "`, `offer_amap_setup="false"`); unknown extensions preserved | **Fixed** |
| R17 | Dynamic evidence requires complete freshness record | Rejects missing field/valid_for, non-timestamp queried_at, naive timestamps; accepts Z/offset timestamps; unknown/login claims without value pass; unknown with value rejected | **Fixed** |
| R18 | Provider response cannot reflect key | Success payload with key in geocodes location and dict key → key absent from JSON; error payload with key in infocode → key absent from JSON | **Fixed** |
| R19 | Non-UTF8 tracked file names are reported | Mocked `b"valid.md\0bad-\xff.md\0"` → files=[valid.md], issues=["tracked file name is not valid UTF-8"] | **Fixed** |
| R20 | Huge integers rejected without overflow | 10⁴⁰⁰ in weights, minimum_viable_days, and dimension score — all rejected with structured JSON, no OverflowError/traceback | **Fixed** |
| R21 | Strict JSON rejects non-finite exponents and deep nesting | `1e9999` → ValueError; 4000-bracket nesting → ValueError; 300-layer gate extra → rejected before deepcopy; provider `1e9999` → malformed_response | **Fixed** |
| R22 | Input file errors do not echo user paths | score/itinerary CLI with `/tmp/CANARY_PRIVATE_PATH_1234567890.json` — canary absent from stdout+stderr, structured `input_unreadable` returned | **Fixed** |
| R23 | do-not-ask-again persists preference only | No getpass call; existing amap + extension preserved; onboarding.offer_amap_setup=false written; mode 0600 | **Fixed** |
| R24 | 0644 key config fails closed | stat-based check rejects group/other-readable files; original mode preserved (not repaired) | **Fixed** |
| R24b | TOCTOU: symlink swap between read and stat | **Bypassed**: racing a symlink swap between `open()` and `os.stat()` allows a 0644 file to be read while a 0600 file is stat'd. Requires local write access to the config directory. | **Minor** — see note |
| R25 | Symlink parent permissions preserved | Symlinked shared dir (0755) → setup writes config (0600), shared dir remains 0755 | **Fixed** |
| R26 | Wide date range bounded | 0001-01-01 through 9999-12-31 resolves in <1ms with structured `day_count_mismatch` | **Fixed** |
| R27 | Docs synchronized | Review file shows "Original verdict: CHANGES REQUIRED" + "PENDING INDEPENDENT RE-REVIEW"; CONTRIBUTING.md includes `requirements-release.txt`; forward-acceptance labels /tmp harness as untracked and not publicly reproducible | **Fixed** |

## R24 TOCTOU Assessment

**What it is:** `get_api_key()` in `travel_common.py` reads the config file first, then stats the path. A local user with write access to the config directory can atomically swap a symlink between the read and the stat — reading a 0644 file but stat'ing a 0600 file. The permission check is bypassed.

**Practical impact:** The attacker must already have write access to the config directory (same user, or root). The permission check exists to prevent accidental world-readable leaks, not to defend against a malicious local user who can already read the file. The attacker who can swap symlinks can just as easily `cat` the 0644 file directly.

**Recommended fix (not blocking):** Move the stat before the open, or use `os.open()` + `os.fstat()` to atomically check permissions on the opened file descriptor, eliminating the TOCTOU window. This is a defense-in-depth hardening item and does not block the current release.

## Additional Verification: Fuzz Testing

85,000 randomized adversarial payloads across all four parsing entry points:
- **score_destinations** (30,000 payloads): 0 crashes, 0 non-strict-JSON serializations
- **validate_itinerary** (30,000 payloads): 0 crashes
- **AMap client provider payloads** (15,000 payloads): 0 crashes
- **config loader** (10,000 payloads): 0 crashes, all invalid inputs → ConfigurationInvalid

This is a strong signal that the recursive JSON validation, wall-of-catch guards, and bounded API reading are working correctly.

## PyYAML 6.0.3 Advisory Status

- pip-audit (latest): **No known vulnerabilities found**
- Snyk: **0 C 0 H 0 M 0 L**
- deps.dev: **No advisories detected**
- OSV: PYSEC-2021-142 only affects versions before 5.4 (mitigated in 5.4+, fixed in 6.0.3)

PyYAML 6.0.3 is the current latest stable version and has zero known vulnerabilities.

## Response Record — R15–R27

| ID | Severity | Disposition | Notes |
|---|---|---|---|
| R15 | High | **Fixed** | Unquoted key assignments detected; no values leaked |
| R16 | Important | **Fixed** | Config types validated; extensions preserved |
| R17 | Important | **Fixed** | Complete freshness records required |
| R18 | Important | **Fixed** | Recursive key redaction from provider JSON |
| R19 | Low | **Fixed** | Non-UTF8 paths reported as release issues |
| R20 | Important | **Fixed** | Safe finite conversion with OverflowError capture |
| R21 | Important | **Fixed** | Unified strict loader with depth limit |
| R22 | Important | **Fixed** | Generic input_unreadable without path echo |
| R23 | Important | **Fixed** | Preference-only persistence, atomic write, 0600 |
| R24 | Important | **Fixed** | POSIX permission check rejects group/other bits |
| R24b | Minor | **Accepted with note** | TOCTOU requires local write access; defense-in-depth hardening deferred |
| R25 | Low | **Fixed** | Symlink target mode preserved |
| R26 | Important | **Fixed** | Day-count comparison before date-span allocation |
| R27 | Docs | **Fixed** | All review/dependency/reproducibility markers correct |

## Final Verdict

**CONDITIONALLY APPROVED.** All 17 gates (88 unit tests, release checks, lint/type/security tools, fresh scenario harness, semantic privacy scan, fuzz testing, dependency audit, docs consistency) pass on commit `d739bcb`. The single remaining finding (R24b symlink TOCTOU) is a defense-in-depth item requiring local write access — it does not increase the attack surface beyond what direct file access already provides, and is accepted for this release.

**Prerequisites before push/PR:**
1. User explicitly approves push.
2. After push, verify GitHub Actions CI passes (fixture-validation job + optional live AMap smoke).

