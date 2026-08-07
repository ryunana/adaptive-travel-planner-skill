# Contributing

Contributions from travelers and agent builders are welcome.

Useful contributions include:

- profile fields for family, senior, accessibility, hiking, cycling, road-trip, or public-transit travel;
- region-specific first-party data sources;
- new weather-attraction classifications;
- better composite-load warnings;
- clearer fallback and cancellation formats;
- fully fictional examples showing different travel styles.

## Contribution Rules

1. Do not submit real health exports, financial statements, booking records, identity data, hotel room details, or precise private tracks.
2. Use fictional or deliberately synthetic examples. Renaming a real traveler is not enough.
3. Do not hard-code a ticket price, schedule, opening status, or weather fact as permanently true.
4. Preserve the distinction between official operational facts and social experience signals.
5. Keep the planner capable of recommending cancellation or deferral.
6. Explain the behavior change and how it was checked in the pull request.

## Local Check

Before submitting:

```bash
git diff --check
rg -n '/Users/|/home/|@|token|cookie|order|booking id|room number' .
```

Review every match rather than assuming a clean command means the content is anonymous.
