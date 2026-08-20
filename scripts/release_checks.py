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
    "references/research-effort-contract.md",
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
RESEARCH_EFFORT_RESOURCE = "references/research-effort-contract.md"
RESEARCH_CONTRACT_REFERENCES = (
    "SKILL.md",
    "README.md",
    "references/source-policy-cn.md",
    "references/planning-contract.md",
    "references/destination-selection.md",
    "references/capability-matrix.md",
    "templates/portable-prompt.template.md",
    "docs/specs/2026-08-07-china-destination-selection-v2-design.md",
)
RESEARCH_EFFORT_MARKERS = (
    ("at least three substantive attempts", "minimum three substantive attempts"),
    ("two materially different query formulations", "two materially different query formulations"),
    ("official or first-party source", "official or first-party source"),
    ("domain-appropriate alternative source", "domain-appropriate alternative source"),
    ("another available discovery channel", "available discovery channel fallback"),
    ("interactive browser", "interactive browser fallback"),
    ("login_required", "login-required branch"),
    ("attempt_log", "attempt log"),
    ("two consecutive attempts", "bounded stopping conditions"),
    ("six substantive attempts", "bounded stopping conditions"),
    ("new high-value lead", "bounded stopping conditions"),
    ("one blocked path is not an early stop", "single blocked path fallback"),
    ("one final additional path", "one final additional path"),
)
RESEARCH_SUMMARY_CAP_MARKERS = {
    "README.md": "最多再跟进一条最终路径",
    "templates/portable-prompt.template.md": "one final additional path",
}
BLOCKED_PATH_EARLY_STOP = re.compile(
    r"further\s+access\s+would\s+require\s+bypassing\s+(?:a\s+)?captcha",
    re.IGNORECASE,
)
UNBOUNDED_HIGH_VALUE_LEAD = (
    re.compile(
        r"six\s+substantive\s+attempts\s+unless\s+a\s+new\s+high-value\s+lead\s+appears",
        re.IGNORECASE,
    ),
    re.compile(r"六次实质尝试且没有新的高价值线索[^。\n]*即可停止"),
)
ONE_QUERY_UNKNOWN = (
    re.compile(
        r"if\s+(?:a|one)\s+query\s+fails?,\s*label\s+the\s+fact\s+unknown",
        re.IGNORECASE,
    ),
    re.compile(
        r"if\s+a\s+query\s+fails,\s*report\s+`?unknown`?\s+instead\s+of\s+estimating",
        re.IGNORECASE,
    ),
    re.compile(r"label\s+failed\s+checks?\s+unknown", re.IGNORECASE),
    re.compile(r"查询失败(?:时|后)?.{0,24}(?:标为|标记为?)\s*`?unknown`?", re.IGNORECASE),
)

BINARY_ASSET_SIGNATURES = {
    ".gif": (b"GIF87a", b"GIF89a"),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".webp": (b"RIFF",),
}


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


def validate_research_effort_contract(root: Path) -> list[str]:
    """Keep active Agent instructions from collapsing one failed query into unknown."""
    issues = []
    contract_path = root / RESEARCH_EFFORT_RESOURCE
    if not contract_path.is_file():
        return [f"required research effort resource missing: {RESEARCH_EFFORT_RESOURCE}"]
    try:
        contract = contract_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [f"cannot read research effort resource: {RESEARCH_EFFORT_RESOURCE}"]

    folded_contract = contract.casefold()
    seen_labels = set()
    for marker, label in RESEARCH_EFFORT_MARKERS:
        if marker.casefold() not in folded_contract and label not in seen_labels:
            issues.append(f"{RESEARCH_EFFORT_RESOURCE} missing requirement: {label}")
            seen_labels.add(label)
    if BLOCKED_PATH_EARLY_STOP.search(contract):
        issues.append(
            f"{RESEARCH_EFFORT_RESOURCE} permits one blocked path to stop research"
        )

    for relative in RESEARCH_CONTRACT_REFERENCES:
        path = root / relative
        if not path.is_file():
            issues.append(f"research effort contract reference missing: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            issues.append(f"cannot read research effort contract reference: {relative}")
            continue
        if "research-effort-contract.md" not in text:
            issues.append(f"{relative} must reference {RESEARCH_EFFORT_RESOURCE}")
        if any(pattern.search(text) for pattern in ONE_QUERY_UNKNOWN):
            issues.append(f"{relative} permits unknown after one failed query")
        if any(pattern.search(text) for pattern in UNBOUNDED_HIGH_VALUE_LEAD):
            issues.append(f"{relative} has an unbounded high-value-lead exception")
        required_cap = RESEARCH_SUMMARY_CAP_MARKERS.get(relative)
        if required_cap is not None and required_cap not in text:
            issues.append(f"{relative} must retain the one-final-path hard cap")
    return issues


def scan_privacy(root: Path, files: list[Path]) -> list[str]:
    issues = []
    for path in files:
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except UnicodeError:
            signatures = BINARY_ASSET_SIGNATURES.get(path.suffix.lower(), ())
            is_webp = path.suffix.lower() == ".webp" and data[8:12] == b"WEBP"
            if not any(data.startswith(signature) for signature in signatures) or (
                path.suffix.lower() == ".webp" and not is_webp
            ):
                issues.append(f"{path.relative_to(root)}: cannot decode tracked file as UTF-8")
                continue
            # Preserve ASCII privacy canaries in image metadata while allowing
            # standard binary image assets in the repository.
            text = data.decode("latin-1")
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
    issues.extend(validate_research_effort_contract(ROOT))
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
