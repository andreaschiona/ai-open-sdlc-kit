import os
import sys
import json
import subprocess
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSDLC_SCRIPT = os.path.join(PROJECT_ROOT, "osdlc.py")


# ──────────────────────────────────────────────
# SMOKE TESTS — quick sanity that the tool works
# ──────────────────────────────────────────────

class TestSmoke:
    """Quick smoke tests: module imports, CLI runs, basic invariants."""

    def test_module_importable(self):
        import osdlc
        import osdlc.cli
        import osdlc.detector
        import osdlc.scaffold
        import osdlc.templates

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "--help"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "AI Open SDLC Kit" in result.stdout
        assert "--help" in result.stdout

    def test_cli_init_non_interactive_creates_files(self, git_init):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        expected = [
            "opencode.json", "AGENTS.md",
            ".opencode/package.json",
            ".github/workflows/opencode.yml",
            ".github/workflows/pr-check.yml",
            ".github/workflows/release.yml",
            ".github/workflows/codeql.yml",
            ".github/workflows/lint.yml",
            ".github/dependabot.yml",
        ]
        for f in expected:
            assert os.path.exists(os.path.join(git_init, f)), f"Missing: {f}"

    def test_cli_init_twice_skips(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Skipped" in result.stdout

    def test_cli_init_force_overwrites(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--force", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Generated" in result.stdout
        assert "Skipped" not in result.stdout

    def test_cli_init_unknown_command_fails(self, git_init):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "nonsense", "--target", git_init],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode in (1, 2)

    def test_cli_init_nonexistent_target_fails(self):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive",
             "--target", r"C:\nonexistent_xyzzy_path_12345"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 1
        assert "does not exist" in result.stderr or "does not exist" in result.stdout

    def test_generated_opencode_json_valid(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        with open(os.path.join(git_init, "opencode.json")) as f:
            data = json.load(f)
        assert "$schema" in data
        assert "model" in data
        assert "permission" in data
        assert data["permission"]["bash"] == "allow"

    def test_generated_workflows_are_valid_yaml(self, git_init):
        pytest.importorskip("yaml")
        import yaml
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        workflows_dir = os.path.join(git_init, ".github", "workflows")
        for fname in os.listdir(workflows_dir):
            fpath = os.path.join(workflows_dir, fname)
            with open(fpath) as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {fname}: {e}")


# ──────────────────────────────────────────────
# INTEGRATION TESTS — end-to-end scenarios
# ──────────────────────────────────────────────

class TestIntegrationEndToEnd:
    """Full end-to-end integration scenarios."""

    def test_full_init_with_project_detection_python(self, git_init):
        open(os.path.join(git_init, "pyproject.toml"), "w").close()
        open(os.path.join(git_init, "main.py"), "w").close()
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Python" in result.stdout
        assert "PEP 621" in result.stdout
        with open(os.path.join(git_init, "AGENTS.md")) as f:
            content = f.read()
        assert "Python" in content

    def test_full_init_with_project_detection_java(self, git_init):
        open(os.path.join(git_init, "pom.xml"), "w").close()
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Maven" in result.stdout
        assert "Java" in result.stdout

    def test_init_in_non_git_dir_shows_warning(self, temp_dir):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", temp_dir],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Warning" in result.stdout or "Warning" in result.stderr
        assert "Git repository" in result.stdout or "Git repository" in result.stderr

    def test_init_all_templates_render_without_errors(self, git_init):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Errors" not in result.stdout

    def test_init_generates_summary_with_counts(self, git_init):
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, text=True, timeout=15
        )
        assert "Generated" in result.stdout
        assert "Summary" in result.stdout
        assert "Quick Start" in result.stdout

    def test_init_handles_interactive_mode(self, git_init):
        inputs = "\n".join([
            "test-project",
            "main",
            "VERSION",
            "echo build",
            "echo test",
            "echo lint",
            "Python",
            "manual",
            "n",
            "opencode/deepseek-v4-flash-free",
            "",
            "",
        ]) + "\n"
        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--target", git_init],
            input=inputs, capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert os.path.exists(os.path.join(git_init, "opencode.json"))


# ──────────────────────────────────────────────
# PREREQUISITES CHECKS — external dependencies
# ──────────────────────────────────────────────

class TestPrerequisites:
    """Verify that external prerequisites are met or warn if not."""

    def test_python_version(self):
        assert sys.version_info >= (3, 8), "Python 3.8+ required"

    def test_git_available(self):
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
        assert "git version" in result.stdout

    def test_github_actions_workflows_have_valid_references(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        with open(os.path.join(git_init, ".github", "workflows", "opencode.yml")) as f:
            content = f.read()
        assert "actions/checkout@v4" in content
        assert "actions/cache@v4" in content

    def test_github_token_secret_documented(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        with open(os.path.join(git_init, ".github", "workflows", "opencode.yml")) as f:
            content = f.read()
        assert "GITHUB_TOKEN" in content
        assert "secrets.GITHUB_TOKEN" in content

    def test_gemini_api_key_referenced(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        with open(os.path.join(git_init, ".github", "workflows", "opencode.yml")) as f:
            content = f.read()
        assert "GEMINI_API_KEY" in content

    def test_workflow_permissions_are_set(self, git_init):
        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", git_init],
            capture_output=True, timeout=15
        )
        with open(os.path.join(git_init, ".github", "workflows", "opencode.yml")) as f:
            content = f.read()
        assert "issues: write" in content
        assert "contents: write" in content
        assert "pull-requests: write" in content

    def test_prerequisite_report(self):
        """Comprehensive check: report status of all external dependencies."""
        checks = {}

        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        checks["git"] = result.returncode == 0

        checks["python_version"] = sys.version_info >= (3, 8)
        checks["python_executable"] = bool(sys.executable)

        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True, timeout=10
        )
        checks["pip"] = result.returncode == 0

        checks["github_token_set"] = "GITHUB_TOKEN" in os.environ
        checks["gemini_api_key_set"] = "GEMINI_API_KEY" in os.environ

        missing = [k for k, v in checks.items() if not v]
        if missing:
            warnings = {
                "github_token_set": "GITHUB_TOKEN not set - required for workflows",
                "gemini_api_key_set": "GEMINI_API_KEY not set - needed for Gemini model",
            }
            msg = "; ".join(warnings.get(m, f"{m} check failed") for m in missing)
            pytest.skip(f"Missing prerequisites: {msg}")
