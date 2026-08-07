# Trip Brief

> Fill only fields that can change the destination decision. Every field is optional; treat omissions as `unknown` and ask one focused question only when the answer blocks the current decision.

## Decision Frame

- Practical origin: [optional]
- Earliest departure: [optional]
- Acceptable date range: [optional]
- Available duration: [optional]
- Hard return date/time: [optional]
- Decision deadline: [optional]
- Budget ceiling that can eliminate an option: [optional]

## Candidate Set

| Original label | Proposed normalized form | Minimum viable days | Accepted by traveler? |
|---|---|---:|---|
| [optional] | [optional bounded city/region/route] | [optional] | [yes / no / unknown] |

- Generate a starting set when no candidates are supplied: [yes / no / unknown]
- Candidate additions or exclusions: [optional]
- Must-include experience: [optional]
- Explicitly rejected booking or trip conditions: [optional]

## Commitments and Switching

- Active transport bookings: [optional]
- Active hotel bookings: [optional]
- Active attraction or rental bookings: [optional]
- Sunk costs: [optional]
- Refund or cancellation deadlines: [optional]
- Same-day or pre-departure switching tolerance: [optional]

## Current Constraints

- Travelers, luggage, and mobility constraints: [optional]
- Current fatigue, illness, or altitude response: [optional]
- Driver condition and road boundaries: [optional]
- Companion constraints: [optional]
- Weather, crowd, reservation, or accessibility vetoes: [optional]

## Capability Status and Preference

- Working host web-search or interactive-browser capability verified by a successful current query: [yes / no / unknown]
- Accept limited mode if neither live discovery capability works: [yes / no / unknown]
- Continue without AMap in the current mode (host search if live discovery is verified; otherwise limited): [yes / no / unknown]
- Offer AMap setup: [yes / no / unknown]
- Do not ask about AMap setup again: [yes / no / unknown]

## Decision Output

- Number of screened candidates: [up to 3 recommended]
- Require one clear recommendation: [yes / no / unknown]
- Rank-2 route detail: [concise / standard / unknown]
- Required comparison details: [optional]
- Preferred answer length: [short / medium / detailed / unknown]

## Pending Gates

| Gate | Candidate | Evidence status | Exact action needed | Deadline |
|---|---|---|---|---|
| `pending_gates` (only unresolved hard gates) | | [unknown / login_required] | | |
