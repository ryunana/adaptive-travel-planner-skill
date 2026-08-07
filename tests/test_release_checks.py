import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import release_checks

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

VALID_RESEARCH_CONTRACT = """# Bounded Research Effort Contract

For each decision-critical dynamic fact, do not assign `unknown` after one failed query.
Before `unknown`, make at least three substantive attempts, use two materially different
query formulations, attempt an official or first-party source and a domain-appropriate
alternative source, and try another available discovery channel such as an interactive
browser. Use `login_required` at an authentication boundary. Record every attempt in an
`attempt_log`. Stop after two consecutive attempts produce no new credible lead once the
minimum coverage is complete. One blocked path is not an early stop while another safe
channel remains. After six substantive attempts, a new high-value lead may justify one
final additional path.
"""


def write_research_contract_fixture(root: Path, *, contract: str = VALID_RESEARCH_CONTRACT) -> None:
    for relative in RESEARCH_CONTRACT_REFERENCES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Follow `references/research-effort-contract.md`.\n", encoding="utf-8")
    (root / "README.md").write_text(
        "Follow `references/research-effort-contract.md`; 最多再跟进一条最终路径。\n",
        encoding="utf-8",
    )
    (root / "templates/portable-prompt.template.md").write_text(
        "Follow `references/research-effort-contract.md`; allow one final additional path.\n",
        encoding="utf-8",
    )
    contract_path = root / "references/research-effort-contract.md"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(contract, encoding="utf-8")


