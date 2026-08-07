# China Destination Selection V2 Design

## 1. Goal

Upgrade Adaptive Travel Planner from a destination-known itinerary auditor into a China-mainland destination decision and trip-planning Skill.

Target interaction:

```text
User: I have time to travel. I am considering several regions.
Agent: Check the private profile, complete only blocking trip facts, research every candidate, rank them, explain what to skip, then build the recommended itinerary.
```

V2 must support vague candidate-level requests without immediately generating several disposable detailed itineraries.

## 2. Scope

### In scope

- Leisure travel within mainland China.
- Candidate destination comparison and elimination.
- Low-cost generation of two to four candidates when the user has none, using the stable traveler profile and seasonal knowledge before live-query budget is spent.
- Exact-date transport, weather, attraction, hotel, crowd, and route research when tools permit.
- Zero-configuration browser/search mode.
- Optional enhanced AMap mode using an official Web Service API key.
- Private traveler profile, composite-load rules, explicit go/conditional/defer/cancel decisions, and post-trip calibration.
- A complete itinerary for the first-ranked option and a concise switchable route for the second-ranked option.

### Out of scope

- International travel data sources.
- Automatic payment, ticket purchase, or hotel booking.
- Brittle scraping of 12306, hotel platforms, or attraction mini-programs.
- Claims that AMap provides rail inventory, hotel prices, attraction ticket stock, or scenic-area microclimate.
- Uploading or synchronizing private traveler profiles.
- A standalone web application or hosted MCP service.
- Exhaustive open-ended destination discovery; generated candidates are a small decision set, not a claim to cover every possible destination.

## 3. Design Principles

1. **Decide before detailing**: compare destinations before spending query effort on daily itineraries.
2. **Hard gates before scores**: safety, closure, impossible transport, and critical health constraints can veto a candidate.
3. **Potential differs from this trip**: preserve long-term destination fit separately from exact-date suitability.
4. **Evidence carries status**: every dynamic fact is verified, auxiliary, unknown, or login-required.
5. **No silent installation**: optional tools require informed user consent and post-install verification.
6. **Private by construction**: real profiles and keys live outside tracked repository files.
7. **Progressive depth**: all candidates receive screening; only leading candidates receive expensive live research.

## 4. User Flow

### Stage A: Normalize the trip brief

Read the private profile, then establish only facts that can change the destination decision:

- departure city or practical origin;
- earliest departure and acceptable date range;
- trip duration and hard return date;
- candidates already under consideration;
- active bookings or sunk costs;
- current health, fatigue, and companion state when departure is near;
- budget only when it can eliminate an option.

Ask one focused question at a time. Do not require every profile field.

If the user supplies no candidates, generate two to four plausible candidates from stable profile preferences and seasonal knowledge, explain that they are a starting set, and let the user remove or add options before screening. Do not spend live-query budget merely to generate that starting set.

Before scoring, normalize every candidate into a comparable trip-shaped unit:

1. Estimate its `minimum_viable_days` and state the geographic/route shape being evaluated.
2. Compare that estimate with the user's available duration and hard return date.
3. When the original shape is too large, propose a meaningful bounded version (for example, an eight-day northern Yunnan route instead of a Yunnan-Guizhou-Sichuan circuit) and obtain the user's acceptance of that material change.
4. Preserve the original destination's long-term potential separately, but score only the accepted normalized form for this trip.

If the minimum meaningful form still materially exceeds the available duration, or the user rejects a bounded version, send the candidate to hard-gate evaluation rather than scoring it against smaller candidates.

### Stage B: Detect capabilities

Detect and report:

- web search availability;
- interactive browser availability and whether login may be required;
- Python runtime;
- AMap enhanced adapter installation;
- AMap key configuration and verified query status.

