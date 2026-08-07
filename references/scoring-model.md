# Destination Scoring Model

Load this reference only after candidate forms are normalized and hard gates are evaluated. Scores support a decision; they never override a failed hard gate or conceal an undecidable one.

## Default Dimensions

Score each eligible normalized candidate from 0 to 5.

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

Weights total 100 and may be adjusted from explicit traveler priorities. Record any adjustment before scoring and apply it consistently to all candidates.

For complete dimension scores, calculate:

```text
suitability_score = sum((dimension_score / 5) * dimension_weight)
```

Do not silently convert missing dimensions to zero. If evidence is insufficient for a decision-critical dimension, mark it unknown, lower confidence, and keep any affected hard gate pending.

## Potential Versus This Trip

Keep these fields separate:

- `destination_potential`: long-term fit with stable traveler preferences, independent of this exact date and route;
- `this_trip_suitability`: exact-date fit of the accepted normalized form;
- `better_window`: a season, duration, booking condition, health state, or other trigger that would improve a deferred candidate.

A famous destination may have high potential and low current suitability. A bounded route may score well for this trip without redefining the potential of the user's larger original region.

## Evidence Confidence

Return `evidence_confidence` separately from suitability. Base it on both:

1. coverage: how many decision-relevant dimensions and hard gates have usable evidence;
2. authority: whether that evidence is `verified`, `auxiliary`, `unknown`, or `login_required` under `source-policy-cn.md`.

The deterministic scorer calculates these fields as follows:

```text
coverage = usable_records / possible_records
authority = average authority of usable records, or 0 when there are none
value = coverage * authority
level = high when value >= 0.8, medium when value >= 0.5, otherwise low
```

Authority weights are 1.0 for `verified`, 0.6 for `auxiliary`, and 0 for `unknown` or `login_required`. Missing records reduce coverage but are not also included as zeroes in the authority average. For example, one verified record out of nine possible records has `coverage=0.111`, `authority=1.0`, and `value=0.111` (low), rather than receiving a second missing-record penalty.

## Hard-Gate Interaction

- `fail`: reject the candidate before ranking by score.
- `pass`: the candidate may be scored.
- `undecidable`: the candidate may receive a provisional score, but must remain provisional and appear in `pending_gates`.

Do not present the highest provisional score as an unconditional winner.

## Anti-False-Precision Rules

- Show dimension scores only where evidence supports the distinction.
- Explain the dimensions that drive the result.
- Do not claim that a poorly evidenced 86 is definitively better than a well-evidenced 82.
- Treat small score gaps as ties when evidence uncertainty can plausibly reverse them.
- Use confidence and pending gates alongside every aggregate score.
- Never fabricate a number to fill an unknown dimension.
- Prefer a range or qualitative comparison when source precision is coarse.

A valid result includes the normalized form, `minimum_viable_days`, hard-gate states, dimension rationale, `suitability_score` or an explicit reason it is unavailable, `evidence_confidence`, destination potential, this-trip suitability, and better window where deferred.
