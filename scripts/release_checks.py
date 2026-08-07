#!/usr/bin/env python3
"""Run release-time metadata, resource, link, and privacy checks."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_RESOURCES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/destination-selection.md",
    "references/source-policy-cn.md",
    "references/capability-matrix.md",
    "references/scoring-model.md",
    "references/planning-contract.md",
    "templates/trip-brief.template.md",
    "templates/traveler-profile.template.md",
    "templates/portable-prompt.template.md",
    "scripts/check_capabilities.py",
    "scripts/setup_amap.py",
    "scripts/amap_cli.py",
    "scripts/verify_amap.py",
    "scripts/score_destinations.py",
    "scripts/validate_itinerary.py",
    "docs/specs/2026-08-07-china-destination-selection-v2-design.md",
)

LOCAL_PATH = re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._-]+/|[A-Za-z]:\\+Users\\+[^\s]+", re.IGNORECASE)
KEY_ASSIGNMENT = re.compile(
    r"(?:api[_-]?key|secret|token|password)\s*[\"']?\s*[:=]\s*[\"']([A-Za-z0-9_-]{24,})[\"']",
    re.IGNORECASE,
)
MARKDOWN_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def validate_skill_metadata(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read {path.name}: {exc}"]
    if not text.startswith("---\n"):
        return ["SKILL.md must begin with YAML frontmatter"]
    closing = text.find("\n---\n", 4)
    if closing == -1:
        return ["SKILL.md frontmatter is not closed"]
    frontmatter = text[4:closing]
    body = text[closing + 5 :]
    if not body.strip():
        return ["SKILL.md must have a non-empty body"]

    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip("\"'")

    issues = []
    for field in ("name", "description"):
        if not fields.get(field):
            issues.append(f"SKILL.md frontmatter must define a non-empty {field}")
    if fields.get("name") and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]):
        issues.append("SKILL.md name must use lowercase hyphenated form")
    return issues


def validate_openai_metadata(skill_path: Path, metadata_path: Path) -> list[str]:
    """Ensure Codex discovery metadata remains derived from SKILL.md."""
    try:
        skill_text = skill_path.read_text(encoding="utf-8")
        metadata_text = metadata_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read metadata: {exc}"]

    closing = skill_text.find("\n---\n", 4)
    frontmatter = skill_text[4:closing] if skill_text.startswith("---\n") and closing != -1 else ""
    skill_fields = {}
    for line in frontmatter.splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            skill_fields[key.strip()] = value.strip().strip("\"'")

    openai_fields = {}
    for line in metadata_text.splitlines():
        match = re.match(r"\s+(display_name|short_description):\s*[\"']?(.*?)[\"']?\s*$", line)
        if match:
            openai_fields[match.group(1)] = match.group(2)

    name = skill_fields.get("name", "")
    description = skill_fields.get("description", "")
    expected_display_name = name.replace("-", " ").title()
    expected_short_description = description[:64].rsplit(" ", 1)[0]

    issues = []
    if openai_fields.get("display_name") != expected_display_name:
        issues.append("openai.yaml display_name must match SKILL.md name")
    if openai_fields.get("short_description") != expected_short_description:
        issues.append("openai.yaml short_description must match the start of SKILL.md description")
    return issues


def validate_required_resources(root: Path) -> list[str]:
    return [f"required resource missing: {relative}" for relative in REQUIRED_RESOURCES if not (root / relative).is_file()]


def scan_privacy(root: Path, files: list[Path]) -> list[str]:
    issues = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        relative = path.relative_to(root)
        for line_number, line in enumerate(text.splitlines(), 1):
            if LOCAL_PATH.search(line):
                issues.append(f"{relative}:{line_number}: local user path")
            if KEY_ASSIGNMENT.search(line):
                issues.append(f"{relative}:{line_number}: key-like assigned value")
    return issues


def validate_markdown_links(root: Path, files: list[Path]) -> list[str]:
    issues = []
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for raw_target in MARKDOWN_LINK.findall(line):
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>\"'")
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = unquote(target.split("#", 1)[0])
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    issues.append(f"{path.relative_to(root)}:{line_number}: link escapes repository: {target}")
                    continue
                if not resolved.exists():
                    issues.append(f"{path.relative_to(root)}:{line_number}: broken local link: {target}")
    return issues


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    files = tracked_files(ROOT)
    issues = []
    issues.extend(validate_skill_metadata(ROOT / "SKILL.md"))
    issues.extend(validate_openai_metadata(ROOT / "SKILL.md", ROOT / "agents/openai.yaml"))
    issues.extend(validate_required_resources(ROOT))
    issues.extend(validate_markdown_links(ROOT, files))
    issues.extend(scan_privacy(ROOT, files))
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1
    print(f"release checks passed: metadata, {len(REQUIRED_RESOURCES)} resources, links, privacy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