If AMap enhanced mode is unavailable, explain precisely what improves with it: geocoding, driving routes, distance, duration, toll reference, and short-horizon city-level baseline weather. State that rail inventory, flights, hotels, attraction tickets, microclimate, and crowd conditions still need other sources. Also state that AMap does not extend the 8-14 day weather decision horizon beyond the normal forecast sources, so enhanced mode has no promised weather-coverage gain for that window. Exact forecast horizon and quota statements must come from the official documentation rechecked during implementation.

Offer:

1. Install and continue.
2. Continue in zero-configuration mode.
3. Continue and do not ask again.

Persist only the third preference locally.

### Stage C: Optional AMap setup

After explicit consent:

0. Direct the user to the official AMap Open Platform to complete any required developer verification and create a Web Service key; the setup script cannot perform account verification or create the key on the user's behalf. Use the official documentation link revalidated during implementation.
1. Explain files, permissions, and key requirement.
2. Install or activate the repository's official-API wrapper; do not download an unreviewed third-party CLI.
3. Store configuration at `~/.config/adaptive-travel-planner/config.json` with user-only permissions.
4. Allow `AMAP_API_KEY` to override the file for CI or advanced use.
5. Accept an interactive key only through hidden input. Never accept it as a command argument or print it in logs, errors, or final answers.
6. Verify geocoding, a route query, and baseline weather with real calls.
7. Report the exact failed stage if verification does not pass.

Do not treat an installed file as a working capability.

Local configuration schema:

```json
{
  "amap": {
    "enabled": true,
    "api_key": "stored-locally"
  },
  "onboarding": {
    "offer_amap_setup": true
  }
}
```

The setup script creates the parent directory with user-only access where supported, writes the file atomically, and sets the file mode to user read/write. Choosing "do not ask again" sets `offer_amap_setup` to `false`; the user can re-enable it manually or by running setup.

Implementation must recheck the current official AMap Web Service documentation, endpoint availability, key type, quota behavior, and terms before coding the adapter. Do not rely on remembered endpoint contracts.

### Stage D: Screen all candidates

For up to three candidates, collect enough evidence to compare:

- traveler-profile fit;
- seasonal climate and current forecast horizon;
- major weather or safety risks;
- core experience count and distinctiveness;
- approximate access friction from the origin;
- summer/holiday crowd and reservation risk;
- bad-weather resilience;
- current price level when available.

If the user supplies more than three candidates, eliminate clearly dominated options first and explain why.

Screen and score only the normalized trip-shaped forms from Stage A. Show each original label, normalized form, and `minimum_viable_days` together so a regional circuit is never silently compared with a single-city stay.

### Stage E: Deep-research leading candidates

For the top two candidates, verify as available:

- exact-date trains, flights, coaches, and realistic inventory;
- door-to-door duration and transfer friction;
- local-market hotel availability and price;
- attraction opening, reservation, refund, and closure rules;
- daily or hourly weather appropriate to forecast horizon;
- route topology and internal travel burden;
- composite physical and driving load;
- cancellation deadlines and switching cost.

### Stage F: Decide and plan

Output:

1. One-sentence ranked conclusion.
2. Evidence comparison for every candidate.
3. Explicit dedicated/en-route/conditional/defer verdicts.
4. Reasons rejected famous options should not be chosen now.
5. Full daily itinerary for rank 1.
6. Concise route and switch condition for rank 2.
7. Better season or trigger for deferred candidates.
8. A 72-hour pre-departure recheck list.
9. A fixed `pending_gates` field listing every hard gate that is undecidable, the affected candidate, and the exact user action needed to resolve it (for example, confirming inventory for a named date and route in the authenticated 12306 app).

The rank-2 route is not an executable stale backup. Every dynamic evidence record keeps its `queried_at`; when a switch condition fires, rerun the changed-item checks from Stage E for rank 2. Reverify dynamic facts older than 24 hours, including transport inventory, hotel availability or price, weather, closures, and reservation rules, before recommending the switch.

## 5. Query Architecture

The Skill orchestrates queries; provider adapters retrieve facts. The public repository must not imply that instructions alone create platform access.

### Source priority for mainland China

