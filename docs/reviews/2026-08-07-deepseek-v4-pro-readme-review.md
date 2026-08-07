# DeepSeek V4 Pro README Content Review

- **Reviewed artifact:** `README.md`
- **Reviewed commit:** `e2ca64d54b2a8678e348b69182d58a6b7a74f4ac`
- **Reviewer:** DeepSeek V4 Pro
- **Review mode:** read-only, full README supplied inline, no repository tools
- **Verdict:** **APPROVE WITH CHANGES**
- **Status:** resolved; accepted findings applied in `fa4bc78cc48ed2780b17a478d97d9a6e78a6996c`

## Executive summary

DeepSeek found no blocking security, privacy, or factual issue. It reported eight Important findings and seven Polish findings. The strongest findings concern capability expectation management, untranslated machine status codes, a real-place example that can be mistaken for current evidence, and prerequisites/attribution around the `npx skills` installer.

Hermes independently checked every finding before adoption. D1, D3, D4, D6, D8, D10, D13, and D15 are accepted; D2 and D7 are accepted only after correcting the reviewer's factual overreach; D5, D9, D11, D12, and D14 are not accepted as stated.

All accepted findings were implemented in `fa4bc78cc48ed2780b17a478d97d9a6e78a6996c`. The rejected findings remain unchanged for the reasons recorded below.

## Independent external fact check

The reviewer made two claims that depend on current external facts. They were checked separately rather than copied into the README:

1. `npm view skills version engines repository --json` returned version `1.5.22`, Node requirement `>=22.20.0`, and repository `vercel-labs/skills`.
2. The current Codex Build Skills page contains `.agents/skills` but does not present `npx skills` or a Node.js prerequisite. Therefore the README must not describe the Vercel Labs installer as a Codex-official CLI.
3. The current AMap terms mention phone numbers, identity verification, ID numbers, and Alipay verification. The retrieved official text did not support the stronger claim that registration categorically requires a *mainland China* phone number.

## Findings

### Important

#### D1 — Standard-output wording can overpromise source coverage

**DeepSeek finding:** The list under “每个核心项目还应包含” can be read as a guarantee that every run will produce hourly weather, internal attraction order, live parking details, and complete door-to-door friction. Neither zero-configuration mode nor AMap mode can guarantee those facts.

**Disposition:** 采纳。

**Recommended change:** Add one sentence before the list stating that the Skill attempts to retrieve these fields, but unavailable or stale fields must remain `unknown`; link to `references/capability-matrix.md`.

#### D2 — The top installer lacks prerequisites and has ambiguous attribution

**DeepSeek finding:** The first-screen `npx skills add` command has no prerequisite note.

**Disposition:** 采纳但调整。

**Independent correction:** Current package metadata confirms Node `>=22.20.0`. However `skills` is the Vercel Labs npm CLI, not a Codex-official CLI, and installing through it does not itself require the Codex CLI to be present.

**Recommended change:** State that this installation path requires Node.js `>=22.20.0`; identify it as the Vercel Labs `skills` installer; separately link the Codex Build Skills documentation for the official `.agents/skills` path and Skill format.

#### D3 — “机动性” is undefined

**DeepSeek finding:** The comparison-table column can mean route flexibility, transportation flexibility, or remaining physical capacity.

**Disposition:** 采纳。

**Recommended change:** Rename it to “切换弹性” or explain that it covers skip/rebook/switch difficulty and nearby alternatives.

#### D4 — Machine-readable status codes lack a Chinese legend

**DeepSeek finding:** `pass`, `fail`, `undecidable`, `pending_gates`, `login_required`, `unknown`, and `verified_working` appear throughout a Chinese README without a central explanation.

**Disposition:** 采纳。

**Recommended change:** Keep the exact codes because they belong to the output contract, but add a short Chinese legend at their first consolidated appearance.

#### D5 — “复合负荷” allegedly appears before it is defined

**DeepSeek finding:** The term was described as unexplained jargon in the first screen and flowchart.

**Disposition:** 不采纳（事实基础不成立）。

**Reason:** The current first screen does not use “复合负荷”. Its first prose occurrence is “计算复合负荷”, immediately followed by a definition covering early starts, walking, climbing, altitude, heat, rain, driving, and recovery. The Mermaid node occurs later. No corrective change is needed.

#### D6 — The English summary interrupts the Chinese first-screen flow

**DeepSeek finding:** The English blockquote sits between the Chinese value explanation and quick start.

**Disposition:** 采纳。

**Recommended change:** Move the English summary directly below the badge, before the Chinese value proposition. Preserve it as a compact bilingual positioning line.

#### D7 — AMap setup needs a clearer optional-registration warning

