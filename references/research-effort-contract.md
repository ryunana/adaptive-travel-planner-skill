# Bounded Research Effort Contract

Load this reference whenever current facts can change a destination ranking, hard gate, booking decision, switch condition, or executable itinerary. The purpose is to reduce avoidable `unknown` values without rewarding endless or low-quality search.

## Scope

A **decision-critical dynamic fact** is a current fact that can change a recommendation or make an itinerary non-executable, including exact-date transport, hotel inventory or price, attraction opening and reservation rules, official closures or warnings, decision-horizon weather, and material road restrictions.

Apply the full protocol to decision-critical facts for the top two destination candidates and to facts needed for the executable rank-1 itinerary. Supporting details that cannot change the decision may use a lighter two-attempt budget and must remain explicitly unverified when unresolved.

A successful authoritative check may stop immediately. The minimum effort below applies before assigning `unknown`, not before accepting a clear current official result.

## Capability Roles

- **Web search** discovers current candidate sources. A host-provided Chinese provider such as Doubao Search Custom is preferred for mainland China current facts when verified, but it is not mandatory.
- **Interactive browser** opens original pages, handles JavaScript-rendered content, checks user-visible flows, and provides another available discovery channel when a search provider fails.
- **AMap or another current map** supplies geography, POI, and driving evidence. It is not general web search and cannot unlock full mode by itself.
- **Authenticated first-party or marketplace session** supplies inventory or rules that public discovery cannot expose. Do not simulate authenticated access with public snippets.

Before research, report which capabilities completed a current test query. An installed adapter, remembered credential, or search-result snippet is not a working capability.

## Minimum Effort Before `unknown`

Do not assign `unknown` to a decision-critical dynamic fact after one failed query. Unless an early stop condition applies, complete all of the following:

1. Make **at least three substantive attempts**.
2. Use **two materially different query formulations**. Change useful dimensions such as the official entity name or alias, exact date, route, property, attraction, service number, and intent terms such as notice, closure, reservation, fare, timetable, or refund.
3. Attempt an **official or first-party source** and at least one **domain-appropriate alternative source**. Alternatives may include a government notice, operator channel, official account, current map, or booking platform, according to the authority rules in `source-policy-cn.md`.
4. If one provider or retrieval path fails, try **another available discovery channel**, including an interactive browser when it is available. Open candidate original pages; a result title or generated summary is only a lead.
5. Preserve source precision and date scope. Do not transfer a result to another date, route, property, or attraction.

A **substantive attempt** changes at least one of the query formulation, source class, provider, retrieval channel, or target page. Repeating the same failed request, refreshing an unchanged page, or paraphrasing without changing search intent does not count.

## Source Ladder

Use the domain-specific priority in `source-policy-cn.md`. A typical sequence is:

1. open a known current official page directly;
2. search the official entity plus exact date and fact;
3. reformulate the query using an alias, route, service number, or notice intent;
4. inspect a government, operator, or other first-party channel;
5. use a domain-appropriate booking platform, map, or recent supporting source;
6. follow any new high-value lead back to the most authoritative original page available.

Supporting evidence can reduce uncertainty but cannot overrule a current official closure, safety warning, ticket rule, or first-party inventory result.

## Authentication Boundary

Use `login_required`, not `unknown`, when an exact next check is known but requires a user-authenticated 12306, airline, hotel, attraction, mini-program, or booking session that the Agent cannot access.

The three-attempt minimum does not require pointless public retries after a verified authentication boundary. Record how the boundary was established, the exact page/app/date/route/property check needed, and the smallest useful user action or screenshot. Never ask for passwords, session cookies, CAPTCHA solutions, or provider keys in chat.

## Attempt Log

Record each effort in an `attempt_log` attached to the evidence record:

```json
{
  "query": "official entity + exact date + decision-critical fact",
  "channel": "web_search | interactive_browser | amap | authenticated_session | user_evidence",
  "provider": "host capability or first-party channel",
  "source_class": "official | first_party | government | marketplace | map | supporting",
  "source_url": null,
  "queried_at": "ISO-8601 timestamp",
  "outcome": "verified | lead | no_result | unreachable | blocked | login_required | conflicting",
  "failure_reason": null,
  "new_information": "short factual description or null"
}
```

Do not put credentials, session identifiers, private profile data, or raw sensitive page content in the log. The user-facing answer should summarize attempts only for unresolved decision-critical facts; do not dump routine successful search traces.

## Stop Conditions

Stop research for the fact when any one condition is met:

- a current authoritative source verifies the fact at the required precision;
- a confirmed authentication boundary requires `login_required`;
- every relevant live discovery capability is unavailable, so limited mode applies;
- after the minimum coverage above, **two consecutive attempts** produce no new credible lead;
- **six substantive attempts** have been completed without verification; a **new high-value lead** found at that boundary may justify **one final additional path**, but no further extension;
- all remaining relevant retrieval paths are blocked by a CAPTCHA, rate limit, paywall, platform control, or safety boundary after the safe available alternatives required above have been tried or found unavailable. **One blocked path is not an early stop** while another safe provider, source class, or browser path remains.

When stopping without verification, assign `unknown`, retain the `attempt_log`, state the exhaustion reason, lower evidence confidence, and carry the exact unresolved action into `pending_gates` when it can change the decision.

Conflicting credible sources are not resolved by majority vote. Prefer the more authoritative and current source; otherwise keep the decision provisional, explain the conflict, and record what would resolve it.

## Anti-Patterns

- One failed query followed immediately by `unknown`.
- Treating one blocked page as a stopping condition while a safe provider, source class, or browser path remains.
- Repeating the same provider, wording, and target page to inflate the attempt count.
- Searching indefinitely after a verified login wall.
- Treating AMap as proof of rail, hotel, ticket, closure, or crowd facts.
- Treating a search snippet, provider authority label, or AI summary as the original evidence.
- Hiding unresolved decision-critical facts in prose instead of `pending_gates`.

## Verification Checklist

Before publishing `unknown` for a decision-critical dynamic fact, verify that:

- [ ] at least three substantive attempts were made, unless an explicit early stop condition applies;
- [ ] two materially different query formulations were used;
- [ ] official/first-party and domain-appropriate alternative source classes were attempted;
- [ ] another available provider or browser channel was tried after a channel failure;
- [ ] authentication boundaries use `login_required` with an exact user action;
- [ ] `attempt_log`, query time, validity scope, and exhaustion reason are recorded;
- [ ] the stopping condition is explicit and the related decision remains provisional when necessary.
