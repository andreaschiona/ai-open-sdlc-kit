import os
import re
import pytest
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