| Domain | Primary | Supporting |
|---|---|---|
| Weather and warnings | Meteorological and government sources | AMap baseline, forecast visualizers |
| Driving and geography | AMap official API or current map UI | Other map providers for comparison |
| Rail | 12306 current page/app | Domestic booking platforms as auxiliary evidence |
| Flights | Airline and aviation service pages | Domestic booking platforms |
| Coaches | Local operator or station channel | Domestic ticket platforms |
| Attractions | Official site, account, or mini-program | Domestic ticket platforms |
| Hotels | Current domestic booking inventory | Hotel official channel |
| Crowd and friction | Recent social and review evidence | Map reviews and comments |
| Road and safety | Traffic police, emergency, government, attraction notices | Social evidence only as a lead |

### Evidence record

Every dynamic fact should map to:

```json
{
  "field": "rail_inventory",
  "value": null,
  "status": "login_required",
  "source": "12306",
  "source_url": null,
  "queried_at": "ISO-8601 timestamp",
  "valid_for": "exact travel date",
  "notes": "User must confirm in authenticated app"
}
```

Allowed statuses:

- `verified`: direct official or first-party current evidence;
- `auxiliary`: credible but not authoritative experience or marketplace evidence;
- `unknown`: query failed or no reliable source;
- `login_required`: the next check requires the user's authenticated session.

## 6. Forecast Horizon Rules

- More than 14 days away: use historical climate and seasonal hazards; do not claim exact weather.
- 8-14 days: use forecast trend with low confidence and keep destination switching open.
- 3-7 days: use daily forecast and begin weather-attraction matching.
- Within 72 hours: use hourly weather, warning, visibility, wind, and attraction-specific go/no-go checks.
- Same day: combine current observations, radar/nowcast when available, official closures, and travel time.

The exact thresholds may be adjusted by source quality, but confidence must be explicit.

## 7. Decision Model

### Hard gates

A candidate may be rejected before scoring for:

- official closure or credible safety risk affecting its primary value;
- no feasible exact-date transport within the user's constraints;
- a critical health, accessibility, or companion constraint;
- no meaningful attraction set after weather invalidation;
- mandatory booking conditions the traveler explicitly rejects.
- the candidate's minimum meaningful duration materially exceeds the available duration and the user rejects a viable bounded form.

Hard gates are three-state: `pass`, `fail`, or `undecidable`. `unknown` and `login_required` evidence must never be interpreted as either pass or fail. An undecidable gate keeps the candidate provisional and must appear in Stage F's `pending_gates` field with the specific authenticated check, screenshot, date/route query, or other action required to resolve it. Do not present a provisional candidate as an unconditional winner.

### Weighted dimensions

Score remaining candidates on a 0-5 scale using profile-adjustable weights:

| Dimension | Default weight |
|---|---:|
| Preference fit | 25 |
| Seasonal and weather fit | 20 |
| Core experience density | 15 |
| Access and route friction | 10 |
| Crowd and ticket friction | 10 |
| Bad-weather resilience | 10 |
| Composite-load fit | 5 |
| Current value for money | 5 |

Return both:

- `suitability_score`: weighted result;
- `evidence_confidence`: coverage and authority of supporting facts.

Do not rank a poorly evidenced 86 as definitively better than a well-evidenced 82. Explain decisive dimensions rather than presenting false precision.

### Potential and current suitability

Maintain:

- `destination_potential`: long-term profile fit;
- `this_trip_suitability`: exact-date fit;
- `better_window`: a better season or condition when deferred.

## 8. Repository Changes

### Core Skill

- Update `SKILL.md` to add destination-selection routing and progressive reference loading.
- Keep the body concise; move source and scoring detail to references.
- Add `agents/openai.yaml` generated from the final Skill metadata.

### References

- `references/destination-selection.md`
- `references/source-policy-cn.md`
- `references/capability-matrix.md`
- `references/scoring-model.md`
- retain and update `references/planning-contract.md`

