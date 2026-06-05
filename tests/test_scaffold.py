import os
import re
import json
import hashlib
import pytest
from osdlc.templates import ALL_TEMPLATES
from osdlc.scaffold import scaffold, build_template_vars, detect_codeql_languages, detect_ecosystem, detect_language_setup_step


class TestScaffold:

    def test_scaffold_creates_files(self, temp_dir, minimal_config):
        generated, skipped, errors = scaffold(minimal_config, root=temp_dir)
        assert len(errors) == 0
        assert len(generated) > 0
        expected_files = [
            "opencode.json", "AGENTS.md",
            ".opencode/package.json", ".opencode/.gitignore",
            ".opencode/skills/version-management/SKILL.md",
            ".github/workflows/opencode.yml",
            ".github/workflows/pr-check.yml",
            ".github/workflows/release.yml",
            ".github/workflows/codeql.yml",
            ".github/workflows/lint.yml",
            ".github/dependabot.yml",
        ]
        for f in expected_files:
            full_path = os.path.join(temp_dir, f)
            assert os.path.exists(full_path), f"Missing: {full_path}"
            assert os.path.getsize(full_path) > 0

    def test_scaffold_skips_existing_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        generated2, skipped2, errors2 = scaffold(minimal_config, root=temp_dir)
        assert len(errors2) == 0
        assert len(generated2) == 0
        assert len(skipped2) > 0

    def test_scaffold_force_overwrites(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        generated2, skipped2, errors2 = scaffold(minimal_config, root=temp_dir, force=True)
        assert len(errors2) == 0
        assert len(generated2) > 0
        assert len(skipped2) == 0

    def test_scaffold_skips_error_skill_when_disabled(self, temp_dir, minimal_config):
        cfg = dict(minimal_config)
        cfg["error_to_issue"] = False
        generated, skipped, errors = scaffold(cfg, root=temp_dir)
        error_skill_path = os.path.join(temp_dir, ".opencode", "skills", "error-handling", "SKILL.md")
        assert not os.path.exists(error_skill_path)

    def test_scaffold_includes_error_skill_when_enabled(self, temp_dir, minimal_config):
        cfg = dict(minimal_config)
        cfg["error_to_issue"] = True
        cfg["provider_google"] = ',\n    "google": {\n      "options": {}\n    }'
        generated, skipped, errors = scaffold(cfg, root=temp_dir)
        error_skill_path = os.path.join(temp_dir, ".opencode", "skills", "error-handling", "SKILL.md")
        assert os.path.exists(error_skill_path)

    def test_generated_opencode_json_is_valid_json(self, temp_dir, minimal_config):
        import json
        scaffold(minimal_config, root=temp_dir)
        with open(os.path.join(temp_dir, "opencode.json")) as f:
            data = json.load(f)
        assert "model" in data
        assert "$schema" in data
        assert "permission" in data

    def test_generated_agents_md_contains_project_name(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        with open(os.path.join(temp_dir, "AGENTS.md")) as f:
            content = f.read()
        assert minimal_config["project_name"] in content
        assert minimal_config["default_branch"] in content


class TestDetectCodeqlLanguages:

    def test_known_languages(self):
        assert detect_codeql_languages("Python") == "python"
        assert detect_codeql_languages("Java") == "java-kotlin"
        assert detect_codeql_languages("JavaScript") == "javascript-typescript"
        assert detect_codeql_languages("Go") == "go"
        assert detect_codeql_languages("Rust") == "rust"

    def test_unknown_falls_back_to_python(self):
        assert detect_codeql_languages("UnknownLang") == "python"


class TestDetectEcosystem:

    def test_known_ecosystems(self):
        assert detect_ecosystem("Maven") == "maven"
        assert detect_ecosystem("npm") == "npm"
        assert detect_ecosystem("Yarn") == "npm"
        assert detect_ecosystem("pnpm") == "npm"
        assert detect_ecosystem("Cargo") == "cargo"
        assert detect_ecosystem("PEP 621") == "pip"
        assert detect_ecosystem("setuptools") == "pip"
        assert detect_ecosystem("pip") == "pip"

    def test_unknown_falls_back_to_pip(self):
        assert detect_ecosystem("Unknown") == "pip"


class TestDetectLanguageSetupStep:

    def test_python_setup(self):
        step = detect_language_setup_step("Python")
        assert "setup-python" in step

    def test_java_setup(self):
        step = detect_language_setup_step("Java")
        assert "setup-java" in step

    def test_unknown_returns_empty(self):
        assert detect_language_setup_step("UnknownLang") == ""


class TestStateFile:

    def test_scaffold_writes_state_file(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        assert os.path.exists(state_path)
        with open(state_path) as f:
            state = json.load(f)
        assert "kit_version" in state
        assert "files" in state
        assert len(state["files"]) > 0

    def test_state_file_checksums_match_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        with open(state_path) as f:
            state = json.load(f)
        for filepath, stored_checksum in state["files"].items():
            full_path = os.path.join(temp_dir, filepath)
            assert os.path.exists(full_path)
            with open(full_path, "rb") as f:
                actual = hashlib.sha256(f.read()).hexdigest()
            assert actual == stored_checksum, f"Mismatch for {filepath}"

    def test_scaffold_force_updates_state(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        with open(state_path) as f:
            first = json.load(f)
        scaffold(minimal_config, root=temp_dir, force=True)
        with open(state_path) as f:
            second = json.load(f)
        assert second["kit_version"] == first["kit_version"]

    def test_calculate_checksum(self):
        from osdlc.scaffold import calculate_checksum
        c1 = calculate_checksum(b"hello")
        c2 = calculate_checksum("hello")
        assert c1 == c2
        assert len(c1) == 64
        assert all(c in "0123456789abcdef" for c in c1)

    def test_read_state_nonexistent(self, temp_dir):
        from osdlc.scaffold import read_state
        assert read_state(temp_dir) is None

    def test_read_state(self, temp_dir, minimal_config):
        from osdlc.scaffold import read_state, write_state, calculate_checksum
        write_state(temp_dir, "1.0.0", {"test.txt": "abc"})
        state = read_state(temp_dir)
        assert state["kit_version"] == "1.0.0"
        assert state["files"]["test.txt"] == "abc"

    def test_state_not_in_templates(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        from osdlc.templates import ALL_TEMPLATES
        assert ".osdlc-state.json" not in ALL_TEMPLATES


class TestUpgradeScaffold:

    def test_upgrade_fails_on_non_scaffolded(self, temp_dir, minimal_config):
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert len(errors) > 0
        assert "not scaffolded" in errors[0][1]

    def test_upgrade_same_version_no_changes(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert len(errors) == 0
        assert len(added) == 0
        assert len(conflicts) == 0
        assert len(removed) == 0

    def test_upgrade_detects_new_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["files"] = {}
        with open(state_path, "w") as f:
            json.dump(state, f)
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert len(errors) == 0

    def test_upgrade_detects_removed_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["files"]["deprecated.txt"] = "oldchecksum"
        with open(state_path, "w") as f:
            json.dump(state, f)
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert "deprecated.txt" in removed
        assert len(errors) == 0

    def test_upgrade_skips_user_modified_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        open(os.path.join(temp_dir, "opencode.json"), "a").write("\n# user comment\n")
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert "opencode.json" in skipped
        assert len(errors) == 0

    def test_upgrade_overwrites_unmodified_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        with open(state_path) as f:
            state = json.load(f)
        original_checksums = dict(state["files"])
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert len(conflicts) == 0
        for fp in original_checksums:
            if fp in ALL_TEMPLATES:
                assert fp in updated or fp in skipped

    def test_upgrade_conflict_detected(self, temp_dir):
        config = {
            "project_name": "old-name",
            "default_branch": "main",
            "version_file": "VERSION",
            "build_cmd": "echo build",
            "test_cmd": "echo test",
            "lint_cmd": "echo lint",
            "language": "Python",
            "build_system": "manual",
            "probe": "manual",
            "error_to_issue": False,
            "model": "opencode/deepseek-v4-flash-free",
            "provider_google": "",
            "env_notes": "No special environment constraints.",
            "architectural_notes": "",
        }
        scaffold(config, root=temp_dir)
        open(os.path.join(temp_dir, "AGENTS.md"), "a").write("\n# user change\n")
        new_config = dict(config)
        new_config["project_name"] = "new-name"
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            new_config, root=temp_dir
        )
        assert "AGENTS.md" in conflicts
        assert len(errors) == 0

    def test_upgrade_dry_run_does_not_modify_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        open(os.path.join(temp_dir, "opencode.json"), "a").write("\n# dry run test\n")
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir, dry_run=True
        )
        conflict_path = os.path.join(temp_dir, "opencode.json.new")
        assert not os.path.exists(conflict_path)
        with open(os.path.join(temp_dir, "opencode.json")) as f:
            content = f.read()
        assert "# dry run test" in content

    def test_upgrade_creates_new_files(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        state_path = os.path.join(temp_dir, ".osdlc-state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["files"].pop("opencode.json", None)
        state["files"].pop("AGENTS.md", None)
        with open(state_path, "w") as f:
            json.dump(state, f)
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert "opencode.json" in added
        assert "AGENTS.md" in added
        assert len(errors) == 0

    def test_upgrade_state_updated_after_run(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        from osdlc.scaffold import upgrade_scaffold, read_state
        upgrade_scaffold(minimal_config, root=temp_dir)
        state = read_state(temp_dir)
        assert state is not None
        assert state["kit_version"] == "0.3.3"

    def test_upgrade_no_state_file_returns_error(self, temp_dir, minimal_config):
        from osdlc.scaffold import upgrade_scaffold
        updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
            minimal_config, root=temp_dir
        )
        assert len(errors) > 0

    def test_upgrade_dry_run_does_not_update_state(self, temp_dir, minimal_config):
        scaffold(minimal_config, root=temp_dir)
        from osdlc.scaffold import upgrade_scaffold, read_state
        state_before = read_state(temp_dir)
        upgrade_scaffold(minimal_config, root=temp_dir, dry_run=True)
        state_after = read_state(temp_dir)
        assert state_after["kit_version"] == state_before["kit_version"]
