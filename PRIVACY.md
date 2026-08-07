# Privacy Guide

Travel planning becomes more useful when it knows real constraints, but the same data can reveal health, relationships, spending, and precise movement. Keep the public method separate from the private profile.

## Keep Local by Default

- completed `references/traveler-profile.md`;
- health exports and fitness history;
- bank, card, wallet, and booking statements;
- order numbers, QR codes, ticket IDs, and hotel room details;
- exact home, work, live hotel, and frequent-location addresses;
- raw navigation history and timestamped routes;
- companion names, contacts, identity documents, and medical details;
- browser sessions, cookies, tokens, API keys, and local tool configuration.

## Share the Minimum Useful Constraint

Prefer:

```text
The traveler has low heat tolerance and needs an indoor fallback.
```

Avoid:

```text
Full health export, medication receipt, hotel room number, and timestamped GPS history.
```

The planner usually needs the boundary, not the raw evidence.

## Before Publishing an Example

Check for:

- usernames and home-directory paths;
- exact travel dates combined with uncommon routes;
- hotel names plus check-in dates;
- transaction amounts and merchant sequences;
- unique combinations of fears, illnesses, and companion details;
- screenshots with status-bar, account, QR, or location metadata;
- repository history containing data that was deleted only in the latest commit.

Use fictional examples rather than lightly edited real itineraries. Changing only names is not sufficient anonymization.

## Repository Protection

This repository ignores `references/traveler-profile.md`, common private directories, exports, screenshots, and environment files. That reduces accidental commits but does not replace review.

Before every public push:

```bash
git status --short
git diff --cached
```

If sensitive data entered Git history, deleting the file in a later commit is not enough. Rewrite the history or create a clean repository before publishing.
