import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import release_checks


class ReleaseChecksTests(unittest.TestCase):
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
                    "openai.yaml short_description must match the start of SKILL.md description",
                ],
            )

    def test_required_release_resources_exist_in_repository(self):
        self.assertEqual(release_checks.validate_required_resources(ROOT), [])


if __name__ == "__main__":
    unittest.main()
