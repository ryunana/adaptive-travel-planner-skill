# Planning and Output Contract

## Destination-Selection Contract

When the destination is undecided, follow `destination-selection.md` before the itinerary contract below:

1. Show each original candidate label, accepted normalized trip-shaped form, and `minimum_viable_days`.
2. Evaluate each hard gate as `pass`, `fail`, or `undecidable` before scoring. `unknown` and `login_required` evidence make a gate undecidable, not passed or failed.
3. Screen every candidate, then spend deep-research effort only on the leading two.
4. Return `destination_potential`, `this_trip_suitability`, `better_window` when deferred, `suitability_score` when evidence supports it, and separate `evidence_confidence`.
5. Never present a provisional candidate as an unconditional winner.

The destination decision must include a one-sentence ranking, evidence comparison for every candidate, explicit verdicts, reasons rejected famous options should not be chosen now, a full rank-1 itinerary, a concise rank-2 route with a switch condition, better windows for deferred choices, a 72-hour recheck list, and a fixed `pending_gates` field.

Each `pending_gates` entry must identify the hard gate, affected candidate, evidence status, and exact user action needed. If a rank-2 switch condition fires, rerun changed-item checks and reverify transport inventory, hotel availability or price, weather, closures, and reservation rules whenever the evidence is older than 24 hours.

## Required Comparison

Start with 2-3 materially different options:

| Option | Expected experience | Weather fit | Door-to-door cost | Composite load | Flexibility | Main risk | Verdict |
|---|---|---|---|---|---|---|---|

Then rank them and recommend one. Do not end with an unranked menu.

## Destination Verdict

Give each proposed city or major attraction exactly one verdict:

- **Dedicated trip**
- **En route**
- **Conditional**: state the exact weather, season, crowd, ticket, or health condition
- **Cancel/defer**

For a rejected famous option, include a short "why not."

## Core-Activity Card

For every core activity provide:

1. Why it fits the current traveler profile.
2. Expected personalized score and confidence.
3. Attraction type and weather sensitivity.
4. Go/no-go threshold.
5. Hourly weather window and query timestamp.
6. Opening status, ticket rule, lead time, refund rule, and official source.
7. Door-to-door route, transfers, luggage, parking, and first/last-mile friction.
8. Walking, ascent, altitude, temperature exposure, and driving load.
9. Internal visit order, with the flagship first.
10. Exit option, fallback, and latest decision time.

## Daily Plan

Use realistic times based on the private profile. Each day should show:

- wake and departure assumption;
- core activity or recovery purpose;
- optional lightweight additions;
- useful meal stops, not filler;
- transport mode and duration;
- estimated composite load;
- weather trigger;
- cancellation or recovery plan.

Do not hide an additional core activity under "optional evening activity."

## Dynamic Facts

- Verify exact dates, not generic schedules.
- Verify direct service before claiming a direct train, bus, ferry, or flight.
- Use the user's domestic currency and booking market unless requested otherwise.
- Rank hotels only after date-specific price and availability checks.
- Official closure, safety, and ticket rules outrank social posts.
- Recent social evidence may identify queues, parking, misleading packaging, and current friction.
- Recheck when the user's current app screenshot conflicts with search results.
- Label failed checks unknown. Never interpolate schedules, inventory, opening status, or prices.
- Record dynamic claims with field, value, evidence status, source, source URL when available, query time, validity scope, and notes as defined in `source-policy-cn.md`.
- Use only `verified`, `auxiliary`, `unknown`, or `login_required` evidence statuses.
- Match weather claims to the forecast horizon: climate and seasonal hazards beyond 14 days, low-confidence trends at 8-14 days, daily forecasts at 3-7 days, hourly and attraction-specific checks within 72 hours, and observations/nowcast/closures on the same day.

## Load Warnings

Raise a prominent warning when relevant:

- multiple core activities plus driving;
- early wake plus high walking load plus night driving;
- long driving followed by intensive hiking;
- altitude gain plus immediate strenuous activity;
- severe heat warning plus prolonged outdoor exposure;
- torrential rain, closure risk, landslide risk, or near-zero visibility;
- a companion fear or medical response without a disclosed alternative;
- no realistic recovery or exit option.

Thresholds should come from the private profile rather than this public contract.

## Restaurant Output

Show:

- local distinctiveness;
- dietary and non-spicy or allergen-safe choices;
- companion-compatible choices;
- queue and reservation status;
- detour, traffic, and parking cost;
- realistic price;
- dedicated-trip or en-route verdict.

Do not infer preference from a payment record alone.

## Hotel Output

Show:

- date-specific local-market price and availability;
- relation to the next core activity;
- parking, transit, and luggage friction;
- fit with the profile's quality baseline;
- whether a location premium buys a real experience;
- refund flexibility;
- whether changing hotels is worth the packing cost.

## Final Audit Checklist

- [ ] Current date, location, completed items, and active bookings are correct.
- [ ] Candidate forms and `minimum_viable_days` are comparable and accepted.
- [ ] Every hard gate is pass, fail, or undecidable; unresolved gates appear in `pending_gates`.
- [ ] Suitability and evidence confidence are separate; destination potential is not confused with exact-date fit.
- [ ] Calendar dates and hotel nights match.
- [ ] No unnecessary geographic backtracking.
- [ ] Every claimed transport service exists on the exact date.
- [ ] Weather was matched to attraction type and time window.
- [ ] Official opening and ticket rules were checked.
- [ ] Daily activity density matches the private profile.
- [ ] Companion constraints and driver fatigue were included.
- [ ] Hotel prices are date-specific and actually available.
- [ ] Rejected famous options include a reason.
- [ ] Unknown facts are labeled rather than invented.
- [ ] Rank-2 dynamic evidence will be reverified when switching, including every affected fact older than 24 hours.
- [ ] The answer does not expose unnecessary private data.
