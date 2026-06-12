import re
import pytest
from osdlc.templates import ALL_TEMPLATES
from osdlc.scaffold import render_template, build_template_vars


class TestTemplateRendering:

    def test_render_simple_substitution(self):
        template = "Hello {name}, version {ver}"
        result = render_template(template, {"name": "World", "ver": "1.0"})
        assert result == "Hello World, version 1.0"

    def test_render_missing_key_unchanged(self):
        template = "Hello {name}, {missing}"
        result = render_template(template, {"name": "World"})
        assert result == "Hello World, {missing}"

    def test_render_empty_vars(self):
        template = "static text"
        result = render_template(template, {})
        assert result == "static text"

    def test_all_templates_have_string_content(self):
        for name, template in ALL_TEMPLATES.items():
            assert isinstance(template, str), f"{name} is not a string"
            assert len(template) > 0, f"{name} is empty"

    def test_all_templates_have_expected_placeholders(self, minimal_config):
        vars_dict = build_template_vars(minimal_config)
        for name, template in ALL_TEMPLATES.items():
            rendered = render_template(template, vars_dict)
            assert isinstance(rendered, str)
            assert len(rendered) > 0

    def test_build_template_vars_contains_all_keys(self, minimal_config):
        vars_dict = build_template_vars(minimal_config)
        expected_keys = [
            "project_name", "default_branch", "version_file",
            "build_cmd", "test_cmd", "lint_cmd",
            "language_description", "env_notes", "architectural_notes",
            "model", "provider_google", "codeql_languages",
            "ecosystem", "language_setup",
            "validate_java", "validate_kotlin", "validate_javascript",
            "validate_typescript", "validate_python", "validate_go",
            "validate_rust", "validate_ruby", "validate_php",
            "validate_xml", "validate_properties",
        ]
        for key in expected_keys:
            assert key in vars_dict, f"Missing key: {key}"

    def test_build_template_vars_python(self, minimal_config):
        vars_dict = build_template_vars(minimal_config)
        assert vars_dict["validate_python"] == "true"
        assert vars_dict["validate_java"] == "false"
        assert vars_dict["ecosystem"] == "pip"
        assert vars_dict["codeql_languages"] == "python"

    def test_build_template_vars_java(self):
        config = {
            "project_name": "java-app",
            "default_branch": "main",
            "version_file": "pom.xml",
            "build_cmd": "mvn compile",
            "test_cmd": "mvn test",
            "lint_cmd": "mvn checkstyle:check",
            "language": "Java",
            "build_system": "Maven",
            "probe": "pom.xml",
            "error_to_issue": False,
            "model": "opencode/deepseek-v4-flash-free",
            "provider_google": "",
            "env_notes": "",
            "architectural_notes": "",
        }
        vars_dict = build_template_vars(config)
        assert vars_dict["validate_java"] == "true"
        assert vars_dict["validate_kotlin"] == "false"
        assert vars_dict["ecosystem"] == "maven"
        assert vars_dict["codeql_languages"] == "java-kotlin"
        assert "setup-java" in vars_dict["language_setup"]

    def test_build_template_vars_go(self):
        config = {
            "project_name": "go-app", "default_branch": "main",
            "version_file": "version.go", "build_cmd": "go build ./...",
            "test_cmd": "go test ./...", "lint_cmd": "go vet ./...",
            "language": "Go", "build_system": "Go modules", "probe": "go.mod",
            "error_to_issue": False, "model": "opencode/deepseek-v4-flash-free",
            "provider_google": "", "env_notes": "", "architectural_notes": "",
        }
        vars_dict = build_template_vars(config)
        assert vars_dict["validate_go"] == "true"
        assert "setup-go" in vars_dict["language_setup"]
        assert vars_dict["ecosystem"] == "go_mod"

    def test_opencode_json_template(self, minimal_config):
        template = ALL_TEMPLATES["opencode.json"]
        vars_dict = build_template_vars(minimal_config)
        rendered = render_template(template, vars_dict)
        assert '"model": "opencode/deepseek-v4-flash-free"' in rendered
        assert '"$schema": "https://opencode.ai/config.json"' in rendered

    def test_agents_md_template(self, minimal_config):
        template = ALL_TEMPLATES["AGENTS.md"]
        vars_dict = build_template_vars(minimal_config)
        rendered = render_template(template, vars_dict)
        assert "test-project" in rendered
        assert "main" in rendered
        assert "Python" in rendered


class TestRequiredPlaceholders:

    PLACEHOLDER_PATTERN = re.compile(r"(?<!\$|\{)\{[a-zA-Z_]\w*\}(?!\})")

    def test_no_unrendered_placeholders_in_full_scaffold(self, minimal_config):
        vars_dict = build_template_vars(minimal_config)
        for name, template in ALL_TEMPLATES.items():
            rendered = render_template(template, vars_dict)
            unrendered = self.PLACEHOLDER_PATTERN.findall(rendered)
            assert not unrendered, f"{name} has unrendered placeholders: {unrendered}"
