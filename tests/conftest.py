import os
import sys
import tempfile
import subprocess
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        yield tmp
        os.chdir(cwd)


@pytest.fixture
def git_init(temp_dir):
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=temp_dir, capture_output=True)
    return temp_dir


@pytest.fixture
def minimal_config():
    return {
        "project_name": "test-project",
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