class ReleaseChecksTests(unittest.TestCase):
    def test_yaml_metadata_rejects_malformed_and_wrong_shapes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "SKILL.md"
            metadata = root / "openai.yaml"
            skill.write_text("---\nname: example\ndescription: [\n---\n# Example\n", encoding="utf-8")
            metadata.write_text("interface: [\n", encoding="utf-8")
            self.assertTrue(release_checks.validate_skill_metadata(skill))
            self.assertTrue(release_checks.validate_openai_metadata(skill, metadata))
            skill.write_text("---\nname: [example]\ndescription: [bad]\n---\n# Example\n", encoding="utf-8")
            metadata.write_text("interface: []\n", encoding="utf-8")
            self.assertTrue(release_checks.validate_skill_metadata(skill))
            self.assertTrue(release_checks.validate_openai_metadata(skill, metadata))
            metadata.write_text('interface:\n  display_name: "Example"\n  short_description: "Bad"\n', encoding="utf-8")
            self.assertTrue(release_checks.validate_openai_metadata(skill, metadata))

    def test_skill_metadata_requires_name_and_description(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "SKILL.md"
            skill.write_text("---\nname: example\n---\n# Example\n", encoding="utf-8")
            self.assertEqual(
                release_checks.validate_skill_metadata(skill),
                ["SKILL.md frontmatter must define a non-empty description"],
            )

    def test_skill_metadata_requires_closed_frontmatter_and_body(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "SKILL.md"
            skill.write_text("---\nname: example\ndescription: Example.\n", encoding="utf-8")
            self.assertEqual(
                release_checks.validate_skill_metadata(skill),
                ["SKILL.md frontmatter is not closed"],
            )
            skill.write_text(
                "---\nname: example\ndescription: Example.\n---\n",
                encoding="utf-8",
            )
            self.assertEqual(
                release_checks.validate_skill_metadata(skill),
                ["SKILL.md must have a non-empty body"],
            )

    def test_privacy_scan_finds_local_user_paths_and_key_like_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.md"
            unsafe.write_text(
                "local: /Users/" + "alice/project\n"
                + "api_key: '" + ("a" * 26) + "123456'\n",
                encoding="utf-8",
            )
            issues = release_checks.scan_privacy(root, [unsafe])
            self.assertEqual(len(issues), 2)
            self.assertTrue(all("unsafe.md" in issue for issue in issues))

    def test_privacy_scan_finds_single_backslash_windows_user_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.md"
            unsafe.write_text(
                "local: C:" + "\\Users\\sample-user\\project\n",
                encoding="utf-8",
            )

            self.assertEqual(
                release_checks.scan_privacy(root, [unsafe]),
                ["unsafe.md:1: local user path"],
            )

    def test_privacy_scan_allows_placeholders_and_scan_documentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            safe = root / "safe.md"
            safe.write_text(
                "api_key: stored-locally\npattern: /Users/|/home/|token\n",
                encoding="utf-8",
            )
            self.assertEqual(release_checks.scan_privacy(root, [safe]), [])

    def test_privacy_scan_detects_quoted_and_unquoted_key_assignments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.env"
            unsafe.write_text(
                "AMAP_API_KEY=" + ("a" * 32) + "\n"
                "key: " + ("B" * 24) + "_-+/=\n"
                "token = '" + ("c" * 32) + "'\n",
                encoding="utf-8",
            )
            issues = release_checks.scan_privacy(root, [unsafe])
            self.assertEqual(len(issues), 3)
            self.assertTrue(all("key-like assigned value" in item for item in issues))

    def test_privacy_scan_fails_closed_on_mixed_encoding_key_canary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.bin"
            unsafe.write_bytes(b"\xff\napi_key='" + (b"x" * 32) + b"'\n")
            issues = release_checks.scan_privacy(root, [unsafe])
            self.assertTrue(any("cannot decode" in issue or "key-like assigned value" in issue for issue in issues))

    def test_markdown_reference_links_and_fragments_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.md"
            target.write_text("# Existing Heading\n", encoding="utf-8")
            source = root / "source.md"
            source.write_text(
                "[good][ok]\n[bad][missing]\n[bad heading](target.md#missing-heading)\n\n"
                "`[code][not-a-reference]`\n```text\n[fenced][not-a-reference]\n```\n"
                "[ok]: target.md#existing-heading\n[missing]: absent.md\n",
                encoding="utf-8",
            )
            issues = release_checks.validate_markdown_links(root, [source, target])
            self.assertEqual(len(issues), 2)
            self.assertTrue(any("absent.md" in issue for issue in issues))
            self.assertTrue(any("missing-heading" in issue for issue in issues))

    def test_openai_metadata_matches_skill_frontmatter(self):
        self.assertEqual(
            release_checks.validate_openai_metadata(ROOT / "SKILL.md", ROOT / "agents/openai.yaml"),
            [],
        )

    def test_openai_metadata_rejects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "SKILL.md"
            metadata = root / "openai.yaml"
            skill.write_text(
                "---\nname: sample-skill\ndescription: Compare sample destinations safely.\n---\n# Sample\n",
                encoding="utf-8",
            )
            metadata.write_text(
                'interface:\n  display_name: "Different Name"\n  short_description: "Unrelated summary"\n',
                encoding="utf-8",
            )

            self.assertEqual(
                release_checks.validate_openai_metadata(skill, metadata),
                [
                    "openai.yaml display_name must match SKILL.md name",
                    "openai.yaml short_description must be consistent with SKILL.md description",
                ],
            )

    def test_openai_short_description_must_be_nonempty_and_at_most_64_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "SKILL.md"
            metadata = root / "openai.yaml"
            skill.write_text(
                "---\nname: sample-skill\ndescription: Compare sample destinations safely.\n---\n# Sample\n",
                encoding="utf-8",
            )
            metadata.write_text(
                'interface:\n  display_name: "Sample Skill"\n  short_description: ""\n',
                encoding="utf-8",
            )
            self.assertIn(
                "openai.yaml short_description must be non-empty",
                release_checks.validate_openai_metadata(skill, metadata),
            )
            metadata.write_text(
                'interface:\n  display_name: "Sample Skill"\n  short_description: "' + ("x" * 65) + '"\n',
                encoding="utf-8",
            )
            self.assertIn(
                "openai.yaml short_description must be at most 64 characters",
                release_checks.validate_openai_metadata(skill, metadata),
            )

    def test_readme_install_uses_current_agents_skills_directory(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://developers.openai.com/codex/build-skills", readme)
        self.assertIn("https://skills.sh/b/ryunana/adaptive-travel-planner-skill", readme)
        self.assertIn("npx skills add ryunana/adaptive-travel-planner-skill -g -a codex -y", readme)
        self.assertIn(
            'mkdir -p ~/.agents/skills\nln -s "$(pwd)" ~/.agents/skills/adaptive-travel-planner',
            readme,
        )
        self.assertNotIn("~/.codex/skills", readme)

    def test_required_release_resources_exist_in_repository(self):
        self.assertEqual(release_checks.validate_required_resources(ROOT), [])

    def test_research_effort_contract_requires_canonical_resource(self):
        with tempfile.TemporaryDirectory() as directory:
            issues = release_checks.validate_research_effort_contract(Path(directory))
        self.assertIn(
            "required research effort resource missing: references/research-effort-contract.md",
            issues,
        )

    def test_research_effort_contract_requires_bounded_exhaustion_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(
                root,
                contract="# Research\nTry an official source, then mark the fact unknown.\n",
            )
            issues = release_checks.validate_research_effort_contract(root)
        self.assertTrue(any("minimum three substantive attempts" in issue for issue in issues))
        self.assertTrue(any("two materially different query formulations" in issue for issue in issues))
        self.assertTrue(any("domain-appropriate alternative source" in issue for issue in issues))
        self.assertTrue(any("available discovery channel fallback" in issue for issue in issues))
        self.assertTrue(any("attempt log" in issue for issue in issues))
        self.assertTrue(any("bounded stopping conditions" in issue for issue in issues))
        self.assertTrue(any("single blocked path fallback" in issue for issue in issues))
        self.assertTrue(any("one final additional path" in issue for issue in issues))

    def test_research_effort_contract_rejects_one_query_unknown_shortcut(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(root)
            portable = root / "templates/portable-prompt.template.md"
            portable.write_text(
                "Follow `references/research-effort-contract.md`.\n"
                "If a query fails, label the fact unknown.\n",
                encoding="utf-8",
            )
            issues = release_checks.validate_research_effort_contract(root)
        self.assertIn(
            "templates/portable-prompt.template.md permits unknown after one failed query",
            issues,
        )

    def test_research_effort_contract_rejects_prior_report_unknown_shortcut(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(root)
            target = root / "SKILL.md"
            target.write_text(
                target.read_text()
                + "\nIf a query fails, report unknown instead of estimating.\n",
                encoding="utf-8",
            )
            issues = release_checks.validate_research_effort_contract(root)
        self.assertIn(
            "SKILL.md permits unknown after one failed query",
            issues,
        )

    def test_research_effort_contract_rejects_single_blocked_path_early_stop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(root)
            contract = root / "references/research-effort-contract.md"
            contract.write_text(
                contract.read_text()
                + "\nStop research when further access would require bypassing a CAPTCHA.\n",
                encoding="utf-8",
            )
            issues = release_checks.validate_research_effort_contract(root)
        self.assertIn(
            "references/research-effort-contract.md permits one blocked path to stop research",
            issues,
        )

    def test_research_effort_contract_rejects_unbounded_english_lead_exception(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(root)
            portable = root / "templates/portable-prompt.template.md"
            portable.write_text(
                "Follow `references/research-effort-contract.md`.\n"
                "Stop after six substantive attempts unless a new high-value lead appears.\n",
                encoding="utf-8",
            )
            issues = release_checks.validate_research_effort_contract(root)
        self.assertIn(
            "templates/portable-prompt.template.md has an unbounded high-value-lead exception",
            issues,
        )

    def test_research_effort_contract_rejects_unbounded_chinese_lead_exception(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(root)
            readme = root / "README.md"
            readme.write_text(
                "Follow `references/research-effort-contract.md`.\n"
                "完成六次实质尝试且没有新的高价值线索，即可停止。\n",
                encoding="utf-8",
            )
            issues = release_checks.validate_research_effort_contract(root)
        self.assertIn(
            "README.md has an unbounded high-value-lead exception",
            issues,
        )

    def test_research_effort_contract_requires_active_resource_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_research_contract_fixture(root)
            (root / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
            issues = release_checks.validate_research_effort_contract(root)
        self.assertIn(
            "SKILL.md must reference references/research-effort-contract.md",
            issues,
        )

    def test_current_repository_satisfies_research_effort_contract(self):
        self.assertEqual(release_checks.validate_research_effort_contract(ROOT), [])

    def test_tracked_files_reports_non_utf8_names_without_traceback(self):
        completed = mock.Mock(stdout=b"valid.md\0bad-\xff.md\0")
        with mock.patch("release_checks.subprocess.run", return_value=completed):
            files, issues = release_checks.tracked_files(ROOT)
        self.assertEqual(files, [ROOT / "valid.md"])
        self.assertEqual(issues, ["tracked file name is not valid UTF-8"])


if __name__ == "__main__":
    unittest.main()