**DeepSeek finding:** AMap may require phone and real-name verification, which can block some users.

**Disposition:** 采纳但调整。

**Independent correction:** Official material supports phone and identity-verification requirements but did not establish a categorical “mainland China phone number required” rule.

**Recommended change:** State that AMap mode is optional and can be skipped; warn that registration may require phone binding and real-name verification. Do not claim a mainland-phone restriction without a current official source.

#### D8 — The destination comparison table can be mistaken for current evidence

**DeepSeek finding:** Real destinations, exact minimum-day numbers, and phrases such as “天气已核验” look like current verified facts even though the table is only an example.

**Disposition:** 采纳，且优先级高。

**Recommended change:** Add an explicit label: “以下为虚构的输出结构示例，不代表这些目的地的当前天气、交通或最少可行天数。” Prefer neutral placeholders or mark all dynamic values as illustrative/unknown.

### Polish

#### D9 — Add a table of contents

**Disposition:** 不采纳。

**Reason:** A long README can benefit from navigation, but a TOC before the value proposition would make the newly simplified first screen heavier. GitHub already exposes heading navigation. Reconsider only if the document grows further.

#### D10 — “30 秒试用” is a fragile time promise

**Disposition:** 采纳。

**Recommended change:** Rename to “快速开始”. The command itself may be quick, but a fresh Node/npm download is environment-dependent.

#### D11 — “五分钟开始使用” is also a fragile promise

**Disposition:** 不采纳原论证；可顺带调整。

**Reason:** The section covers clone, a minimal local profile, and installation; optional AMap setup is outside it. Five minutes is plausible for an equipped developer. Nevertheless “开始使用” is simpler and avoids unnecessary timing claims, so it can be changed during cleanup without treating it as a defect.

#### D12 — Remove or redesign the Mermaid diagram

**Disposition:** 不采纳。

**Reason:** The linear diagram is redundant for careful readers but gives skimming users a compact overview and costs little. A branching state-machine diagram would add technical burden to a user-facing README.

#### D13 — Add troubleshooting guidance

**Disposition:** 采纳。

**Recommended change:** Add a short FAQ covering missing `npx`, Skill not discovered, AMap verification failure, and how to continue in zero-configuration mode. Avoid duplicating full technical diagnostics.

#### D14 — Replace “同好” with “贡献者”

**Disposition:** 不采纳。

**Reason:** “同好” matches the repository's intended peer-traveler voice and was deliberately chosen. It is not a correctness or consistency problem.

#### D15 — Split the long cross-agent compatibility sentence

**Disposition:** 采纳。

**Recommended change:** Break the installation paragraph into one sentence per Agent and one short compatibility note. This will improve scanning without changing meaning.

## Recommended minimal change set

1. Mark the real-place comparison table as entirely fictional and non-current (D8).
2. Add capability/`unknown` qualification before the standard-output field list (D1).
3. Correct installer prerequisites and attribution: Node `>=22.20.0`, Vercel Labs installer, Codex official-path link kept separate (D2).
4. Add the Chinese status-code legend (D4).
5. Move the English summary below the badge (D6).
6. Rename “机动性” to “切换弹性” or define it (D3).
7. Clarify that AMap is optional and may require phone plus identity verification (D7).
8. Rename “30 秒试用” to “快速开始” (D10).
9. Add a compact troubleshooting section (D13).
10. Split the long cross-agent compatibility paragraph (D15).

## Response tracking

| Finding | Severity | Disposition | README change status |
|---|---|---|---|
| D1 | Important | 采纳 | Applied in `fa4bc78` |
| D2 | Important | 采纳但调整 | Applied in `fa4bc78` |
| D3 | Important | 采纳 | Applied in `fa4bc78` |
| D4 | Important | 采纳 | Applied in `fa4bc78` |
| D5 | Important | 不采纳 | Closed; no change |
| D6 | Important | 采纳 | Applied in `fa4bc78` |
| D7 | Important | 采纳但调整 | Applied in `fa4bc78` |
| D8 | Important | 采纳 | Applied in `fa4bc78` |
| D9 | Polish | 不采纳 | Closed; no change |
| D10 | Polish | 采纳 | Applied in `fa4bc78` |
| D11 | Polish | 不采纳原论证；可顺带调整 | Closed; no change |
| D12 | Polish | 不采纳 | Closed; no change |
| D13 | Polish | 采纳 | Applied in `fa4bc78` |
| D14 | Polish | 不采纳 | Closed; no change |
| D15 | Polish | 采纳 | Applied in `fa4bc78` |

## Current release implication

The reviewer found no blocking issue. All accepted Important and Polish findings are now resolved in `fa4bc78`; the README content review is closed. The implementation code was not changed by this review cycle.
