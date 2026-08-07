# Destination Selection Workflow

Load this reference when the destination is undecided, the user supplies vague or mixed-granularity candidates, or the current destination may need to be replaced. Use `source-policy-cn.md` and `scoring-model.md` only when researching and ranking; use `capability-matrix.md` only when detecting or explaining adapters.

## Stage A: Normalize the Trip Brief

Read the private traveler profile, then establish only decision-changing facts:

- practical origin;
- earliest departure, acceptable date range, duration, and hard return date;
- candidates already under consideration;
- active bookings and sunk costs;
- near-departure health, fatigue, driver, and companion state;
- budget only when it can eliminate an option.

Ask one focused question at a time. Missing V2 profile fields are `unknown`, not errors.

If the user has no candidates, generate two to four plausible options from stable preferences and seasonal knowledge. Present them as a starting set and let the user add or remove options before screening. Do not spend live-query budget merely to create this set.

### Normalize candidate granularity

Before a score is possible, convert every candidate to a comparable trip-shaped form:

1. Retain the user's original label.
2. Define the city, region, or bounded route actually being evaluated.
3. Estimate and show `minimum_viable_days` for that form.
4. Compare it with the available duration and hard return date.
5. If the original shape is too large, propose a meaningful bounded form and obtain acceptance because this is a material change.
6. Preserve long-term potential for the original destination, but score only the accepted normalized form.

If the minimum meaningful form still materially exceeds available time, or the user rejects the bounded form, evaluate the duration hard gate instead of penalizing it against a single-city stay.

## Stage B: Detect Capabilities

Detect and report web search, interactive browser and likely login needs, Python runtime, AMap adapter installation, key configuration, and verified-query status. An installed file is not a working capability. Full dynamic planning requires at least one successful current query through web search or an interactive browser.

If neither live discovery capability works, enter limited mode. Continue only with candidate normalization, stable profile fit, composite-load analysis, structural review, and current evidence supplied by the user. Keep unsupported dynamic facts `unknown` or `login_required`; do not present the result as a fully verified current itinerary. Missing web search and missing AMap are different conditions.

If enhanced AMap mode is unavailable, describe its narrow benefit: geocoding, driving route, distance, duration, toll reference, and short-horizon city-level baseline weather. It does not provide rail or flight inventory, hotel prices, attraction ticket stock, scenic-area microclimate, or crowd conditions, and it does not extend the 8-14 day weather decision horizon.

When optional AMap enhancement is unavailable, offer exactly one mode-appropriate choice set:

- If web search or an interactive browser has completed a successful current query: (1) set up AMap and continue in host search mode, (2) continue in host search mode without AMap, or (3) continue without AMap and do not ask again.
- If neither live discovery capability works: (1) set up AMap as a narrow map enhancement while remaining in limited mode, (2) continue in limited mode without AMap, or (3) continue in limited mode without AMap and do not ask again.

Persist only the third choice in the selected set. AMap success or failure never changes the discovery mode by itself. Follow `capability-matrix.md`; never imply that instructions alone create provider access.

## Stage C: Optional AMap Setup

Proceed only after explicit consent. Direct the user to the official AMap Open Platform for any developer verification and Web Service key creation; automation cannot complete those account steps. Explain files, permissions, and key handling before setup.

Use only the repository's official-API wrapper. Store local configuration under `~/.config/adaptive-travel-planner/config.json`, with user-only directory access where supported, atomic writes, and user read/write file permissions. `AMAP_API_KEY` may override the file. Accept an interactively supplied key through hidden input only; never place it in an argument, output, logs, or errors.

Verify a real geocode, route, and baseline-weather query. Report the exact failed stage and preserve the current discovery mode if any check fails: remain in host search mode only when web search or an interactive browser is verified working; otherwise remain in limited mode. Recheck current official endpoint, Web Service key, quota, and terms documentation during adapter implementation rather than relying on remembered contracts.

## Stage D: Screen All Candidates

Screen up to three normalized candidates on:

- traveler-profile fit;
- seasonal climate and current forecast horizon;
- weather and safety risks;
- core-experience count and distinctiveness;
- approximate access friction;
- holiday or seasonal crowd and reservation risk;
- bad-weather resilience;
- current price level when available.

If there are more than three, first eliminate clearly dominated choices and explain why. Always show the original label, normalized form, and `minimum_viable_days` together.

### Apply hard gates before scores

Hard gates cover official closure or credible safety risk, impossible exact-date transport, critical health/accessibility/companion constraints, no meaningful attraction set after weather invalidation, rejected mandatory booking conditions, and an irreducibly overlong trip shape.

Every gate is `pass`, `fail`, or `undecidable`:

- `pass`: sufficient evidence confirms the constraint is satisfied;
- `fail`: sufficient evidence confirms the candidate is vetoed;
- `undecidable`: evidence is `unknown` or `login_required`, or a decision-critical check remains outstanding.

Never convert missing evidence into pass or fail. Keep an undecidable candidate provisional, and add a `pending_gates` entry containing the gate, affected candidate, evidence status, and exact action needed to resolve it.

## Stage E: Deep-Research the Leaders

For the top two provisional candidates, verify as available:

- exact-date train, flight, and coach service and realistic inventory;
- door-to-door time and transfer friction;
- local-market hotel availability and price;
- attraction opening, reservation, refund, and closure rules;
- daily or hourly weather appropriate to the forecast horizon;
- route topology and internal travel burden;
- composite physical and driving load;
- cancellation deadlines and switching cost.

Represent dynamic facts using the evidence record in `source-policy-cn.md`. Never fabricate a score when decision-critical evidence is insufficient.

## Forecast Horizon

- More than 14 days: use historical climate and seasonal hazards; do not claim exact weather.
- 8-14 days: use low-confidence forecast trends and keep switching open.
- 3-7 days: use daily forecasts and match weather to attractions.
- Within 72 hours: use hourly weather, warnings, visibility, wind, and attraction-specific go/no-go checks.
- Same day: combine observations, radar or nowcast when available, official closures, and travel time.

Source quality may justify a threshold adjustment, but confidence and the reason must be explicit.

## Stage F: Decide and Plan

Return, in order:

1. a one-sentence ranked conclusion;
2. an evidence comparison for every candidate;
3. a dedicated/en-route/conditional/defer verdict for each;
4. reasons famous rejected options should not be chosen now;
5. a full daily itinerary for rank 1;
6. a concise route and explicit switch condition for rank 2;
7. a better season or trigger for deferred candidates;
8. a 72-hour pre-departure recheck list;
9. a fixed `pending_gates` field for every undecidable hard gate.

Do not present a provisional candidate as an unconditional winner. The rank-2 route is a switchable outline, not an executable stale backup. When a switch condition fires, rerun the changed-item Stage E checks for rank 2 and reverify every dynamic fact older than 24 hours, including transport inventory, hotel availability or price, weather, closures, and reservation rules, before recommending the switch.
