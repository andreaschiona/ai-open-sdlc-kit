import os
import json
import pytest
from osdlc.version import (
    detect_version_file,
    read_version,
    write_version,
    determine_bump_type,
    bump_version,
)


class TestDetectVersionFile:
    def test_detect_version_txt(self, tmp_path):
        f = tmp_path / "VERSION"
        f.write_text("version=1.2.3")
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "version_txt"

    def test_detect_pyproject_toml(self, tmp_path):
        f = tmp_path / "pyproject.toml"
        f.write_text('[project]\nversion = "1.0.0"')
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "pyproject_toml"

    def test_detect_package_json(self, tmp_path):
        f = tmp_path / "package.json"
        f.write_text('{"version": "2.0.0"}')
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "package_json"

    def test_detect_cargo_toml(self, tmp_path):
        f = tmp_path / "Cargo.toml"
        f.write_text('[package]\nversion = "0.5.0"')
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "cargo_toml"

    def test_detect_gradle_properties(self, tmp_path):
        f = tmp_path / "gradle.properties"
        f.write_text("version=3.1.0")
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "gradle_properties"

    def test_detect_version_py(self, tmp_path):
        f = tmp_path / "version.py"
        f.write_text('__version__ = "4.2.0"')
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "version_py"

    def test_detect_no_file(self, tmp_path):
        path, fmt = detect_version_file(str(tmp_path))
        assert path is None
        assert fmt is None

    def test_detect_precedence(self, tmp_path):
        (tmp_path / "VERSION").write_text("version=1.0.0")
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "2.0.0"')
        path, fmt = detect_version_file(str(tmp_path))
        assert fmt == "pyproject_toml"


class TestReadVersion:
    def test_version_txt(self, tmp_path):
        f = tmp_path / "VERSION"
        f.write_text("version=1.2.3")
        assert read_version(str(f), "version_txt") == "1.2.3"

    def test_version_txt_plain(self, tmp_path):
        f = tmp_path / "VERSION"
        f.write_text("1.2.3")
        assert read_version(str(f), "version_txt") == "1.2.3"

    def test_pyproject_toml(self, tmp_path):
        f = tmp_path / "pyproject.toml"
        f.write_text('[project]\nversion = "1.0.0"')
        assert read_version(str(f), "pyproject_toml") == "1.0.0"

    def test_package_json(self, tmp_path):
        f = tmp_path / "package.json"
        f.write_text('{"version": "2.0.0"}')
        assert read_version(str(f), "package_json") == "2.0.0"

    def test_cargo_toml(self, tmp_path):
        f = tmp_path / "Cargo.toml"
        f.write_text('[package]\nversion = "0.5.0"')
        assert read_version(str(f), "cargo_toml") == "0.5.0"

    def test_gradle_properties(self, tmp_path):
        f = tmp_path / "gradle.properties"
        f.write_text("version=3.1.0")
        assert read_version(str(f), "gradle_properties") == "3.1.0"

    def test_version_py(self, tmp_path):
        f = tmp_path / "version.py"
        f.write_text('__version__ = "4.2.0"')
        assert read_version(str(f), "version_py") == "4.2.0"

    def test_composer_json(self, tmp_path):
        f = tmp_path / "composer.json"
        f.write_text('{"version": "5.0.0"}')
        assert read_version(str(f), "composer_json") == "5.0.0"

    def test_cmake(self, tmp_path):
        f = tmp_path / "CMakeLists.txt"
        f.write_text("project(MyLib VERSION 6.1.2)")
        assert read_version(str(f), "cmake") == "6.1.2"

    def test_mix(self, tmp_path):
        f = tmp_path / "mix.exs"
        f.write_text('version: "7.2.1"')
        assert read_version(str(f), "mix") == "7.2.1"


class TestWriteVersion:
    def test_version_txt(self, tmp_path):
        f = tmp_path / "VERSION"
        f.write_text("version=1.0.0")
        write_version(str(f), "version_txt", "2.0.0")
        assert f.read_text() == "version=2.0.0"

    def test_version_txt_plain(self, tmp_path):
        f = tmp_path / "VERSION"
        f.write_text("1.0.0")
        write_version(str(f), "version_txt", "2.0.0")
        assert f.read_text() == "2.0.0"

    def test_pyproject_toml(self, tmp_path):
        f = tmp_path / "pyproject.toml"
        f.write_text('[project]\nversion = "1.0.0"')
        write_version(str(f), "pyproject_toml", "2.0.0")
        assert f.read_text() == '[project]\nversion = "2.0.0"'

    def test_package_json(self, tmp_path):
        f = tmp_path / "package.json"
        f.write_text('{"version": "1.0.0"}')
        write_version(str(f), "package_json", "3.0.0")
        data = json.loads(f.read_text())
        assert data["version"] == "3.0.0"

    def test_cargo_toml(self, tmp_path):
        f = tmp_path / "Cargo.toml"
        f.write_text('[package]\nversion = "0.5.0"')
        write_version(str(f), "cargo_toml", "0.6.0")
        assert f.read_text() == '[package]\nversion = "0.6.0"'

    def test_gradle_properties(self, tmp_path):
        f = tmp_path / "gradle.properties"
        f.write_text("version=3.1.0")
        write_version(str(f), "gradle_properties", "4.0.0")
        assert f.read_text() == "version=4.0.0"

    def test_version_py(self, tmp_path):
        f = tmp_path / "version.py"
        f.write_text('__version__ = "1.0.0"')
        write_version(str(f), "version_py", "2.0.0")
        assert f.read_text() == '__version__ = "2.0.0"'

    def test_composer_json(self, tmp_path):
        f = tmp_path / "composer.json"
        f.write_text('{"version": "1.0.0"}')
        write_version(str(f), "composer_json", "5.0.0")
        data = json.loads(f.read_text())
        assert data["version"] == "5.0.0"


class TestDetermineBumpType:
    def test_breaking_change_is_major(self):
        commits = ["feat: add new API", "BREAKING CHANGE: restructure module"]
        assert determine_bump_type(commits) == "major"

    def test_feat_is_minor(self):
        commits = ["fix: correct typo", "feat: add new endpoint"]
        assert determine_bump_type(commits) == "minor"

    def test_fix_is_patch(self):
        commits = ["fix: correct null pointer", "chore: update deps"]
        assert determine_bump_type(commits) == "patch"

    def test_chore_is_patch(self):
        commits = ["chore: update dependencies"]
        assert determine_bump_type(commits) == "patch"

    def test_feat_bang_is_major(self):
        commits = ["feat!: redesign API"]
        assert determine_bump_type(commits) == "major"

    def test_empty_commits_is_patch(self):
        assert determine_bump_type([]) == "patch"


class TestBumpVersion:
    def test_major(self):
        assert bump_version("1.2.3", "major") == "2.0.0"

    def test_minor(self):
        assert bump_version("1.2.3", "minor") == "1.3.0"

    def test_patch(self):
        assert bump_version("1.2.3", "patch") == "1.2.4"

    def test_major_from_zero(self):
        assert bump_version("0.0.1", "major") == "1.0.0"

    def test_invalid_version(self):
        with pytest.raises(ValueError):
            bump_version("abc", "patch")
