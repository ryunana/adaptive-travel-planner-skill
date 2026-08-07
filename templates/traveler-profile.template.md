# Private Traveler Profile

> Copy this file to `references/traveler-profile.md` and fill only what is useful. Keep the completed file local.
> V2 destination-decision fields are optional. Treat every missing field as `unknown` and ask for it only when it blocks the current decision; existing V1 profiles remain valid.

## Destination Decision Preferences (Optional)

- Preferred candidate granularity: [city / compact region / bounded route / unknown]
- Typical trip-duration range: [optional]
- Minimum meaningful stay rule: [optional]
- Candidate-generation interests or exclusions: [optional]
- Seasonal destination priorities: [optional]
- Hard destination vetoes: [safety, health, accessibility, mandatory booking, etc.]
- Same-day or pre-departure destination-switch tolerance: [optional]
- Acceptable cancellation or switching cost: [optional]
- Destination-potential versus current-trip priority: [optional]
- Preferred evidence-confidence threshold for commitment: [optional]
- AMap setup preference: [offer / zero-configuration / do not ask again / unknown]

## Party and Luggage

- Travelers: [number and relationship only if useful]
- Luggage: [size and count]
- Primary decision maker: [optional]
- Primary driver: [none / one / multiple]

## Schedule

- Natural wake time: [time range]
- Realistic departure time: [time range]
- Early-start tolerance: [conditions and earliest acceptable time]
- Preferred core activities per day: [number]
- Recovery pattern: [what requires a light day]

## Experience Preference

- Strong likes: [natural, cultural, theme park, architecture, food, events, etc.]
- Strong dislikes: [commercial packaging, crowds, photo spots, shopping, etc.]
- What makes an artificial attraction worthwhile: [quality signals]
- Photography preference: [landscape / portrait / neither / both]
- Surprise tolerance: [low / medium / high]

## Physical and Health Boundaries

- Comfortable walking range: [time, steps, or subjective range]
- Stairs and ascent: [boundary]
- Altitude response: [boundary and recovery method]
- Heat, cold, rain, motion, or food response: [boundary]
- Required medication or access needs: [store locally; include only if useful]

## Driving and Transport

- Comfortable daily driving: [hours or conditions]
- Maximum conditional driving: [hours and required recovery]
- Road types to avoid: [unpaved, mountain, night, rain, etc.]
- Preferred intercity modes: [rail / flight / rental / bus]
- Preferred urban modes: [transit / taxi / drive / walk]
- Is vehicle choice part of the experience: [yes/no and why]

## Companion Constraints

- Different wake or energy pattern: [details]
- Food differences: [details]
- Altitude or motion response: [details]
- Fear or accessibility boundaries: [details]
- How to resolve preference conflicts: [rule]

## Accommodation

- Stable quality baseline: [brands or objective facilities]
- Preferred location: [transport hub / attraction gate / city center / quiet area]
- Minimum consecutive nights: [preference]
- When moving hotels is worthwhile: [conditions]
- Refundability preference: [rule]
- Experience-hotel premium rule: [what must justify it]

## Food

- Local specialties: [interest]
- Spice, allergy, and hard exclusions: [details]
- Queue tolerance: [minutes]
- Reservation tolerance: [details]
- Detour tolerance: [conditions]
- Normal and special meal budget: [currency and range]

## Booking and Crowds

- Advance booking tolerance: [days]
- Ticket rush tolerance: [conditions]
- Crowd tolerance: [low / medium / high]
- Willingness to pay for reliable efficiency products: [rule]
- Same-day city-change tolerance: [rule]

## Shopping and Keepsakes

- Standard keepsakes: [items]
- Craft or shopping interest: [details]
- Sales-pressure boundary: [details]

## Calibration Cases

Use both high and low scores. Separate destination potential from actual visit conditions.

| Experience | Actual score | Potential score | Weather/crowd | What worked | What failed |
|---|---:|---:|---|---|---|
| [case 1] | | | | | |
| [case 2] | | | | | |
| [case 3] | | | | | |

## Planning Output Preference

- Number of options: [2-3 recommended]
- Require one clear recommendation: [yes/no]
- Require explicit dedicated/en-route/conditional/defer verdict: [yes/no]
- Required details: [weather, tickets, transport, load, fallback, etc.]
- Preferred answer length: [short / medium / detailed]