`references/capability-matrix.md` must distinguish each adapter's capability, forecast horizon, authentication prerequisite, and quota boundary. Numeric claims and official links are implementation-time verified facts rather than values copied from memory.

### Templates

- `templates/trip-brief.template.md`
- update portable prompt and traveler-profile templates with destination-decision fields.

### Deterministic scripts

- `scripts/check_capabilities.py`
- `scripts/setup_amap.py`
- `scripts/amap_cli.py`
- `scripts/verify_amap.py`
- `scripts/score_destinations.py`
- `scripts/validate_itinerary.py`

Scripts should use the Python standard library where practical and support a broadly available Python 3 version. Network adapters must have timeouts, structured errors, and machine-readable output.

### Public documentation

Update README with:

- the vague-candidates use case;
- zero-configuration versus enhanced mode;
- what enhanced AMap does and does not improve;
- safe key setup;
- destination comparison and output examples.

## 9. Failure and Degraded Behavior

| Failure | Required behavior |
|---|---|
| No AMap key | Explain impact, offer setup, then use browser mode if declined |
| Invalid or quota-limited key | Mark enhanced capability failed; never expose key |
| 12306 or hotel login required | Mark field login-required and ask for authenticated check or screenshot |
| One provider disagrees with another | Prefer first-party evidence and explain discrepancy |
| Weather outside reliable horizon | Use climate/seasonal risk and lower confidence |
| Candidate has insufficient evidence | Do not fabricate score; report uncertainty and missing decision-critical facts |
| Install succeeds but live test fails | Report setup incomplete and stay in zero-configuration mode |
| Entire city loses primary value | Compare another city, not only weak local substitutes |

## 10. Validation

### Static checks

- Skill metadata validates.
- All referenced resources exist.
- Private config and completed profile paths are ignored.
- No secret, local username, real itinerary, or personal profile enters tracked files.
- Scripts return structured output and redact key-like values.

### Script tests

- Capability detection with no config, file config, and environment override.
- Config creation uses user-only permissions.
- Invalid key, timeout, quota, malformed API response, and successful response.
- Destination score calculation, hard-gate rejection, missing-evidence confidence, and tie handling.
- Itinerary validator catches date mismatch, excessive core activities, backtracking input, and unsupported dynamic claims.

### Forward evaluations

1. Three summer candidates with different weather and crowd risks.
2. More than three candidates requiring fast elimination.
3. Departure more than 14 days away, where exact weather must not be invented.
4. No AMap key and user declines installation.
5. User accepts setup but the key fails verification.
6. Rank 1 becomes invalid within 72 hours and the plan switches to rank 2.
7. A famous destination scores high in potential but low for the current trip.
8. Mixed-granularity candidates (regional circuit versus single city) with limited days; output must show each normalized candidate form and its minimum viable days before ranking.

Acceptance requires a ranked destination decision, evidence statuses, one full itinerary, one concise fallback route, explicit deferred reasons, and no fabricated dynamic facts.

## 11. Release Plan

- Implement on `agent/china-destination-selection-v2`.
- Keep V1 private-profile compatibility: every missing V2 profile field is treated as `unknown` and is asked only when it blocks the current decision, so an existing profile does not need to be rewritten.
- Validate scripts without a real key using fixtures; perform a live AMap smoke test only when a user-authorized key is available.
- Add a minimal GitHub Actions workflow for pushes and pull requests that runs fixture-backed script tests without a real key, scans tracked content for private paths and key-like material, and validates Skill metadata. Keep the live AMap smoke test manual-only and secret-gated.
- Run privacy scans before commit.
- Treat `agents/openai.yaml` as Codex-specific discovery metadata only; `SKILL.md` and portable references remain the cross-agent contract.
- Keep the finalized public design in `docs/specs/`; it was moved from the workflow-staging path before release. Historical files in `docs/reviews/` retain their original review-time references.
- Publish through a reviewed pull request rather than pushing directly to `main`.
