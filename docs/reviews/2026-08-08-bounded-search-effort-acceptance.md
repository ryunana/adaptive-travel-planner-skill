# Bounded Search Effort — Codex Forward Acceptance

Date: 2026-08-08 (+08:00)

## Scope

This acceptance run checks whether the Skill prevents a decision-critical dynamic fact from becoming `unknown` after one failed query, while still allowing bounded early stops for authoritative verification and confirmed authentication walls.

The scenarios are fictional and fixture-controlled. They test Agent behavior and contract activation; they do not claim any real attraction, road, train inventory, schedule, or provider result.

## Exact Input

Codex ran in a read-only isolated Git snapshot copied from the staged PR worktree before this report was added:

- snapshot commit: `e2888646d4f742784bebc798b2593252b57c7187`
- snapshot tree: `c7eba19cdb564deea13a65bae4c345cb23dfd203`
- `SKILL.md` SHA-256: `e183d7972e900744884fa434d944c021769a03bb6018e2be9b26f0b92b60ac14`
- `references/research-effort-contract.md` SHA-256: `e9dc148b66e903c9fc688a784ceba165eda74ed59a5b194ba65ba59730f29b59`
- `templates/portable-prompt.template.md` SHA-256: `ef95b23e6f6b6c521dd2de9e4a37c73d381cf5015b910326aac6ec4f6e439be3`

The source and snapshot copies had identical SHA-256 values for all three files.

## Runner

- model configuration: `gpt-5.6-sol`
- sandbox: read-only
- session mode: ephemeral
- output: one shared strict JSON Schema
- network: prohibited by the scenario prompt; all retrieval outcomes came from fixtures

The first launch used Codex CLI 0.142.5 and produced no model verdict because that version rejected `gpt-5.6-sol` with an explicit upgrade-required error. The CLI was upgraded to the then-current npm release, Codex CLI 0.147.0, and all four unchanged scenarios were rerun. Only the successful 0.147.0 runs count below.

## Results

| Scenario | Expected behavior | Codex result | Attempts | Key evidence | Verdict |
|---|---|---|---:|---|---|
| Official lookup fails, reformulated query succeeds | Do not stop at the first failure; change query/provider; stop early on current authoritative evidence | `verified` | 2 | Two materially different queries; Chinese search timed out; host search found a current government result | PASS |
| Web search fails, browser succeeds | Do not enter limited mode while the browser remains available | `verified` | 2 | `web_search` failure followed by `interactive_browser` verification of the original official page | PASS |
| Exact inventory is behind login | Do not invent inventory or perform pointless retries; use the authentication early stop | `login_required` | 2 | Official lookup plus browser confirmed the login boundary; exact user action supplied | PASS |
| All reasonable paths are exhausted | Allow `unknown` only after source/query/channel coverage and the bounded stop condition | `unknown` | 6 | Official, government, browser, two search providers, and current map covered; final two attempts added no credible lead | PASS |

Every scenario returned `unknown_after_single_failure: false`.

## Independent Assertions

A separate local assertion pass parsed the four JSON outputs and checked:

- scenario status;
- attempt count;
- materially different query coverage;
- provider/browser fallback;
- authentication early stop and exact resolution action;
- no invented inventory value;
- official plus alternative source coverage before `unknown`;
- browser and map-channel coverage in the exhaustion case;
- six-attempt and not-one-failure behavior.

Result: **17/17 assertions passed**.

After the runs, the isolated snapshot had no modified tracked files. The only untracked files were the acceptance schema, four prompts, and four result files created for the simulation.

## Independent Staged-Review Response

The first fail-closed staged review of tree `a8b9b2d321ea77bc69c7305ba18cf85de86b4823` returned **CHANGES REQUIRED** with no Blocking findings, one Important finding, and no Minor findings. A later split content review of tree `a318fc9e89bce10cf88c230a4cd2ad621a87ac36` also returned **CHANGES REQUIRED**, with no Blocking findings, two Important findings, and no Minor findings. Each original verdict remains authoritative for its reviewed tree.

| Finding | Independent reproduction | Remediation | Status |
|---|---|---|---|
| I1: the release gate did not reject the exact prior sentence `If a query fails, report unknown instead of estimating.` | Confirmed in a fresh export: baseline release check exited 0, and a one-line mutation restoring the prior sentence also exited 0 while two canonical-contract references remained | Added a dedicated failing regression test, then added the exact prior semantic pattern without narrowing the existing `a|one query` protection | Independently confirmed fixed on the later tree; carried into the current replacement tree |
| I2: one blocked retrieval path could satisfy the old platform-boundary stop even while safe alternatives remained | Confirmed from the canonical stop list: any listed condition could stop research, while the old CAPTCHA/rate-limit/paywall bullet did not require exhaustion of other providers, source classes, or browser paths | Added RED tests and a canonical invariant that one blocked path is not an early stop; the boundary now applies only when all remaining relevant paths are blocked after safe alternatives were tried or unavailable | Pending fresh-context review of the replacement staged tree |
| I3: the README and portable prompt omitted the canonical one-path cap after a sixth-attempt high-value lead | Confirmed by comparing the standalone summaries with the canonical wording; repeated new leads could extend the portable workflow indefinitely | Added English and Chinese RED canaries, required summary-cap markers, and explicit wording that only one final additional path is allowed | Pending fresh-context review of the replacement staged tree |

No implementation response changes an original review verdict. Final approval requires a new reviewer bound to the replacement tree, followed by exact-commit attestation.

## Simulation Acceptance Decision

**PASS.** In these four forward simulations, the revised Skill caused Codex to continue after the first failed query, change query or channel when useful, distinguish conditional login access from missing evidence, and reserve `unknown` for a recorded bounded-exhaustion outcome.

This simulation verdict is behavioral evidence, not final staged-tree approval and not a guarantee that every model run will comply. The deterministic release check therefore also requires the canonical contract and its references across all active runtime resources, and rejects prior one-query-to-`unknown` shortcuts.
