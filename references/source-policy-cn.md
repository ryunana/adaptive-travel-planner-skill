# Mainland China Source Policy

Load this reference when researching dynamic facts for mainland China destinations. A provider's presence is not proof of current access, and supporting evidence must not silently become authoritative evidence.

## Provider Routing

Full dynamic planning requires a working host web-search or interactive-browser capability. Installing this repository does not install one.

Route discovery as follows:

1. When a current official URL is already known, open that page directly.
2. For mainland China notices, policies, transport changes, prices, and recent Chinese sources, prefer a host-provided Chinese search provider such as Doubao Search Custom when it has completed a successful live query.
3. If that provider is unavailable, use the host's default web search or interactive browser. Doubao is recommended, not mandatory.
4. Use AMap for map, POI, geocoding, and driving evidence, not as a replacement for general web search.
5. If no live discovery capability works, enter limited mode and keep every unsupported dynamic claim `unknown` or `login_required`.

A provider's authority label is only a ranking hint. Open the original result and classify the underlying first-party or supporting source using the policy below. Keep provider credentials and setup at the host layer; never ask the user to paste a key into chat or store it in this repository.

This file decides source authority; `research-effort-contract.md` decides how much bounded search effort is required. For a decision-critical dynamic fact, one failed query is not enough for `unknown`: reformulate the query, change source class, and try another available provider or interactive browser as required there.

## Source Priority

| Domain | Primary evidence | Supporting evidence |
|---|---|---|
| Weather and warnings | Meteorological and government sources | AMap baseline and forecast visualizers |
| Driving and geography | AMap official API or current map UI | Other current map providers for comparison |
| Rail | Current 12306 page or authenticated app | Domestic booking platforms |
| Flights | Airline and aviation-service pages | Domestic booking platforms |
| Coaches | Local operator or station channel | Domestic ticket platforms |
| Attractions | Official site, account, or mini-program | Domestic ticket platforms |
| Hotels | Current domestic booking inventory | Hotel official channel |
| Crowd and on-site friction | Recent social and review evidence | Map reviews and comments |
| Road and safety | Traffic police, emergency, government, and attraction notices | Social evidence as a lead only |

Prefer first-party current evidence when sources disagree. Explain material discrepancies rather than averaging them. User-provided current app evidence may supersede stale public results, but label its source and scope.

## Evidence Record

Map every dynamic claim to a record with this shape:

```json
{
  "field": "rail_inventory",
  "value": null,
  "status": "login_required",
  "source": "12306",
  "source_url": null,
  "queried_at": "ISO-8601 timestamp",
  "valid_for": "exact travel date",
  "attempt_log": [],
  "exhaustion_reason": null,
  "notes": "User must confirm in authenticated app"
}
```

Use exactly one of four statuses:

- `verified`: direct, current official or first-party evidence supports the claim;
- `auxiliary`: credible marketplace, review, or experience evidence supports context but is not authoritative;
- `unknown`: the bounded protocol in `research-effort-contract.md` reached an allowed stopping condition without reliable evidence;
- `login_required`: the next check requires the user's authenticated session.

`unknown` and `login_required` are not negative facts. They make a related hard gate `undecidable`, never automatically `pass` or `fail`. Carry each unresolved decision-critical item into `pending_gates` with the exact authenticated check, screenshot, date/route lookup, or other user action required. Keep the full `attempt_log` internal unless an unresolved fact affects the decision; then summarize attempted source classes, channels, failure reasons, and the stopping condition without dumping routine traces.

## Freshness and Precision

Record `queried_at` and the date, route, property, or attraction for which the fact is valid. Avoid transferring a fact to another date or location. Recheck when the user's current screenshot conflicts with older evidence. When switching to rank 2, reverify changed items and all dynamic facts older than 24 hours.

Do not invent schedules, availability, opening status, prices, quotas, or forecast coverage. If the source exposes less precision than requested, preserve that coarser precision and lower confidence.
