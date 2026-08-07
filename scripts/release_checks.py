#!/usr/bin/env python3
"""Run release-time metadata, resource, link, and privacy checks."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

import yaml  # type: ignore[import-untyped]

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
    r"(?:[A-Za-z0-9_-]*api[_-]?key|key|secret|token|password)\s*[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_+/=-]{24,})[\"']?",
    re.IGNORECASE,
)
MARKDOWN_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")
REFERENCE_USAGE = re.compile(r"(?<!!)\[[^]]+\]\[([^]]+)\]")
REFERENCE_DEFINITION = re.compile(r"^\s*\[([^]]+)\]:\s*(\S+)", re.MULTILINE)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)


def _yaml_mapping(text: str, label: str):
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"{label} is invalid YAML") from exc
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a YAML mapping")
    return value


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

    try:
        fields = _yaml_mapping(frontmatter, "SKILL.md frontmatter")
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    issues = []
    for field in ("name", "description"):
        if not isinstance(fields.get(field), str) or not fields[field].strip():
            issues.append(f"SKILL.md frontmatter must define a non-empty {field}")
    if isinstance(fields.get("name"), str) and fields["name"] and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]):
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
    try:
        skill_fields = _yaml_mapping(frontmatter, "SKILL.md frontmatter")
        metadata = _yaml_mapping(metadata_text, "openai.yaml")
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    openai_fields = metadata.get("interface")
    if not isinstance(openai_fields, dict):
        return ["openai.yaml interface must be a YAML mapping"]

    name = skill_fields.get("name", "")
    description = skill_fields.get("description", "")
    if not isinstance(name, str) or not isinstance(description, str):
        return ["SKILL.md name and description must be strings"]
    expected_display_name = name.replace("-", " ").title()
    short_description = openai_fields.get("short_description", "")

    issues = []
    if not isinstance(openai_fields.get("display_name"), str) or openai_fields.get("display_name") != expected_display_name:
        issues.append("openai.yaml display_name must match SKILL.md name")
    if not isinstance(short_description, str) or not short_description.strip():
        issues.append("openai.yaml short_description must be non-empty")
    elif len(short_description) > 64:
        issues.append("openai.yaml short_description must be at most 64 characters")
    if isinstance(short_description, str) and short_description.strip() and description and short_description.split()[0].lower() != description.split()[0].lower():
        issues.append("openai.yaml short_description must be consistent with SKILL.md description")
    return issues


def validate_required_resources(root: Path) -> list[str]:
    return [f"required resource missing: {relative}" for relative in REQUIRED_RESOURCES if not (root / relative).is_file()]


def scan_privacy(root: Path, files: list[Path]) -> list[str]:
    issues = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            issues.append(f"{path.relative_to(root)}: cannot decode tracked file as UTF-8")
            continue
        except OSError:
            issues.append(f"{path.relative_to(root)}: cannot read tracked file")
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
        scan_text = _without_markdown_code(text)
        definitions = {name.casefold(): target for name, target in REFERENCE_DEFINITION.findall(scan_text)}
        for reference in REFERENCE_USAGE.findall(scan_text):
            if reference.casefold() not in definitions:
                issues.append(f"{path.relative_to(root)}: undefined reference link: {reference}")
        targets = [(match.start(), match.group(1)) for match in MARKDOWN_LINK.finditer(scan_text)]
        targets.extend((match.start(), match.group(2)) for match in REFERENCE_DEFINITION.finditer(scan_text))
        for position, raw_target in targets:
            line_number = text.count("\n", 0, position) + 1
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>\"'")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, separator, fragment = target.partition("#")
            decoded_path = unquote(file_part)
            resolved = (path.parent / decoded_path).resolve() if decoded_path else path.resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                issues.append(f"{path.relative_to(root)}:{line_number}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                issues.append(f"{path.relative_to(root)}:{line_number}: broken local link: {decoded_path}")
                continue
            if separator and fragment and resolved.suffix.lower() == ".md":
                try:
                    destination_text = resolved.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    issues.append(f"{path.relative_to(root)}:{line_number}: cannot inspect link fragment: {target}")
                    continue
                headings = {_heading_slug(value) for value in HEADING.findall(destination_text)}
                if unquote(fragment).casefold() not in headings:
                    issues.append(f"{path.relative_to(root)}:{line_number}: broken heading fragment: {fragment}")
    return issues


def _heading_slug(value: str) -> str:
    value = re.sub(r"[^\w\- ]", "", value.casefold(), flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", value).strip("-")


def _without_markdown_code(text: str) -> str:
    output = []
    fenced = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            output.append("\n" if line.endswith("\n") else "")
        elif fenced:
            output.append("\n" if line.endswith("\n") else "")
        else:
            output.append(re.sub(r"`[^`]*`", "", line))
    return "".join(output)


def tracked_files(root: Path) -> tuple[list[Path], list[str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return [], ["cannot enumerate tracked files"]
    files = []
    issues = []
    for item in result.stdout.split(b"\0"):
        if not item:
            continue
        try:
            files.append(root / item.decode("utf-8"))
        except UnicodeDecodeError:
            issues.append("tracked file name is not valid UTF-8")
    return files, issues


def main() -> int:
    files, issues = tracked_files(ROOT)
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
