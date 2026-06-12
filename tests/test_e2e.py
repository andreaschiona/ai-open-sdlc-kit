import os
import sys
import json
import time
import uuid
import subprocess
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSDLC_SCRIPT = os.path.join(PROJECT_ROOT, "run.py")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        "GITHUB_TOKEN" not in os.environ,
        reason="GITHUB_TOKEN not set — cannot create GitHub resources",
    ),
    pytest.mark.skipif(
        subprocess.run(["gh", "--version"], capture_output=True).returncode != 0,
        reason="gh CLI not available",
    ),
]


@pytest.fixture
def gh_test_repo():
    project = os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1] or "osdlc"
    username = os.environ.get("GITHUB_ACTOR", "test-user")
    repo_name = f"e2e-{project}-{uuid.uuid4().hex[:8]}"
    clone_dir = os.path.join(PROJECT_ROOT, f".tmp-e2e-{repo_name}")

    try:
        result = subprocess.run(
            ["gh", "repo", "create", repo_name, "--private", "--clone"],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "GH_DEBUG": ""},
        )
        if result.returncode != 0:
            pytest.skip(f"Cannot create repo: {result.stderr.strip()}")

        assert os.path.isdir(clone_dir), f"Clone dir not found: {clone_dir}"
        subprocess.run(
            ["git", "config", "user.email", "e2e@test.local"],
            cwd=clone_dir, capture_output=True, timeout=10,
        )
        subprocess.run(
            ["git", "config", "user.name", "E2E Test"],
            cwd=clone_dir, capture_output=True, timeout=10,
        )

        yield repo_name, clone_dir
    finally:
        subprocess.run(
            ["gh", "repo", "delete", f"{username}/{repo_name}", "--yes"],
            capture_output=True, timeout=30,
        )
        subprocess.run(["rm", "-rf", clone_dir], capture_output=True, timeout=30)


class TestE2EGitHubCycle:
    """End-to-end test: GitHub repo → kit init → issue → /oc cycle."""

    def test_full_cycle_repo_init_issue(self, gh_test_repo):
        repo_name, clone_dir = gh_test_repo

        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", clone_dir],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, f"init failed: {result.stderr}"
        assert os.path.exists(os.path.join(clone_dir, "opencode.json"))
        assert os.path.exists(os.path.join(clone_dir, "AGENTS.md"))
        assert os.path.exists(os.path.join(clone_dir, ".github", "workflows", "opencode.yml"))

        subprocess.run(["git", "add", "-A"], cwd=clone_dir, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", "chore: bootstrap SDLC kit"],
            cwd=clone_dir, capture_output=True, timeout=10,
        )
        push = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=clone_dir, capture_output=True, text=True, timeout=30,
        )
        assert push.returncode == 0, f"push failed: {push.stderr}"

        issue = subprocess.run(
            ["gh", "issue", "create",
             "--title", "E2E test issue",
             "--body", "Test the full /oc cycle from e2e test",
             "--label", "enhancement"],
            capture_output=True, text=True, timeout=30,
            cwd=clone_dir,
        )
        assert issue.returncode == 0, f"issue create failed: {issue.stderr}"
        issue_url = issue.stdout.strip()
        assert issue_url.startswith("https://")
        issue_number = issue_url.rstrip("/").split("/")[-1]

        comment = subprocess.run(
            ["gh", "issue", "comment", issue_number,
             "--body", "/oc analyze Verify the kit was bootstrapped correctly"],
            capture_output=True, text=True, timeout=30,
            cwd=clone_dir,
        )
        assert comment.returncode == 0, f"comment failed: {comment.stderr}"

        time.sleep(5)

        runs = subprocess.run(
            ["gh", "run", "list", "--repo", f"{username}/{repo_name}",
             "--limit", "5", "--json", "name,status,conclusion"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "GH_REPO": "", "PWD": PROJECT_ROOT},
        )
        assert runs.returncode == 0, f"run list failed: {runs.stderr}"

        with open(os.path.join(clone_dir, "AGENTS.md")) as f:
            agents = f.read()
        assert "E2E test issue" not in agents
        assert "/oc analyze" in agents

    def test_kit_init_on_fresh_github_repo(self, gh_test_repo):
        repo_name, clone_dir = gh_test_repo

        result = subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", clone_dir],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
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
            assert os.path.exists(os.path.join(clone_dir, f)), f"Missing: {f}"

        with open(os.path.join(clone_dir, "opencode.json")) as f:
            config = json.load(f)
        assert config["permission"]["bash"] == "allow"
        assert "opencode/deepseek-v4-flash-free" in json.dumps(config)

        subprocess.run(["git", "add", "-A"], cwd=clone_dir, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", "chore: init kit"],
            cwd=clone_dir, capture_output=True, timeout=10,
        )
        push = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=clone_dir, capture_output=True, text=True, timeout=30,
        )
        assert push.returncode == 0

    def test_workflow_triggers_on_issue_comment(self, gh_test_repo):
        repo_name, clone_dir = gh_test_repo

        subprocess.run(
            [sys.executable, OSDLC_SCRIPT, "init", "--non-interactive", "--target", clone_dir],
            capture_output=True, timeout=15,
        )
        subprocess.run(["git", "add", "-A"], cwd=clone_dir, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", "chore: init kit"],
            cwd=clone_dir, capture_output=True, timeout=10,
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=clone_dir, capture_output=True, timeout=30,
        )

        issue = subprocess.run(
            ["gh", "issue", "create",
             "--title", "Workflow trigger test",
             "--body", "Test that opencode workflow triggers on /oc comment"],
            capture_output=True, text=True, timeout=30,
            cwd=clone_dir,
        )
        assert issue.returncode == 0
        issue_number = issue.stdout.strip().rstrip("/").split("/")[-1]

        with open(os.path.join(clone_dir, ".github", "workflows", "opencode.yml")) as f:
            workflow = f.read()
        assert "issue_comment" in workflow
        assert "/oc" in workflow or "/opencode" in workflow

        comment = subprocess.run(
            ["gh", "issue", "comment", issue_number, "--body", "/oc analyze"],
            capture_output=True, text=True, timeout=30,
            cwd=clone_dir,
        )
        assert comment.returncode == 0

        time.sleep(3)

        comment_check = subprocess.run(
            ["gh", "issue", "view", issue_number, "--json", "comments"],
            capture_output=True, text=True, timeout=30,
            cwd=clone_dir,
        )
        if comment_check.returncode == 0:
            data = json.loads(comment_check.stdout)
            bodies = [c["body"] for c in data.get("comments", [])]
            assert any("/oc analyze" in b for b in bodies), "Comment not found on issue"
