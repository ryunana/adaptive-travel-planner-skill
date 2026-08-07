# Capability Matrix

Load this reference only when detecting, explaining, configuring, or choosing data adapters. Detection must distinguish availability, authentication, and a verified query; installed code alone is not a working capability.

## Adapter Boundaries

| Adapter | Useful capabilities | Forecast horizon | Authentication prerequisite | Quota and access boundary |
|---|---|---|---|---|
| Web search | Discover official pages, warnings, schedules, policies, and recent supporting evidence | Depends on the discovered source; search itself provides no forecast | Usually none; some results lead to gated pages | Result coverage and freshness vary; no guaranteed inventory access |
| Host-provided Chinese web search, for example Doubao Search Custom | Discover mainland China official notices, domestic transport changes, prices, policies, and recent Chinese supporting evidence | Depends on the original source; search itself provides no forecast | Separate host-level registration and provider credential; this repository does not install or store it | Quota, pricing, ranking, freshness, and coverage can change; provider authority labels are hints, not proof |
| Interactive browser | Inspect current first-party pages and user-visible inventory; support user-authenticated checks | Depends on the page and source | May require user login, consent, CAPTCHA, or app-only action | Session, anti-automation, and page-access limits apply; never claim access before a successful check |
| Python runtime | Run deterministic local validation, scoring, capability checks, and repository adapters | None by itself | Local executable only | No external data or provider entitlement by itself |
| Repository AMap Web Service adapter | Official geocoding, driving routes, distance, duration, toll reference, and city-level baseline weather | Short-horizon baseline only; it does not extend the 8-14 day decision horizon | AMap developer verification where required plus an authorized Web Service key | Endpoint availability, key type, numeric quotas, rate behavior, and terms must be reverified against current official documentation during implementation |
| Current map UI without API | Geography, route plausibility, and current user-visible map information | Only what the current UI explicitly exposes | Sometimes none; richer functions may require a session | UI access is not an API contract and must not be treated as stable automation |
| 12306 page/app | Exact-date rail service and inventory | Not applicable | Current inventory may require an authenticated user session or app confirmation | No brittle scraping; use `login_required` when the authenticated check cannot be performed |
| Airline or aviation-service pages | Exact-date flights and current operational information | Not applicable | Varies by carrier or service | Availability and fares are date- and market-specific |
| Domestic booking platforms | Auxiliary rail/flight evidence and current hotel marketplace inventory | Any weather display remains auxiliary unless sourced authoritatively | Login may be required for full inventory or prices | Marketplace inventory and prices drift; record market, date, and query time |
| Attraction official channels | Opening, closure, reservation, refund, and ticket rules | Attraction-specific notices, not a general forecast | Official account, mini-program, or login may be required | App-only or login-gated facts remain `login_required` until confirmed |
| Meteorological/government sources | Warnings, observations, forecasts, and seasonal risk evidence | Use only the horizon and granularity the source currently publishes | Usually none; varies by source | City forecasts do not establish scenic-area microclimate; preserve published precision |

## Full and Limited Modes

Full dynamic planning requires at least one successful current query through web search or an interactive browser. Any provider is acceptable if it can return inspectable source URLs; Doubao Search Custom is recommended for mainland China discovery but is not mandatory.

Without a working discovery capability, the Skill remains useful for candidate normalization, preference fit, composite-load analysis, and structural itinerary review. It must treat unsupported weather, opening status, schedules, prices, inventory, and crowd claims as `unknown` or `login_required` and must not describe the output as a fully verified current itinerary.

AMap alone does not satisfy the general web-search requirement because it cannot establish rail inventory, flights, hotel prices, attraction ticket stock, scenic-area microclimate, or current crowd conditions.

These capabilities do not have equal roles. Web search and the interactive browser are the live-discovery foundation; at least one must work for full dynamic planning. AMap is a narrow geography and driving enhancement. Authenticated 12306, hotel, attraction, or booking sessions are conditional verification channels required only when a decision depends on facts hidden behind login.

If one search provider fails, do not collapse the whole host into limited mode while another provider or browser is available. Follow `research-effort-contract.md` for query reformulation, source changes, channel fallback, authentication boundaries, attempt logging, and bounded stopping conditions before a decision-critical fact becomes `unknown`.

## Enhanced AMap Claims

Enhanced AMap mode improves geocoding and driving-route evidence and may provide short-horizon city-level baseline weather. It does not provide rail inventory, flights, hotel prices, attraction ticket stock, scenic-area microclimate, or crowd conditions. It offers no promised weather-coverage gain for the 8-14 day switching window.

Before implementing or revising the adapter, verify official links, endpoint availability, Web Service key requirements, forecast fields and horizon, quotas, rate handling, and terms from the current AMap Open Platform documentation. Put verified numeric values in code tests or implementation documentation with a retrieval date; do not copy remembered values into this matrix.

### Implementation verification (2026-08-07)

The repository adapter was checked against the current official pages before its endpoint contracts were implemented:

- [Geocoding](https://lbs.amap.com/api/webservice/guide/api/georegeo): `GET https://restapi.amap.com/v3/geocode/geo`; `key` and `address` are required, and the key must be a **Web Service API** key.
- [Driving directions](https://lbs.amap.com/api/webservice/guide/api/direction): `GET https://restapi.amap.com/v3/direction/driving`; `key`, `origin`, and `destination` are required.
- [Weather](https://lbs.amap.com/api/webservice/guide/api/weatherinfo): `GET https://restapi.amap.com/v3/weather/weatherInfo`; `city` is an adcode and `extensions=base|all` selects observations or forecast output. The page documents update cadence but does not promise an 8-14 day decision horizon.
- [Create application and key](https://lbs.amap.com/api/webservice/guide/create-project/get-key): the developer creates an application and selects the `Web 服务` platform when adding the key; the setup script cannot create an account or key.
- [Traffic limits](https://lbs.amap.com/api/webservice/guide/tools/flowlevel): the official page sends developers to the current pricing/base-service quota page and the authenticated console's quota-management view for QPS. Therefore this repository does not hard-code a numeric quota.
- [AMap Open Platform service agreement](https://lbs.amap.com/pages/terms/): use is subject to the current platform agreement (the retrieved page showed an update date of 2025-12-03). The adapter does not imply broader rights or capabilities than the official service grants.

The URLs above returned official AMap pages on 2026-08-07. Recheck them before changing provider behavior because endpoint availability, quotas, pricing, and terms can change.

## Capability States

Report each adapter as one of:

- unavailable;
- installed but unconfigured;
- configured but unverified;
- verified working;
- failed, with the exact failed stage.

When an enhanced adapter is unavailable or failed, continue in host search mode if a working web-search or interactive-browser capability remains. Otherwise enter limited mode. Do not lower evidence standards merely because a preferred adapter is absent.
