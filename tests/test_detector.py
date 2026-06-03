import os
import pytest
from osdlc.detector import detect_project_type, suggest_language_by_extension, PROBES, LANGUAGE_EXTENSIONS


class TestDetectProjectType:

    def test_returns_none_for_empty_dir(self, temp_dir):
        assert detect_project_type(temp_dir) is None

    def test_detects_maven_java(self, temp_dir):
        open(os.path.join(temp_dir, "pom.xml"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "Maven"
        assert result["language"] == "Java"

    def test_detects_npm_javascript(self, temp_dir):
        open(os.path.join(temp_dir, "package.json"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "npm"
        assert result["language"] == "JavaScript"

    def test_detects_cargo_rust(self, temp_dir):
        open(os.path.join(temp_dir, "Cargo.toml"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "Cargo"
        assert result["language"] == "Rust"

    def test_detects_pyproject_toml(self, temp_dir):
        open(os.path.join(temp_dir, "pyproject.toml"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "PEP 621"
        assert result["language"] == "Python"

    def test_detects_go_mod(self, temp_dir):
        open(os.path.join(temp_dir, "go.mod"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "Go modules"
        assert result["language"] == "Go"

    def test_detects_gradle(self, temp_dir):
        open(os.path.join(temp_dir, "build.gradle"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "Gradle"

    def test_detects_gradle_kotlin(self, temp_dir):
        open(os.path.join(temp_dir, "build.gradle.kts"), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == "Gradle Kotlin"

    def test_priority_order(self, temp_dir):
        open(os.path.join(temp_dir, "pom.xml"), "w").close()
        open(os.path.join(temp_dir, "package.json"), "w").close()
        result = detect_project_type(temp_dir)
        assert result["build_system"] == "Maven"

    def test_all_probes_have_consistent_structure(self):
        for probe in PROBES:
            assert len(probe) == 7
            assert isinstance(probe[0], str)
            assert isinstance(probe[1], str)
            assert isinstance(probe[2], str)
            assert isinstance(probe[3], str)
            assert isinstance(probe[4], str)
            assert isinstance(probe[5], str)
            assert isinstance(probe[6], str)

    @pytest.mark.parametrize("probe", PROBES)
    def test_detect_each_build_system(self, temp_dir, probe):
        open(os.path.join(temp_dir, probe[0]), "w").close()
        result = detect_project_type(temp_dir)
        assert result is not None
        assert result["build_system"] == probe[1]
        assert result["language"] == probe[2]


class TestSuggestLanguageByExtension:

    def test_returns_none_for_empty_dir(self, temp_dir):
        assert suggest_language_by_extension(temp_dir) is None

    def test_suggests_python(self, temp_dir):
        open(os.path.join(temp_dir, "main.py"), "w").close()
        assert suggest_language_by_extension(temp_dir) == "Python"

    def test_suggests_javascript(self, temp_dir):
        open(os.path.join(temp_dir, "index.js"), "w").close()
        assert suggest_language_by_extension(temp_dir) == "JavaScript"

    def test_suggests_by_majority(self, temp_dir):
        open(os.path.join(temp_dir, "a.py"), "w").close()
        open(os.path.join(temp_dir, "b.py"), "w").close()
        open(os.path.join(temp_dir, "c.py"), "w").close()
        open(os.path.join(temp_dir, "d.js"), "w").close()
        result = suggest_language_by_extension(temp_dir)
        assert result == "Python"

    def test_ignores_unknown_extensions(self, temp_dir):
        open(os.path.join(temp_dir, "readme.md"), "w").close()
        open(os.path.join(temp_dir, "data.txt"), "w").close()
        assert suggest_language_by_extension(temp_dir) is None

    def test_all_known_extensions_mapped(self):
        known = {".py", ".js", ".ts", ".rs", ".go", ".java", ".kt", ".kts",
                 ".rb", ".ex", ".exs", ".php", ".cs", ".swift", ".jsx", ".tsx"}
        assert set(LANGUAGE_EXTENSIONS.keys()) == known
